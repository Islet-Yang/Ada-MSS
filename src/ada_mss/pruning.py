from __future__ import annotations

from dataclasses import dataclass


PRUNING_LEVELS = ["TAC", "PSS", "CDS"]


@dataclass
class PrunedContext:
    level: str
    content: str


class SemanticPruningEngine:
    """AST-oriented context shrinking scaffold aligned with proposal figure levels."""

    def build(self, buggy_code: str, tests: str, level: str) -> PrunedContext:
        if level == "TAC":
            content = self._trace_core(buggy_code, tests)
        elif level == "PSS":
            content = self._syntax_skeleton(buggy_code, tests)
        else:
            content = self._dependency_slice(buggy_code, tests)
        return PrunedContext(level=level, content=content)

    def _trace_core(self, buggy_code: str, tests: str) -> str:
        code_lines = buggy_code.splitlines()
        return "\n".join(code_lines[: min(40, len(code_lines))]) + "\n\nTests:\n" + tests

    def _syntax_skeleton(self, buggy_code: str, tests: str) -> str:
        skeleton = []
        for line in buggy_code.splitlines():
            s = line.strip()
            if s.startswith(("def ", "class ", "import ", "from ", "if ", "for ", "while ")):
                skeleton.append(line)
        return "\n".join(skeleton) + "\n\nTests:\n" + tests

    def _dependency_slice(self, buggy_code: str, tests: str) -> str:
        lines = buggy_code.splitlines()
        tail = "\n".join(lines[max(0, len(lines) - 60) :])
        return tail + "\n\nTests:\n" + tests
