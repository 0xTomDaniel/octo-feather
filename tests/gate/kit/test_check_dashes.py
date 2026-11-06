"""The pytest item of tests/gate/kit/check_dashes.py's scenario (what it proves: its docstring),
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_dashes import dashes

Case = Callable[..., None]


def test_check_dashes_planted(case: Case) -> None:
    case(dashes)
