from .pipeline import AdaMSSPipeline


def train_stub(train_lines: list[str]) -> dict:
    """Training entry scaffold (currently runs baseline inference for sanity check)."""
    pipeline = AdaMSSPipeline()
    outputs = pipeline.run(train_lines)
    return {"num_samples": len(outputs), "status": "scaffold_ready"}
