"""The pytest items of tests/gate/kit/check_ts.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_ts import empty_store, findings, other_fs, unused_suppression

Case = Callable[..., None]


def test_empty_store(case: Case) -> None:
    case(empty_store)


def test_other_fs(case: Case) -> None:
    case(other_fs)


def test_findings(case: Case) -> None:
    case(findings)


def test_unused_suppression(case: Case) -> None:
    case(unused_suppression)
