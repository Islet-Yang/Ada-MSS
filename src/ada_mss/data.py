from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
import json
import re


@dataclass
class Document:
    doc_id: str
    text: str
    source: str


@dataclass
class RepairTask:
    task_id: str
    buggy_code: str
    tests: str


class KnowledgeBase:
    def __init__(self, docs: list[Document]) -> None:
        self.docs = docs

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "KnowledgeBase":
        docs: list[Document] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            docs.append(
                Document(
                    doc_id=item["doc_id"],
                    text=item["text"],
                    source=item.get("source", "unknown"),
                )
            )
        return cls(docs)


class TaskDataset:
    """Loader for bug-fix tasks: supports JSONL and Arrow variants."""

    @classmethod
    def from_jsonl(cls, path: str | Path, max_samples: int | None = None) -> list[RepairTask]:
        tasks: list[RepairTask] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            tests = item.get("tests", "")
            if not cls._contains_test_code(tests):
                generated = cls._build_tests_from_debugbench_markdown(
                    tests, item.get("buggy_code", ""), item.get("solution", "")
                )
                if generated:
                    tests = generated
            tasks.append(
                RepairTask(
                    task_id=item["task_id"],
                    buggy_code=item["buggy_code"],
                    tests=tests,
                )
            )
            if max_samples and len(tasks) >= max_samples:
                break
        return tasks

    @classmethod
    def from_arrow(cls, path: str | Path, max_samples: int | None = None, language: str = "python3") -> list[RepairTask]:
        try:
            import pyarrow as pa
        except ImportError as exc:
            raise ImportError(
                "Loading .arrow DebugBench datasets requires pyarrow. Install with: pip install pyarrow"
            ) from exc

        tasks: list[RepairTask] = []
        with Path(path).open("rb") as f:
            reader = pa.ipc.open_stream(f)
            for batch in reader:
                data = batch.to_pydict()
                length = len(next(iter(data.values()))) if data else 0
                for i in range(length):
                    item = {k: data[k][i] for k in data}
                    if language and item.get("language") != language:
                        continue
                    buggy_code = item.get("buggy_code", "")
                    if not buggy_code:
                        continue
                    task_id = item.get("slug") or item.get("task_id") or f"debugbench_{len(tasks)}"
                    tests = cls._build_tests_from_debugbench_item(item)
                    if not tests:
                        continue
                    tasks.append(RepairTask(task_id=task_id, buggy_code=buggy_code, tests=tests))
                    if max_samples and len(tasks) >= max_samples:
                        return tasks
        return tasks

    @classmethod
    def from_path(cls, path: str | Path, max_samples: int | None = None, language: str = "python3") -> list[RepairTask]:
        path_obj = Path(path)
        suffix = path_obj.suffix.lower()
        if suffix == ".arrow":
            return cls.from_arrow(path_obj, max_samples=max_samples, language=language)
        return cls.from_jsonl(path_obj, max_samples=max_samples)

    @classmethod
    def _contains_test_code(cls, tests: str) -> bool:
        if not isinstance(tests, str):
            return False
        lowered = tests.lower()
        if "def test_" in lowered or "assert " in tests:
            return True
        return False

    @classmethod
    def _build_tests_from_debugbench_item(cls, item: dict) -> str:
        tests = item.get("tests")
        if isinstance(tests, str):
            generated = cls._build_tests_from_debugbench_markdown(
                tests, item.get("buggy_code", ""), item.get("solution", "")
            )
            if generated:
                return generated

        examples = item.get("examples") or []
        if not isinstance(examples, list):
            return ""
        return cls._build_tests_from_examples(examples, item.get("buggy_code", ""), item.get("solution", ""))

    @classmethod
    def _build_tests_from_debugbench_markdown(cls, text: str, buggy_code: str, solution: str) -> str:
        examples = []
        current: list[str] = []
        for line in text.splitlines():
            if "Example" in line and "Input:" in line:
                if current:
                    examples.append("\n".join(current))
                current = [line]
            elif current:
                current.append(line)
        if current:
            examples.append("\n".join(current))
        return cls._build_tests_from_examples(examples, buggy_code, solution)

    @classmethod
    def _build_tests_from_examples(cls, examples: list, buggy_code: str, solution: str) -> str:
        func_name = cls._extract_function_name(buggy_code) or cls._extract_function_name(solution) or "solution"
        class_name = cls._extract_class_name(buggy_code) or cls._extract_class_name(solution)
        call_prefix = f"{class_name}()." if class_name else ""
        test_code_lines = ["import pytest", ""]
        valid_examples = 0
        for idx, ex in enumerate(examples[:3]):
            parsed = cls._parse_example(ex)
            if not parsed:
                continue
            args, expected = parsed
            test_code_lines.append(f"def test_example_{idx}():")
            test_code_lines.append(f"    assert {call_prefix}{func_name}({args}) == {expected}")
            test_code_lines.append("")
            valid_examples += 1
        if valid_examples == 0:
            return ""
        return "\n".join(test_code_lines)

    @classmethod
    def _extract_function_name(cls, code: str) -> str:
        match = re.search(r"def\s+(\w+)\s*\(", code)
        if match:
            return match.group(1)
        return ""

    @classmethod
    def _extract_class_name(cls, code: str) -> str:
        match = re.search(r"class\s+(\w+)\s*:", code)
        if match:
            return match.group(1)
        return ""

    @classmethod
    def _parse_example(cls, example: str) -> tuple[str, str] | None:
        if "Input:" not in example or "Output:" not in example:
            return None
        try:
            input_part, output_part = example.split("Output:", 1)
            input_part = input_part.replace("Input:", "").strip()
            output_part = output_part.strip()
            args = []
            for line in input_part.splitlines():
                line = line.strip()
                if not line:
                    continue
                if "=" in line:
                    parts = cls._split_top_level_commas(line)
                    for part in parts:
                        part = part.strip()
                        if not part:
                            continue
                        if "=" in part:
                            name, value = part.split("=", 1)
                            args.append(f"{name.strip()}={cls._normalize_literal(value.strip())}")
                        else:
                            args.append(repr(cls._normalize_literal(part)))
                else:
                    args.append(repr(cls._normalize_literal(line)))
            expected = repr(cls._normalize_literal(output_part))
            return ", ".join(args), expected
        except Exception:
            return None

    @classmethod
    def _split_top_level_commas(cls, text: str) -> list[str]:
        parts: list[str] = []
        depth = 0
        current = []
        for ch in text:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth = max(depth - 1, 0)
            if ch == "," and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(ch)
        if current:
            parts.append("".join(current))
        return parts

    @classmethod
    def _normalize_literal(cls, value: str):
        text = value.strip()
        if not text:
            return text
        text = re.sub(r"\btrue\b", "True", text, flags=re.IGNORECASE)
        text = re.sub(r"\bfalse\b", "False", text, flags=re.IGNORECASE)
        text = re.sub(r"\bnull\b", "None", text, flags=re.IGNORECASE)
        try:
            return ast.literal_eval(text)
        except Exception:
            try:
                return json.loads(text)
            except Exception:
                return text


def tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9_\-]+", text)}
