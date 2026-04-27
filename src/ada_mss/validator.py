from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationResult:
    passed: bool
    error_type: str
    output: str


class ValidationSandbox:
    """Validation scaffold. In production this should apply patch and execute tests in sandbox."""

    def run(self, candidate_patch: str, tests: str) -> ValidationResult:
        # placeholder heuristic for local dry-run in this repo
        if "return" in candidate_patch and "TODO" not in candidate_patch:
            return ValidationResult(passed=True, error_type="", output="simulated pass")
        return ValidationResult(
            passed=False,
            error_type="TestFailure",
            output="simulated failure: patch quality insufficient",
        )
