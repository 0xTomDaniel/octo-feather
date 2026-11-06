"""The pytest items of tests/gate/kit/integrate_slot.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from integrate_slot import red, refused

Case = Callable[..., None]


def test_refused(case: Case) -> None:
    case(refused)


def test_red(case: Case) -> None:
    case(red)
