"""The pytest items of tests/gate/kit/herdr_messaging.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from herdr_messaging import (
    post_merge_busy,
    resume_live,
    say_lookup_fails,
    say_parked,
    say_stalled,
    spawn_dialog,
    spawn_plain,
    spawn_ready_late,
    tell_supervisors,
)

Case = Callable[..., None]


@pytest.mark.e2e
def test_spawn_ready_late(case: Case) -> None:
    case(spawn_ready_late)


def test_say_lookup_fails(case: Case) -> None:
    case(say_lookup_fails)


def test_say_stalled(case: Case) -> None:
    case(say_stalled)


@pytest.mark.e2e
def test_post_merge_busy(case: Case) -> None:
    case(post_merge_busy)


def test_herdr_spawn_plain(case: Case) -> None:
    case(spawn_plain)


def test_herdr_spawn_dialog(case: Case) -> None:
    case(spawn_dialog)


def test_herdr_say_resume_live(case: Case) -> None:
    case(resume_live)


def test_herdr_say_parked(case: Case) -> None:
    case(say_parked)


def test_post_merge_tell_supervisors(case: Case) -> None:
    case(tell_supervisors)
