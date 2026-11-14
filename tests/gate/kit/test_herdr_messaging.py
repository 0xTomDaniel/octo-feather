"""The pytest items of tests/gate/kit/herdr_messaging.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from herdr_messaging import (
    post_merge_busy,
    say_lookup_fails,
    say_resumes_parked,
    say_stalled,
    spawn_fails_closed,
    spawn_one_bound,
    spawn_ready_late,
)

Case = Callable[..., None]


def test_spawn_ready_late(case: Case) -> None:
    case(spawn_ready_late)


def test_spawn_fails_closed(case: Case) -> None:
    case(spawn_fails_closed)


def test_spawn_one_bound(case: Case) -> None:
    case(spawn_one_bound)


def test_say_resumes_parked(case: Case) -> None:
    case(say_resumes_parked)


def test_say_lookup_fails(case: Case) -> None:
    case(say_lookup_fails)


def test_say_stalled(case: Case) -> None:
    case(say_stalled)


def test_post_merge_busy(case: Case) -> None:
    case(post_merge_busy)
