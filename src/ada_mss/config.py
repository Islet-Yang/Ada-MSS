from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    model: str
    api_key_env: str = ""
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    enabled: bool = True
    deployment: str = "remote"  # remote | local


@dataclass
class PipelineConfig:
    initial_level: str = "TAC"
    max_context_level: int = 2
    max_repair_attempts: int = 3
    fallback_to_template: bool = True


@dataclass
class AppConfig:
    project_name: str = "Ada-MSS"
    providers: list[ProviderConfig] = field(default_factory=list)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)


def load_config(path: str | Path) -> AppConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    providers = [ProviderConfig(**item) for item in payload.get("providers", [])]
    return AppConfig(
        project_name=payload.get("project_name", "Ada-MSS"),
        providers=providers,
        pipeline=PipelineConfig(**payload.get("pipeline", {})),
    )
