from __future__ import annotations

from .config import RetrievalConfig
from .data import Document, KnowledgeBase, tokenize


class KeywordRetriever:
    def __init__(self, cfg: RetrievalConfig) -> None:
        self.cfg = cfg

    def search(self, kb: KnowledgeBase, query: str) -> list[Document]:
        q = tokenize(query)
        scored: list[tuple[int, Document]] = []
        for doc in kb.docs:
            overlap = len(q & tokenize(doc.text))
            if overlap >= self.cfg.min_keyword_overlap:
                scored.append((overlap, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[: self.cfg.top_k]]
