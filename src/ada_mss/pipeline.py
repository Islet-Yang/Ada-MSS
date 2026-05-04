from __future__ import annotations

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


class AdaMSSPipeline:
    """Figure-aligned repair loop: prune -> repair -> validate -> escalate."""

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.router = CostAwareProviderRouter(cfg.providers)
        self.pruner = SemanticPruningEngine()
        self.validator = ValidationSandbox()
        self.escalation = EscalationPolicy(max_context_level=cfg.pipeline.max_context_level)

    def _extract_code(self, llm_output: str, fallback: str) -> str:
        code_block = re.search(r"```(?:python)?\n(.*?)```", llm_output, re.S)
        if code_block:
            return code_block.group(1).strip()
        stripped = llm_output.strip()
        return stripped or fallback

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
                llm_output = agent.propose_patch(context)
                candidate_code = self._extract_code(llm_output, task.buggy_code)
            except Exception as e:
                if self.cfg.pipeline.fallback_to_template:
                    trace.append(f"llm_unavailable_template_patch:{type(e).__name__}")
                    candidate_code = self._template_repair(task)
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
        )
