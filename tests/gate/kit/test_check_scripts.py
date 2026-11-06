"""The pytest item of tests/gate/kit/check_scripts.py's scenario (what it proves: its docstring),
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_scripts import scripts

Case = Callable[..., None]


def test_check_scripts_planted(case: Case) -> None:
    case(scripts)
