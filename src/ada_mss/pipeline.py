from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .data import RepairTask
from .escalation import EscalationPolicy
from .provider_router import CostAwareProviderRouter
from .pruning import SemanticPruningEngine
from .repair_agent import LLMRepairAgent
from .validator import ValidationSandbox


@dataclass
class PipelineResult:
    status: str
    provider: str
    model: str
    final_level: str
    attempts: int
    trace: list[str]
    candidate_patch: str


class AdaMSSPipeline:
    """Figure-aligned repair loop: prune -> repair -> validate -> escalate."""

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.router = CostAwareProviderRouter(cfg.providers)
        self.pruner = SemanticPruningEngine()
        self.validator = ValidationSandbox()
        self.escalation = EscalationPolicy(max_context_level=cfg.pipeline.max_context_level)

    def run(self, task: RepairTask) -> PipelineResult:
        trace: list[str] = []
        level = self.cfg.pipeline.initial_level
        attempts = 0
        last_patch = ""

        try:
            provider = self.router.pick()
            agent = LLMRepairAgent(provider)
        except Exception:
            if not self.cfg.pipeline.fallback_to_template:
                raise
            return PipelineResult(
                status="repair_fail",
                provider="template_fallback",
                model="none",
                final_level=level,
                attempts=0,
                trace=["provider_unavailable"],
                candidate_patch="",
            )

        while attempts < self.cfg.pipeline.max_repair_attempts:
            attempts += 1
            trace.append(f"semantic_pruning:{level}")
            context = self.pruner.build(task.buggy_code, task.tests, level)

            trace.append("llm_repair_agent")
            try:
                last_patch = agent.propose_patch(context)
            except Exception:
                if self.cfg.pipeline.fallback_to_template:
                    trace.append("llm_unavailable_template_patch")
                    last_patch = "# TODO: generated patch unavailable"
                else:
                    raise

            trace.append("validation_sandbox")
            val = self.validator.run(last_patch, task.tests)

            if val.passed:
                trace.append("repair_success")
                return PipelineResult(
                    status="repair_success",
                    provider=provider.name,
                    model=provider.model,
                    final_level=level,
                    attempts=attempts,
                    trace=trace,
                    candidate_patch=last_patch,
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
                    candidate_patch=last_patch,
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
            candidate_patch=last_patch,
        )
