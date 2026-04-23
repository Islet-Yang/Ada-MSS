from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class DataConfig:
    input_path: str = "data/raw"
    cache_path: str = "data/cache"


@dataclass
class ModelConfig:
    encoder_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    hidden_size: int = 384


@dataclass
class TrainConfig:
    batch_size: int = 16
    epochs: int = 5
    learning_rate: float = 1e-4


@dataclass
class AppConfig:
    project_name: str = "Ada-MSS"
    task_name: str = "proposal-aligned baseline"
    data: DataConfig = DataConfig()
    model: ModelConfig = ModelConfig()
    train: TrainConfig = TrainConfig()


def load_config(path: str | Path) -> AppConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return AppConfig(
        project_name=payload.get("project_name", "Ada-MSS"),
        task_name=payload.get("task_name", "proposal-aligned baseline"),
        data=DataConfig(**payload.get("data", {})),
        model=ModelConfig(**payload.get("model", {})),
        train=TrainConfig(**payload.get("train", {})),
    )
