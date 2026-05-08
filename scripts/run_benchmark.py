from ada_mss.benchmark import run_benchmark, write_summary_csv, write_summary_json
from ada_mss.config import load_config
import argparse
import json
from urllib import error, parse, request

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


def _open_direct_for_local(url: str, timeout: float):
    req = request.Request(url=url, method="GET")
    host = parse.urlparse(url).hostname or ""
    if host in {"127.0.0.1", "localhost", "::1"}:
        opener = request.build_opener(request.ProxyHandler({}))
        return opener.open(req, timeout=timeout)
    return request.urlopen(req, timeout=timeout)


def _preflight_provider(
    config_path: str,
    provider_base_url: str | None,
    provider_model: str | None,
) -> None:
    cfg = load_config(config_path)
    provider = next((p for p in cfg.providers if p.enabled), None)
    if provider is None:
        print("Preflight: no enabled provider in config")
        return

    base_url = (provider_base_url or provider.base_url).rstrip("/")
    model = provider_model or provider.model
    api_root = base_url[:-3] if base_url.endswith("/v1") else base_url
    print(f"Preflight: provider={provider.name}, base_url={base_url}, model={model}")

    try:
        with _open_direct_for_local(f"{api_root}/health", timeout=3) as resp:
            print(f"Preflight: /health HTTP {resp.status}")
    except Exception as e:
        print(f"Preflight WARNING: /health failed: {type(e).__name__}: {e}")

    try:
        with _open_direct_for_local(f"{base_url}/models", timeout=3) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        model_ids = [item.get("id", "") for item in body.get("data", [])]
        print(f"Preflight: /v1/models -> {model_ids}")
        if model not in model_ids:
            print(
                "Preflight WARNING: configured model is not in /v1/models; "
                "set configs/default.json model or vLLM --served-model-name to the same value."
            )
    except error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"Preflight WARNING: /v1/models HTTP {e.code}: {err_body[:500]}")
    except Exception as e:
        print(f"Preflight WARNING: /v1/models failed: {type(e).__name__}: {e}")


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
    parser.add_argument("--provider-base-url", default="",
                        help="Override the first enabled provider base URL, e.g. http://127.0.0.1:21220/v1")
    parser.add_argument("--provider-model", default="",
                        help="Override the first enabled provider model, e.g. local_qwen")
    parser.add_argument("--no-progress", action="store_true",
                        help="Disable tqdm progress bar")
    parser.add_argument("--skip-preflight", action="store_true",
                        help="Skip provider /health and /v1/models checks before benchmark")
    parser.add_argument("--experiment-mode", choices=["ada_mss", "tac_only", "highest_context"], default="ada_mss",
                        help="Evaluation strategy: adaptive Ada-MSS, TAC-only baseline, or highest-context baseline")
    parser.add_argument("--output-json", default="",
                        help="Optional path to write machine-readable benchmark results")
    parser.add_argument("--output-csv", default="",
                        help="Optional path to write per-task CSV results")
    args = parser.parse_args()

    file_handle = open(args.verbose_log_file, "w", encoding="utf-8") if args.verbose_log_file else None

    try:
        if not args.skip_preflight:
            _preflight_provider(
                args.config,
                args.provider_base_url or None,
                args.provider_model or None,
            )
        summary = run_benchmark(
            config_path=args.config,
            dataset_path=args.dataset,
            max_samples=args.test_samples,
            show_progress=not args.no_progress,
            provider_base_url=args.provider_base_url or None,
            provider_model=args.provider_model or None,
            experiment_mode=args.experiment_mode,
        )
        _print_line(f"Total: {summary.total}", file_handle)
        _print_line(f"Success: {summary.success}", file_handle)
        _print_line(f"Success rate: {summary.success_rate:.2%}", file_handle)
        _print_line(f"Experiment mode: {summary.experiment_mode}", file_handle)
        _print_line(
            f"Tokens: prompt={summary.prompt_tokens}, completion={summary.completion_tokens}, total={summary.total_tokens}",
            file_handle,
        )
        unavailable_items = [
            item for item in summary.items
            if any(step.startswith("llm_unavailable") for step in item.trace)
        ]
        if unavailable_items:
            first = unavailable_items[0]
            reason = next(step for step in first.trace if step.startswith("llm_unavailable"))
            _print_line(
                f"WARNING: LLM unavailable for {len(unavailable_items)}/{summary.total} tasks; "
                f"first={first.task_id}, provider={first.provider}, reason={reason}",
                file_handle,
            )
        for item in summary.items:
            _print_line(
                f"- {item.task_id}: {item.status}, attempts={item.attempts}, level={item.final_level}, provider={item.provider}, model={item.model}, tokens={item.total_tokens}",
                file_handle,
            )
            if args.verbose:
                _print_line(f"  trace: {' -> '.join(item.trace)}", file_handle)
                for step in item.attempt_logs:
                    status = "PASS" if step.validation_passed else "FAIL"
                    _print_line(
                        f"  [attempt {step.attempt} @ {step.level}] validate={status} error={step.validation_error_type} "
                        f"tokens={step.total_tokens} finish={step.finish_reason} output={step.validation_output}",
                        file_handle,
                    )
                    _print_line("    candidate_patch:", file_handle)
                    _print_line("    --- BEGIN CANDIDATE PATCH ---", file_handle)
                    _print_line(_preview_patch(step.candidate_patch, max_lines=args.patch_preview_lines), file_handle)
                    _print_line("    --- END CANDIDATE PATCH ---", file_handle)
        params = {
            "config": args.config,
            "dataset": args.dataset,
            "test_samples": args.test_samples,
            "provider_base_url": args.provider_base_url,
            "provider_model": args.provider_model,
            "experiment_mode": args.experiment_mode,
        }
        if args.output_json:
            write_summary_json(summary, args.output_json, params=params)
        if args.output_csv:
            write_summary_csv(summary, args.output_csv)
    finally:
        if file_handle is not None:
            file_handle.close()
