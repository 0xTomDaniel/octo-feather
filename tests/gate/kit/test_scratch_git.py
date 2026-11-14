"""The pytest item of tests/gate/kit/scratch_git.py's scenario (what it proves: its docstring), run
as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from scratch_git import no_auto_maintenance

Case = Callable[..., None]


def test_no_auto_maintenance(case: Case) -> None:
    case(no_auto_maintenance)
