from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .data import KnowledgeBase
from .llm import OpenAICompatClient
from .provider_router import CostAwareProviderRouter
from .retrieval import KeywordRetriever


@dataclass
class PipelineResult:
    answer: str
    provider: str
    model: str
    retrieved_doc_ids: list[str]


class AdaMSSPipeline:
    """
    System-figure aligned flow (implementation scaffold):
    1) Query intake
    2) Retrieval
    3) Context assembly
    4) LLM reasoning + answer generation
    """

    def __init__(self, cfg: AppConfig, kb: KnowledgeBase) -> None:
        self.cfg = cfg
        self.kb = kb
        self.retriever = KeywordRetriever(cfg.retrieval)
        self.router = CostAwareProviderRouter(cfg.providers)

    def run(self, query: str) -> PipelineResult:
        docs = self.retriever.search(self.kb, query)
        context = "\n\n".join([f"[{d.doc_id}] {d.text}" for d in docs])
        context = context[: self.cfg.pipeline.max_context_chars]

        system_prompt = (
            "You are Ada-MSS assistant. Use context when available, "
            "state uncertainty explicitly, and avoid fabricated citations."
        )
        user_prompt = f"Query:\n{query}\n\nContext:\n{context}\n\nAnswer:".strip()

        try:
            provider = self.router.pick()
            client = OpenAICompatClient(provider)
            out = client.generate(user_prompt, system_prompt)
            return PipelineResult(
                answer=out.content,
                provider=out.provider,
                model=out.model,
                retrieved_doc_ids=[d.doc_id for d in docs],
            )
        except Exception:
            if not self.cfg.pipeline.fallback_to_template:
                raise
            fallback = (
                "[Template Fallback] No LLM provider is available now. "
                "Please configure API keys and retry.\n\n"
                f"Top retrieved docs: {[d.doc_id for d in docs]}"
            )
            return PipelineResult(
                answer=fallback,
                provider="template_fallback",
                model="none",
                retrieved_doc_ids=[d.doc_id for d in docs],
            )
