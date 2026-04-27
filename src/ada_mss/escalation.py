from __future__ import annotations

from .pruning import PRUNING_LEVELS


class EscalationPolicy:
    """Map runtime error categories to next pruning level."""

    def __init__(self, max_context_level: int = 2) -> None:
        self.max_context_level = max_context_level

    def next_level(self, current_level: str, error_type: str) -> str | None:
        idx = PRUNING_LEVELS.index(current_level)
        if idx >= min(self.max_context_level, len(PRUNING_LEVELS) - 1):
            return None

        if error_type in {"AssertionError", "TestFailure", "WrongOutput"}:
            return PRUNING_LEVELS[min(idx + 1, len(PRUNING_LEVELS) - 1)]
        if error_type in {"SyntaxError", "NameError", "TypeError", "RuntimeError"}:
            return PRUNING_LEVELS[min(idx + 1, len(PRUNING_LEVELS) - 1)]
        return PRUNING_LEVELS[min(idx + 1, len(PRUNING_LEVELS) - 1)]
