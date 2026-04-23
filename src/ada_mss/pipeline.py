from .data import DatasetReader
from .models import BaselineModel


class AdaMSSPipeline:
    def __init__(self) -> None:
        self.reader = DatasetReader()
        self.model = BaselineModel()

    def run(self, lines: list[str]) -> list[dict]:
        samples = self.reader.read(lines)
        return [
            {"text": sample.text, "result": self.model.predict(sample.text).__dict__}
            for sample in samples
        ]
