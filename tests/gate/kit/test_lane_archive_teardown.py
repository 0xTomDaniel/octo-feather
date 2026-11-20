"""The pytest items of tests/gate/kit/lane_archive_teardown.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_archive_teardown import (
    archive_tears_down,
    archive_waits,
    no_manager,
    unit_fails,
    unit_killed,
)

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_archive_teardown.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-archive-tears-down", source=SOURCE)
@pytest.mark.criterion("comms#acceptance-close-message", source=SOURCE)
def test_lane_archive_tears_down(case: Case) -> None:
    case(archive_tears_down)


def test_lane_archive_teardown_no_manager(case: Case) -> None:
    case(no_manager)


def test_lane_archive_waits(case: Case) -> None:
    case(archive_waits)


def test_lane_archive_teardown_unit_fails(case: Case) -> None:
    case(unit_fails)


def test_lane_archive_teardown_unit_killed(case: Case) -> None:
    case(unit_killed)
