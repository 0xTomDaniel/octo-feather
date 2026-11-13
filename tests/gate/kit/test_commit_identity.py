"""The pytest items of tests/gate/kit/commit_identity.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from commit_identity import applied, no_commit, read_only, unset

Case = Callable[..., None]


def test_applied(case: Case) -> None:
    case(applied)


def test_unset(case: Case) -> None:
    case(unset)


def test_read_only(case: Case) -> None:
    case(read_only)


def test_no_commit(case: Case) -> None:
    case(no_commit)
