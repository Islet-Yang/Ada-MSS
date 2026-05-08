from __future__ import annotations

from .config import ProviderConfig
from .llm import LLMResponse, OpenAICompatClient
from .pruning import PrunedContext


class LLMRepairAgent:
    def __init__(self, provider: ProviderConfig) -> None:
        self.provider = provider
        self.client = OpenAICompatClient(provider)

    def propose_patch(self, context: PrunedContext) -> LLMResponse:
        system_prompt = (
            "You are a Python code patch generator, not a tutor. "
            "Do not reason step by step. Do not output <think> blocks. "
            "Output exactly one repaired Python file and nothing else. "
            "The first non-whitespace token must be import, from, class, or def."
        )
        user_prompt = (
            "/no_think\n"
            f"Pruning level: {context.level}\n"
            "Repair the buggy Python code below so it passes the examples. "
            "Return only executable Python code. No markdown. No explanation.\n\n"
            f"{context.content}"
        )
        return self.client.generate(user_prompt, system_prompt)
