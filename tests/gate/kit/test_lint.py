"""The pytest items of tests/gate/kit/lint.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lint import baselines, empty_sets, stale

Case = Callable[..., None]


def test_lint_baselines(case: Case) -> None:
    case(baselines)


def test_lint_stale(case: Case) -> None:
    case(stale)


def test_lint_empty_sets(case: Case) -> None:
    case(empty_sets)
