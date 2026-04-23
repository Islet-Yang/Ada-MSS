from dataclasses import dataclass
from typing import Iterable


@dataclass
class Sample:
    text: str
    label: str | None = None


class DatasetReader:
    """Simple placeholder reader for proposal datasets."""

    def read(self, lines: Iterable[str]) -> list[Sample]:
        return [Sample(text=line.strip()) for line in lines if line.strip()]
