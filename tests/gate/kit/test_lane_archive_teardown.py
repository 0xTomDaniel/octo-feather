"""The pytest items of tests/gate/kit/lane_archive_teardown.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_archive_teardown import (
    archive_tears_down,
    archive_waits,
    director_unread,
    no_manager,
    red_main,
    shared_supervisor_kept,
    unit_fails,
    unit_killed,
    unit_start_fails,
    watch_gh_gone,
)

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_archive_teardown.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-archive-tears-down", source=SOURCE)
@pytest.mark.criterion("comms#acceptance-close-message", source=SOURCE)
def test_lane_archive_tears_down(case: Case) -> None:
    case(archive_tears_down)


@pytest.mark.criterion("comms#acceptance-shared-supervisor-kept", source=SOURCE)
def test_lane_archive_shared_supervisor_kept(case: Case) -> None:
    case(shared_supervisor_kept)


def test_lane_archive_teardown_no_manager(case: Case) -> None:
    case(no_manager)


def test_lane_archive_waits(case: Case) -> None:
    case(archive_waits)


@pytest.mark.criterion("issue-lifecycle#acceptance-red-main-stops", source=SOURCE)
def test_lane_archive_red_main(case: Case) -> None:
    case(red_main)


@pytest.mark.criterion("issue-lifecycle#acceptance-red-main-stops", source=SOURCE)
def test_lane_archive_director_unread(case: Case) -> None:
    case(director_unread)


@pytest.mark.criterion("issue-lifecycle#acceptance-red-main-stops", source=SOURCE)
def test_lane_archive_watch_gh_gone(case: Case) -> None:
    case(watch_gh_gone)


def test_lane_archive_teardown_unit_fails(case: Case) -> None:
    case(unit_fails)


def test_lane_archive_teardown_unit_killed(case: Case) -> None:
    case(unit_killed)


def test_lane_archive_teardown_unit_start_fails(case: Case) -> None:
    case(unit_start_fails)
