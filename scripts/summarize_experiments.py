#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def by_task(result: dict) -> dict[str, dict]:
    return {item["task_id"]: item for item in result["items"]}


def attempt_line(item: dict) -> str:
    attempts = item.get("attempt_logs", [])
    parts = []
    for step in attempts:
        ok = "PASS" if step.get("validation_passed") else "FAIL"
        parts.append(
            f"{step.get('level')}:{ok}:{step.get('validation_error_type')}:tokens={step.get('total_tokens')}"
        )
    return " | ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Ada-MSS experiment outputs")
    parser.add_argument("--ada", required=True, help="Ada-MSS JSON output")
    parser.add_argument("--tac", required=True, help="TAC-only JSON output")
    parser.add_argument("--highest", required=True, help="Highest-context JSON output")
    parser.add_argument("--out-dir", required=True, help="Directory for summary artifacts")
    parser.add_argument("--max-case-studies", type=int, default=20)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ada = load(Path(args.ada))
    tac = load(Path(args.tac))
    highest = load(Path(args.highest))

    ada_items = by_task(ada)
    tac_items = by_task(tac)
    highest_items = by_task(highest)

    common_ids = sorted(set(ada_items) & set(tac_items) & set(highest_items))

    escalated_wins = []
    highest_only_wins = []
    tac_only_wins = []
    for task_id in common_ids:
        a = ada_items[task_id]
        t = tac_items[task_id]
        h = highest_items[task_id]
        a_ok = a["status"] == "repair_success"
        t_ok = t["status"] == "repair_success"
        h_ok = h["status"] == "repair_success"
        if a_ok and not t_ok and a.get("final_level") != "TAC":
            escalated_wins.append(task_id)
        if h_ok and not t_ok:
            highest_only_wins.append(task_id)
        if t_ok and not h_ok:
            tac_only_wins.append(task_id)

    case_studies = []
    for task_id in escalated_wins[: args.max_case_studies]:
        case_studies.append(
            {
                "task_id": task_id,
                "why_selected": "TAC-only failed, Ada-MSS succeeded after escalation",
                "ada_mss": {
                    "status": ada_items[task_id]["status"],
                    "final_level": ada_items[task_id]["final_level"],
                    "attempts": ada_items[task_id]["attempts"],
                    "tokens": ada_items[task_id]["total_tokens"],
                    "trace": ada_items[task_id]["trace"],
                    "attempt_summary": attempt_line(ada_items[task_id]),
                    "candidate_patch": ada_items[task_id]["candidate_patch"],
                },
                "tac_only": {
                    "status": tac_items[task_id]["status"],
                    "tokens": tac_items[task_id]["total_tokens"],
                    "attempt_summary": attempt_line(tac_items[task_id]),
                },
                "highest_context": {
                    "status": highest_items[task_id]["status"],
                    "tokens": highest_items[task_id]["total_tokens"],
                    "attempt_summary": attempt_line(highest_items[task_id]),
                },
            }
        )

    (out_dir / "case_studies.json").write_text(
        json.dumps(case_studies, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    rows = [
        ("ada_mss", ada),
        ("tac_only", tac),
        ("highest_context", highest),
    ]
    lines = [
        "# Ada-MSS Experiment Summary",
        "",
        "| method | total | success | success_rate | prompt_tokens | completion_tokens | total_tokens |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, result in rows:
        lines.append(
            f"| {name} | {result['total']} | {result['success']} | {result['success_rate']:.2%} | "
            f"{result.get('prompt_tokens', 0)} | {result.get('completion_tokens', 0)} | {result.get('total_tokens', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Case Study Candidates",
            "",
            f"- TAC-only failed but Ada-MSS succeeded after escalation: {len(escalated_wins)}",
            f"- TAC-only failed but highest-context succeeded: {len(highest_only_wins)}",
            f"- TAC-only succeeded but highest-context failed: {len(tac_only_wins)}",
            "",
            "Selected task ids:",
        ]
    )
    lines.extend([f"- {task_id}" for task_id in escalated_wins[: args.max_case_studies]])
    lines.append("")
    lines.append("Detailed patches are in `case_studies.json`.")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
