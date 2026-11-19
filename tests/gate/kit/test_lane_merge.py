"""The pytest items of tests/gate/kit/lane_merge.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_merge import merge_starts_routine, refused, resume

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-starts-routine", source="tests/gate/kit/lane_merge.py"
)
def test_lane_merge_starts_routine(case: Case) -> None:
    case(merge_starts_routine)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-starts-routine", source="tests/gate/kit/lane_merge.py"
)
def test_lane_merge_resume(case: Case) -> None:
    case(resume)


def test_lane_merge_refused(case: Case) -> None:
    case(refused)
