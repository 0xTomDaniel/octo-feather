"""The pytest items of tests/gate/kit/launch_stash_guard.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from launch_stash_guard import one_worktree, pane_path, refused, unchanged

Case = Callable[..., None]


def test_refused(case: Case) -> None:
    case(refused)


def test_one_worktree(case: Case) -> None:
    case(one_worktree)


def test_unchanged(case: Case) -> None:
    case(unchanged)


def test_pane_path(case: Case) -> None:
    case(pane_path)
