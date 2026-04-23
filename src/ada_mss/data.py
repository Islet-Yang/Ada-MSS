from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re


@dataclass
class Document:
    doc_id: str
    text: str
    source: str


class KnowledgeBase:
    def __init__(self, docs: list[Document]) -> None:
        self.docs = docs

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "KnowledgeBase":
        docs: list[Document] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            docs.append(
                Document(
                    doc_id=item["doc_id"],
                    text=item["text"],
                    source=item.get("source", "unknown"),
                )
            )
        return cls(docs)


def tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9_\-]+", text)}
