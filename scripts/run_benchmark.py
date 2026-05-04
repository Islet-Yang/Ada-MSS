from ada_mss.benchmark import run_benchmark
import argparse

# PYTHONPATH=src python scripts/run_benchmark.py --config configs/default.json --dataset /models/models/islet/data/Rtian___debug_bench/default/0.0.0/f474dcd2ad9276dfb48f96670f830da694870447/debug_bench-test.arrow --test-samples 10

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Ada-MSS benchmark")
    parser.add_argument("--config", "-c", default="configs/default.json",
                        help="Path to config file")
    parser.add_argument("--dataset", "-d", default="data/processed/debugbench.jsonl",
                        help="Path to dataset JSONL or Arrow file")
    parser.add_argument("--test-samples", "-n", type=int, default=None,
                        help="Maximum number of samples to evaluate")
    args = parser.parse_args()

    summary = run_benchmark(
        config_path=args.config,
        dataset_path=args.dataset,
        max_samples=args.test_samples,
    )
    print(f"Total: {summary.total}")
    print(f"Success: {summary.success}")
    print(f"Success rate: {summary.success_rate:.2%}")
    for item in summary.items:
        print(
            f"- {item.task_id}: {item.status}, attempts={item.attempts}, level={item.final_level}, provider={item.provider}, model={item.model}"
        )
