from __future__ import annotations

from .config import load_config
from .data import RepairTask
from .pipeline import AdaMSSPipeline, PipelineResult


def run_repair(config_path: str, task: RepairTask) -> PipelineResult:
    cfg = load_config(config_path)
    pipeline = AdaMSSPipeline(cfg)
    return pipeline.run(task)
