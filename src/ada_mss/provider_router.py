from __future__ import annotations

import os

from .config import ProviderConfig


class CostAwareProviderRouter:
    """Pick the cheapest enabled provider that has API key configured."""

    def __init__(self, providers: list[ProviderConfig]) -> None:
        self.providers = providers

    def pick(self) -> ProviderConfig:
        candidates = [
            p for p in self.providers if p.enabled and os.getenv(p.api_key_env)
        ]
        if not candidates:
            raise RuntimeError("No available provider. Set at least one API key env var.")

        return min(candidates, key=lambda p: p.input_cost_per_1k + p.output_cost_per_1k)
