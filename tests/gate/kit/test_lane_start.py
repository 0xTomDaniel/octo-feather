"""The pytest items of tests/gate/kit/lane_start.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_start import exists, refused, rerun, started, unicode_title

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start", source="tests/gate/kit/lane_start.py"
)
def test_lane_start_started(case: Case) -> None:
    case(started)


def test_lane_start_unicode_title(case: Case) -> None:
    case(unicode_title)


def test_lane_start_refused(case: Case) -> None:
    case(refused)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start-exists", source="tests/gate/kit/lane_start.py"
)
def test_lane_start_exists(case: Case) -> None:
    case(exists)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start-rerun", source="tests/gate/kit/lane_start.py"
)
def test_lane_start_rerun(case: Case) -> None:
    case(rerun)
