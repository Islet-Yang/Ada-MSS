from ada_mss.benchmark import run_benchmark
import argparse

# PYTHONPATH=src python scripts/run_benchmark.py --config configs/default.json --dataset /models/models/islet/data/Rtian___debug_bench/default/0.0.0/f474dcd2ad9276dfb48f96670f830da694870447/debug_bench-test.arrow --test-samples 10


def _preview_patch(text: str, max_lines: int) -> str:
    if max_lines <= 0:
        return text
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"


def _print_line(message: str, file_handle=None) -> None:
    print(message)
    if file_handle is not None:
        file_handle.write(message + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Ada-MSS benchmark")
    parser.add_argument("--config", "-c", default="configs/default.json",
                        help="Path to config file")
    parser.add_argument("--dataset", "-d", default="data/processed/debugbench.jsonl",
                        help="Path to dataset JSONL or Arrow file")
    parser.add_argument("--test-samples", "-n", type=int, default=None,
                        help="Maximum number of samples to evaluate")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print per-task trace and candidate patch preview")
    parser.add_argument("--patch-preview-lines", type=int, default=20,
                        help="Max lines to print for candidate patch preview when verbose is enabled; <=0 means no truncation")
    parser.add_argument("--verbose-log-file", default="",
                        help="Optional file path to write the same benchmark output (useful for detailed diffing)")
    args = parser.parse_args()

    file_handle = open(args.verbose_log_file, "w", encoding="utf-8") if args.verbose_log_file else None

    try:
        summary = run_benchmark(
            config_path=args.config,
            dataset_path=args.dataset,
            max_samples=args.test_samples,
        )
        _print_line(f"Total: {summary.total}", file_handle)
        _print_line(f"Success: {summary.success}", file_handle)
        _print_line(f"Success rate: {summary.success_rate:.2%}", file_handle)
        for item in summary.items:
            _print_line(
                f"- {item.task_id}: {item.status}, attempts={item.attempts}, level={item.final_level}, provider={item.provider}, model={item.model}",
                file_handle,
            )
            if args.verbose:
                _print_line(f"  trace: {' -> '.join(item.trace)}", file_handle)
                for step in item.attempt_logs:
                    status = "PASS" if step.validation_passed else "FAIL"
                    _print_line(
                        f"  [attempt {step.attempt} @ {step.level}] validate={status} error={step.validation_error_type} output={step.validation_output}",
                        file_handle,
                    )
                    _print_line("    candidate_patch:", file_handle)
                    _print_line("    --- BEGIN CANDIDATE PATCH ---", file_handle)
                    _print_line(_preview_patch(step.candidate_patch, max_lines=args.patch_preview_lines), file_handle)
                    _print_line("    --- END CANDIDATE PATCH ---", file_handle)
    finally:
        if file_handle is not None:
            file_handle.close()
