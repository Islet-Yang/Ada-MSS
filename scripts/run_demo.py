from ada_mss.infer import predict


if __name__ == "__main__":
    demo = [
        "This is a concise project summary.",
        "This line is intentionally much longer to trigger a different confidence score in the baseline model.",
    ]
    for item in predict(demo):
        print(item)
