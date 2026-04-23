from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    model: str
    api_key_env: str
    input_cost_per_1k: float
    output_cost_per_1k: float
    enabled: bool = True


@dataclass
class RetrievalConfig:
    top_k: int = 4
    min_keyword_overlap: int = 1


@dataclass
class PipelineConfig:
    max_context_chars: int = 6000
    fallback_to_template: bool = True


@dataclass
class AppConfig:
    project_name: str = "Ada-MSS"
    providers: list[ProviderConfig] = field(default_factory=list)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)


def load_config(path: str | Path) -> AppConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    providers = [ProviderConfig(**item) for item in payload.get("providers", [])]
    return AppConfig(
        project_name=payload.get("project_name", "Ada-MSS"),
        providers=providers,
        retrieval=RetrievalConfig(**payload.get("retrieval", {})),
        pipeline=PipelineConfig(**payload.get("pipeline", {})),
    )
