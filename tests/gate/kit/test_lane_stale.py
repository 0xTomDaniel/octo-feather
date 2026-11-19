"""The pytest item of tests/gate/kit/lane_stale.py's scenario (what it proves: its docstring), run
as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from lane_stale import stale_agents

Case = Callable[..., None]


@pytest.mark.skipif(
    sys.platform == "darwin", reason="the Herdr stand-in reads its Pi stand-ins from /proc"
)
@pytest.mark.criterion(
    "issue-lifecycle#acceptance-stale-agents", source="tests/gate/kit/lane_stale.py"
)
def test_lane_stale_agents(case: Case) -> None:
    case(stale_agents)
