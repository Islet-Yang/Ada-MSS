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
    """OpenAI-compatible client via stdlib urllib to avoid hard dependency."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        key = os.getenv(self.config.api_key_env)
        if not key:
            raise RuntimeError(f"Missing env var: {self.config.api_key_env}")

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
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        content = body["choices"][0]["message"]["content"]
        return LLMResponse(provider=self.config.name, model=self.config.model, content=content)
