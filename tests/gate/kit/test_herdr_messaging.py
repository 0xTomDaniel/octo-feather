"""The pytest items of tests/gate/kit/herdr_messaging.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from herdr_messaging import (
    post_merge_busy,
    resume_gone,
    resume_live,
    say_lookup_fails,
    say_refused,
    say_resume_lane,
    say_resume_parent,
    say_stalled,
    spawn_cwd,
    spawn_dialog,
    spawn_mise_path,
    spawn_plain,
    spawn_ready_late,
    tell_failed,
    tell_gone,
    tell_kit,
    tell_live,
)

Case = Callable[..., None]


def test_spawn_ready_late(case: Case) -> None:
    case(spawn_ready_late)


def test_say_lookup_fails(case: Case) -> None:
    case(say_lookup_fails)


def test_say_stalled(case: Case) -> None:
    case(say_stalled)


def test_post_merge_busy(case: Case) -> None:
    case(post_merge_busy)


def test_herdr_spawn_plain(case: Case) -> None:
    case(spawn_plain)


def test_herdr_spawn_cwd(case: Case) -> None:
    case(spawn_cwd)


def test_herdr_spawn_dialog(case: Case) -> None:
    case(spawn_dialog)


def test_herdr_spawn_mise_path(case: Case) -> None:
    case(spawn_mise_path)


def test_herdr_say_resume_live(case: Case) -> None:
    case(resume_live)


def test_herdr_say_resume_gone(case: Case) -> None:
    case(resume_gone)


def test_herdr_say_resume_lane(case: Case) -> None:
    case(say_resume_lane)


def test_herdr_say_resume_parent(case: Case) -> None:
    case(say_resume_parent)


def test_herdr_say_refused(case: Case) -> None:
    case(say_refused)


def test_post_merge_tell_live(case: Case) -> None:
    case(tell_live)


def test_post_merge_tell_kit(case: Case) -> None:
    case(tell_kit)


def test_post_merge_tell_failed(case: Case) -> None:
    case(tell_failed)


def test_post_merge_tell_gone(case: Case) -> None:
    case(tell_gone)
