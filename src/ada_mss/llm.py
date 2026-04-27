from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib import request

from .config import ProviderConfig


@dataclass
class LLMResponse:
    provider: str
    model: str
    content: str


class OpenAICompatClient:
    """OpenAI-compatible client for both cloud APIs and local servers."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key_env:
            key = os.getenv(self.config.api_key_env)
            if not key:
                raise RuntimeError(f"Missing env var: {self.config.api_key_env}")
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.config.base_url}/chat/completions",
            data=data,
            headers=self._build_headers(),
            method="POST",
        )
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        content = body["choices"][0]["message"]["content"]
        return LLMResponse(provider=self.config.name, model=self.config.model, content=content)
