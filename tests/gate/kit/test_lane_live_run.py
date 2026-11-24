"""The pytest items of tests/gate/kit/lane_live_run.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_live_run import refresh_waits, teardown_waits

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-refresh-waits-run", source="tests/gate/kit/lane_live_run.py"
)
def test_lane_live_run_refresh_waits(case: Case) -> None:
    case(refresh_waits)


def test_lane_live_run_teardown_waits(case: Case) -> None:
    case(teardown_waits)
