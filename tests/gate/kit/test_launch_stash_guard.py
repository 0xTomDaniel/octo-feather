"""The pytest items of tests/gate/kit/launch_stash_guard.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from launch_stash_guard import refused, unchanged

Case = Callable[..., None]


def test_refused(case: Case) -> None:
    case(refused)


def test_unchanged(case: Case) -> None:
    case(unchanged)
