from ada_mss.infer import predict


if __name__ == "__main__":
    result = predict(
        config_path="configs/default.json",
        kb_path="data/sample_kb.jsonl",
        query="How does Ada-MSS control cost while keeping answer quality?",
    )
    print(result)
