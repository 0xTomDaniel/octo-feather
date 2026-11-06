"""The pytest items of tests/gate/kit/fast.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from fast import past_full_pass, selects

Case = Callable[..., None]


def test_fast_selects(case: Case) -> None:
    case(selects)


def test_fast_past_full_pass(case: Case) -> None:
    case(past_full_pass)
