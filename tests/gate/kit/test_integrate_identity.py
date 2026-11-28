"""The pytest items of tests/gate/kit/integrate_identity.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from integrate_identity import conflict, unset

Case = Callable[..., None]


def test_unset(case: Case) -> None:
    case(unset)


def test_conflict(case: Case) -> None:
    case(conflict)
