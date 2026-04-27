from __future__ import annotations

import os

from .config import ProviderConfig


class CostAwareProviderRouter:
    """Prefer local deployment first, then cheapest remote provider."""

    def __init__(self, providers: list[ProviderConfig]) -> None:
        self.providers = providers

    def _is_available(self, p: ProviderConfig) -> bool:
        if not p.enabled:
            return False
        if not p.api_key_env:
            return True
        return bool(os.getenv(p.api_key_env))

    def pick(self) -> ProviderConfig:
        available = [p for p in self.providers if self._is_available(p)]
        if not available:
            raise RuntimeError("No available provider. Configure local server or API key.")

        locals_first = [p for p in available if p.deployment == "local"]
        if locals_first:
            return locals_first[0]

        return min(available, key=lambda p: p.input_cost_per_1k + p.output_cost_per_1k)
