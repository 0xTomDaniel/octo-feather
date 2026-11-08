"""The pytest items of tests/gate/kit/lever.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lever import executable_need, interrupted, stale

Case = Callable[..., None]


def test_lever_interrupted(case: Case) -> None:
    case(interrupted)


def test_lever_stale(case: Case) -> None:
    case(stale)


def test_lever_executable_need(case: Case) -> None:
    case(executable_need)
