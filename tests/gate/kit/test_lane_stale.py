"""The pytest items of tests/gate/kit/lane_stale.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from lane_stale import stale_agents, stale_herdr_extension, stale_malformed

Case = Callable[..., None]
linux = pytest.mark.skipif(sys.platform == "darwin", reason="the Herdr stand-in reads /proc")
criterion = pytest.mark.criterion(
    "issue-lifecycle#acceptance-stale-agents", source="tests/gate/kit/lane_stale.py"
)


@linux
@criterion
def test_lane_stale_agents(case: Case) -> None:
    case(stale_agents)


@linux
@criterion
def test_lane_stale_herdr_extension(case: Case) -> None:
    case(stale_herdr_extension)


@criterion
def test_lane_stale_malformed(case: Case) -> None:
    case(stale_malformed)
