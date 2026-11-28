"""The pytest items of tests/gate/kit/lane_start.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_start import (
    behind_kit,
    exists,
    filed_stopped,
    files,
    help_,
    refused,
    rerun,
    started,
    sub_issue,
    unicode_title,
    unknown_send,
)

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start",
    "issue-lifecycle#acceptance-lane-start-clear",
    source="tests/gate/kit/lane_start.py",
)
def test_lane_start_started(case: Case) -> None:
    case(started)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start-unread", source="tests/gate/kit/lane_start.py"
)
def test_lane_start_unicode_title(case: Case) -> None:
    case(unicode_title)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start-usage",
    "issue-lifecycle#acceptance-lane-start-carried",
    source="tests/gate/kit/lane_start.py",
)
def test_lane_start_refused(case: Case) -> None:
    case(refused)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start-files",
    "issue-lifecycle#acceptance-lane-start-unread",
    source="tests/gate/kit/lane_start.py",
)
def test_lane_start_files(case: Case) -> None:
    case(files)


def test_lane_start_filed_stopped(case: Case) -> None:
    case(filed_stopped)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start-sub-issue", source="tests/gate/kit/lane_start.py"
)
def test_lane_start_sub_issue(case: Case) -> None:
    case(sub_issue)


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


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start-rerun", source="tests/gate/kit/lane_start.py"
)
def test_lane_start_unknown_send(case: Case) -> None:
    case(unknown_send)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-lane-start-current-kit", source="tests/gate/kit/lane_start.py"
)
def test_lane_start_behind_kit(case: Case) -> None:
    case(behind_kit)


def test_lane_start_help(case: Case) -> None:
    case(help_)
