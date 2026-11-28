"""The pytest items of tests/gate/kit/check_fake_gh.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from check_fake_gh import moved_off, new_use, no_default, passes, renamed, replayed

Case = Callable[..., None]


def test_check_fake_gh_passes(case: Case) -> None:
    case(passes)


def test_check_fake_gh_new_use(case: Case) -> None:
    case(new_use)


def test_check_fake_gh_moved_off(case: Case) -> None:
    case(moved_off)


def test_check_fake_gh_renamed(case: Case) -> None:
    case(renamed)


def test_check_fake_gh_no_default(case: Case) -> None:
    case(no_default)


def test_check_fake_gh_replayed(case: Case) -> None:
    case(replayed)
