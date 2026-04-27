from __future__ import annotations

from .config import ProviderConfig
from .llm import OpenAICompatClient
from .pruning import PrunedContext


class LLMRepairAgent:
    def __init__(self, provider: ProviderConfig) -> None:
        self.provider = provider
        self.client = OpenAICompatClient(provider)

    def propose_patch(self, context: PrunedContext) -> str:
        system_prompt = (
            "You are a code repair agent. Return only a compact patch-like suggestion "
            "that can help tests pass."
        )
        user_prompt = (
            f"Pruning level: {context.level}\n"
            "Given buggy code + tests context below, generate candidate fix patch.\n\n"
            f"{context.content}"
        )
        return self.client.generate(user_prompt, system_prompt).content
