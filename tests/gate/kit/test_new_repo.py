"""The pytest item of tests/gate/kit/new_repo.py's scenario (what it proves: its docstring), run
as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from new_repo import new_repo

Case = Callable[..., None]


def test_new_repo(case: Case) -> None:
    case(new_repo)
