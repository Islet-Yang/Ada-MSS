from __future__ import annotations

from .config import load_config
from .data import KnowledgeBase
from .pipeline import AdaMSSPipeline, PipelineResult


def predict(config_path: str, kb_path: str, query: str) -> PipelineResult:
    cfg = load_config(config_path)
    kb = KnowledgeBase.from_jsonl(kb_path)
    pipeline = AdaMSSPipeline(cfg, kb)
    return pipeline.run(query)
