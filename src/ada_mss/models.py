from dataclasses import dataclass


@dataclass
class ModelOutput:
    score: float
    decision: str


class BaselineModel:
    """Rule-based baseline; replace with proposal-specific model implementation."""

    def predict(self, text: str) -> ModelOutput:
        score = min(len(text) / 200.0, 1.0)
        decision = "positive" if score >= 0.5 else "negative"
        return ModelOutput(score=score, decision=decision)
