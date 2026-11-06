"""The pytest items of tests/gate/kit/check_refs.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_refs import broken, in_gate, planted

Case = Callable[..., None]


def test_check_refs_planted(case: Case) -> None:
    case(planted)


def test_check_refs_broken(case: Case) -> None:
    case(broken)


def test_check_refs_in_gate(case: Case) -> None:
    case(in_gate)
