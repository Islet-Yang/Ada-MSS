from __future__ import annotations

import csv
from dataclasses import dataclass
from dataclasses import asdict
import json
from pathlib import Path

from .config import load_config
from .data import TaskDataset
from .pipeline import AdaMSSPipeline, AttemptLog


@dataclass
class EvalItem:
    task_id: str
    status: str
    attempts: int
    final_level: str
    provider: str
    model: str
    trace: list[str]
    candidate_patch: str
    attempt_logs: list[AttemptLog]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class EvalSummary:
    total: int
    success: int
    success_rate: float
    items: list[EvalItem]
    experiment_mode: str = "ada_mss"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def _task_iterator(tasks: list, show_progress: bool):
    if not show_progress:
        return tasks
    try:
        from tqdm.auto import tqdm
    except ImportError:
        return tasks
    return tqdm(tasks, total=len(tasks), desc="Ada-MSS benchmark", unit="task")


def run_benchmark(
    config_path: str,
    dataset_path: str,
    max_samples: int | None = None,
    show_progress: bool = False,
    provider_base_url: str | None = None,
    provider_model: str | None = None,
    experiment_mode: str = "ada_mss",
) -> EvalSummary:
    cfg = load_config(config_path)
    if provider_base_url or provider_model:
        for provider in cfg.providers:
            if provider.enabled:
                if provider_base_url:
                    provider.base_url = provider_base_url.rstrip("/")
                if provider_model:
                    provider.model = provider_model
                break

    if experiment_mode == "tac_only":
        cfg.pipeline.initial_level = "TAC"
        cfg.pipeline.max_context_level = 0
        cfg.pipeline.max_repair_attempts = 1
    elif experiment_mode == "highest_context":
        cfg.pipeline.initial_level = "CDS"
        cfg.pipeline.max_context_level = 2
        cfg.pipeline.max_repair_attempts = 1
    elif experiment_mode != "ada_mss":
        raise ValueError(f"Unknown experiment_mode: {experiment_mode}")

    pipeline = AdaMSSPipeline(cfg)
    tasks = TaskDataset.from_path(dataset_path, max_samples=max_samples)

    items: list[EvalItem] = []
    success = 0

    iterator = _task_iterator(tasks, show_progress)
    for task in iterator:
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
                trace=result.trace,
                candidate_patch=result.candidate_patch,
                attempt_logs=result.attempt_logs,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
            )
        )
        if hasattr(iterator, "set_postfix"):
            rate = success / len(items)
            iterator.set_postfix(
                success=success,
                rate=f"{rate:.1%}",
                last=result.status,
                provider=result.provider,
            )

    total = len(tasks)
    rate = (success / total) if total else 0.0
    return EvalSummary(
        total=total,
        success=success,
        success_rate=rate,
        items=items,
        experiment_mode=experiment_mode,
        prompt_tokens=sum(item.prompt_tokens for item in items),
        completion_tokens=sum(item.completion_tokens for item in items),
        total_tokens=sum(item.total_tokens for item in items),
    )


def write_summary_json(summary: EvalSummary, path: str | Path, params: dict | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(summary)
    payload["params"] = params or {}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_summary_csv(summary: EvalSummary, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "task_id",
                "status",
                "attempts",
                "final_level",
                "provider",
                "model",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "trace",
            ],
        )
        writer.writeheader()
        for item in summary.items:
            writer.writerow(
                {
                    "task_id": item.task_id,
                    "status": item.status,
                    "attempts": item.attempts,
                    "final_level": item.final_level,
                    "provider": item.provider,
                    "model": item.model,
                    "prompt_tokens": item.prompt_tokens,
                    "completion_tokens": item.completion_tokens,
                    "total_tokens": item.total_tokens,
                    "trace": " -> ".join(item.trace),
                }
            )
