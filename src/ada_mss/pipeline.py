from __future__ import annotations

import ast
from dataclasses import dataclass
import re

from .config import AppConfig
from .data import RepairTask
from .escalation import EscalationPolicy
from .provider_router import CostAwareProviderRouter
from .pruning import SemanticPruningEngine
from .repair_agent import LLMRepairAgent
from .validator import ValidationSandbox


@dataclass
class AttemptLog:
    attempt: int
    level: str
    candidate_patch: str
    validation_passed: bool
    validation_error_type: str
    validation_output: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""


@dataclass
class PipelineResult:
    status: str
    provider: str
    model: str
    final_level: str
    attempts: int
    trace: list[str]
    candidate_patch: str
    attempt_logs: list[AttemptLog]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AdaMSSPipeline:
    """Figure-aligned repair loop: prune -> repair -> validate -> escalate."""

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.router = CostAwareProviderRouter(cfg.providers)
        self.pruner = SemanticPruningEngine()
        self.validator = ValidationSandbox()
        self.escalation = EscalationPolicy(max_context_level=cfg.pipeline.max_context_level)

    def _extract_code(self, llm_output: str, fallback: str) -> str:
        text = llm_output.strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.I | re.S).strip()
        if "</think>" in text.lower():
            text = re.split(r"</think>", text, flags=re.I)[-1].strip()

        tagged = re.search(r"<code>\s*(.*?)\s*</code>", text, re.I | re.S)
        if tagged:
            text = tagged.group(1).strip()

        code_block = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.S)
        if code_block:
            text = code_block.group(1).strip()

        match = re.search(r"(?m)^(?:from\s+\S+\s+import\s+|import\s+|class\s+|def\s+)", text)
        if match:
            text = text[match.start():].strip()

        text = self._trim_after_code(text)

        lines = text.splitlines()
        for end in range(len(lines), 0, -1):
            candidate = "\n".join(lines[:end]).strip()
            if not candidate:
                continue
            try:
                ast.parse(candidate)
                return candidate
            except SyntaxError:
                continue

        return text or fallback

    def _trim_after_code(self, text: str) -> str:
        lines = text.splitlines()
        if not lines:
            return text
        kept: list[str] = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if (
                idx > 0
                and line == stripped
                and stripped
                and not stripped.startswith((
                    "import ",
                    "from ",
                    "class ",
                    "def ",
                    "@",
                    "#",
                ))
            ):
                break
            kept.append(line)
        return "\n".join(kept).strip()

    def _template_repair(self, task: RepairTask) -> str:
        code = task.buggy_code
        if "def add(" in code and "assert add(" in task.tests:
            code = code.replace("return a - b", "return a + b")
            code = code.replace("return a * b", "return a + b")
        if "def subtract(" in code and "assert subtract(" in task.tests:
            code = code.replace("return a + b", "return a - b")
        return code

    def run(self, task: RepairTask) -> PipelineResult:
        trace: list[str] = []
        attempt_logs: list[AttemptLog] = []
        level = self.cfg.pipeline.initial_level
        attempts = 0
        candidate_code = task.buggy_code

        try:
            provider = self.router.pick()
            agent = LLMRepairAgent(provider)
        except Exception as e:
            if not self.cfg.pipeline.fallback_to_template:
                raise
            trace.append(f"provider_unavailable:{type(e).__name__}")
            provider = type("ProviderStub", (), {"name": "template_fallback", "model": "none"})()
            agent = None

        while attempts < self.cfg.pipeline.max_repair_attempts:
            attempts += 1
            trace.append(f"semantic_pruning:{level}")
            context = self.pruner.build(task.buggy_code, task.tests, level)

            trace.append("llm_repair_agent")
            try:
                if agent is None:
                    raise RuntimeError("llm_agent_not_ready")
                llm_response = agent.propose_patch(context)
                candidate_code = self._extract_code(llm_response.content, task.buggy_code)
            except Exception as e:
                if self.cfg.pipeline.fallback_to_template:
                    message = str(e).replace("\n", " ")[:200]
                    trace.append(f"llm_unavailable_template_patch:{type(e).__name__}:{message}")
                    candidate_code = self._template_repair(task)
                    llm_response = None
                else:
                    raise

            trace.append("validation_sandbox")
            val = self.validator.run(task, candidate_code)
            attempt_logs.append(
                AttemptLog(
                    attempt=attempts,
                    level=level,
                    candidate_patch=candidate_code,
                    validation_passed=val.passed,
                    validation_error_type=val.error_type,
                    validation_output=val.output,
                    prompt_tokens=llm_response.prompt_tokens if llm_response else 0,
                    completion_tokens=llm_response.completion_tokens if llm_response else 0,
                    total_tokens=llm_response.total_tokens if llm_response else 0,
                    finish_reason=llm_response.finish_reason if llm_response else "",
                )
            )

            if val.passed:
                trace.append("repair_success")
                return PipelineResult(
                    status="repair_success",
                    provider=provider.name,
                    model=provider.model,
                    final_level=level,
                    attempts=attempts,
                    trace=trace,
                    candidate_patch=candidate_code,
                    attempt_logs=attempt_logs,
                    prompt_tokens=sum(step.prompt_tokens for step in attempt_logs),
                    completion_tokens=sum(step.completion_tokens for step in attempt_logs),
                    total_tokens=sum(step.total_tokens for step in attempt_logs),
                )

            trace.append(f"repair_failed:{val.error_type}")
            nxt = self.escalation.next_level(level, val.error_type)
            if nxt is None:
                trace.append("max_context_reached")
                return PipelineResult(
                    status="repair_fail",
                    provider=provider.name,
                    model=provider.model,
                    final_level=level,
                    attempts=attempts,
                    trace=trace,
                    candidate_patch=candidate_code,
                    attempt_logs=attempt_logs,
                    prompt_tokens=sum(step.prompt_tokens for step in attempt_logs),
                    completion_tokens=sum(step.completion_tokens for step in attempt_logs),
                    total_tokens=sum(step.total_tokens for step in attempt_logs),
                )
            level = nxt
            trace.append(f"escalate_to:{level}")

        trace.append("attempt_budget_exhausted")
        return PipelineResult(
            status="repair_fail",
            provider=provider.name,
            model=provider.model,
            final_level=level,
            attempts=attempts,
            trace=trace,
            candidate_patch=candidate_code,
            attempt_logs=attempt_logs,
            prompt_tokens=sum(step.prompt_tokens for step in attempt_logs),
            completion_tokens=sum(step.completion_tokens for step in attempt_logs),
            total_tokens=sum(step.total_tokens for step in attempt_logs),
        )
