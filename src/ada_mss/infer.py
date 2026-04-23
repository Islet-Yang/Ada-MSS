from .pipeline import AdaMSSPipeline


def predict(lines: list[str]) -> list[dict]:
    pipeline = AdaMSSPipeline()
    return pipeline.run(lines)
