from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from urllib import error, request

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

    def _append_debug_log(self, record: dict) -> None:
        log_path = os.getenv("ADA_MSS_LLM_LOG")
        if not log_path:
            return
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 512,
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        }
        data = json.dumps(payload).encode("utf-8")
        url = f"{self.config.base_url}/chat/completions"
        req = request.Request(
            url=url,
            data=data,
            headers=self._build_headers(),
            method="POST",
        )

        started_at = datetime.now(timezone.utc).isoformat()
        try:
            with request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            self._append_debug_log(
                {
                    "time": started_at,
                    "provider": self.config.name,
                    "model": self.config.model,
                    "url": url,
                    "request": payload,
                    "http_status": e.code,
                    "error_response": err_body,
                }
            )
            raise

        content = body["choices"][0]["message"]["content"]
        self._append_debug_log(
            {
                "time": started_at,
                "provider": self.config.name,
                "model": self.config.model,
                "url": url,
                "request": payload,
                "response": body,
            }
        )
        return LLMResponse(provider=self.config.name, model=self.config.model, content=content)
