from __future__ import annotations

from dataclasses import dataclass

from .data import RepairTask
from .sandbox_evaluator import (
    extract_debugbench_test_cases,
    infer_entry_point,
    run_multiple_tests,
)


@dataclass
class ValidationResult:
    passed: bool
    error_type: str
    output: str


class ValidationSandbox:
    """Executes candidate code in a subprocess-backed LeetCode-style sandbox."""

    def run(self, task: RepairTask, candidate_code: str) -> ValidationResult:
        example_cases = extract_debugbench_test_cases(task.tests)
        if example_cases:
            entry_point = infer_entry_point(task.buggy_code)
            patches_and_tests = [
                (candidate_code, inputs, expected)
                for inputs, expected in example_cases
            ]
            results = run_multiple_tests(patches_and_tests, entry_point, timeout=2.0)
            for idx, result in enumerate(results, start=1):
                status = result.get("status", "RuntimeError")
                if status != "Pass":
                    error_type = result.get("error_type") or status
                    return ValidationResult(
                        False,
                        error_type,
                        f"example_{idx}: {result}",
                    )
            return ValidationResult(True, "", f"{len(results)} example tests passed")

        ns: dict = {}
        try:
            exec(candidate_code, ns, ns)
            exec(task.tests, ns, ns)

            test_functions = [v for k, v in ns.items() if k.startswith("test_") and callable(v)]
            if not test_functions:
                return ValidationResult(False, "NoTestsDiscovered", "No test_* function found")

            for fn in test_functions:
                fn()
            return ValidationResult(True, "", "all tests passed")
        except AssertionError as e:
            return ValidationResult(False, "AssertionError", str(e) or "assertion failed")
        except Exception as e:
            return ValidationResult(False, type(e).__name__, str(e))
