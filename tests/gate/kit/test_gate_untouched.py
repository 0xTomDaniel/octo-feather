"""The pytest item of tests/gate/kit/gate_untouched.py's scenario (what it proves: its docstring),
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from gate_untouched import concurrent, seeded

Case = Callable[..., None]


def test_seeded(case: Case) -> None:
    case(seeded)


def test_concurrent(case: Case) -> None:
    case(concurrent)
