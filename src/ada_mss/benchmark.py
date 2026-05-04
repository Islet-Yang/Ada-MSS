from __future__ import annotations

from dataclasses import dataclass

from .config import load_config
from .data import TaskDataset
from .pipeline import AdaMSSPipeline


@dataclass
class EvalItem:
    task_id: str
    status: str
    attempts: int
    final_level: str
    provider: str
    model: str


@dataclass
class EvalSummary:
    total: int
    success: int
    success_rate: float
    items: list[EvalItem]


def run_benchmark(config_path: str, dataset_path: str, max_samples: int | None = None) -> EvalSummary:
    cfg = load_config(config_path)
    pipeline = AdaMSSPipeline(cfg)
    tasks = TaskDataset.from_path(dataset_path, max_samples=max_samples)

    items: list[EvalItem] = []
    success = 0

    for task in tasks:
        result = pipeline.run(task)
        if result.status == "repair_success":
            success += 1
        items.append(
            EvalItem(
                task_id=task.task_id,
                status=result.status,
                attempts=result.attempts,
                final_level=result.final_level,
                provider=result.provider,
                model=result.model,
            )
        )

    total = len(tasks)
    rate = (success / total) if total else 0.0
    return EvalSummary(total=total, success=success, success_rate=rate, items=items)
