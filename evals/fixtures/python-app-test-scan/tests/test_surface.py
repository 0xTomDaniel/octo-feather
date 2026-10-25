"""Every test reaches the app through its CLI, never an internal module (AGENTS.md Rules)."""

import re
from pathlib import Path

TESTS = Path(__file__).parent
INTERNAL = re.compile(r"^\s*(from app\.core\b|import app\.core\b)|\bapp\.cli\._\w", re.MULTILINE)


def test_no_test_imports_app_internals() -> None:
    offenders = [
        path.name
        for path in sorted(TESTS.glob("test_*.py"))
        if path.name != Path(__file__).name and INTERNAL.search(path.read_text())
    ]
    assert offenders == []
