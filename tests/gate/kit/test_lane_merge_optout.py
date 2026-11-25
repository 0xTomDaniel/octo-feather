"""The pytest items of tests/gate/kit/lane_merge_optout.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). The
items proving a criterion carry its tag, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_optout import demo, optout_cleared, optout_uncleared, owner_decision_verdict

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_merge_optout.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-owner-decision", source=SOURCE)
def test_merge_tier_owner_decision_verdict(case: Case) -> None:
    case(owner_decision_verdict)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-optout-cleared", source=SOURCE)
def test_merge_tier_optout_cleared(case: Case) -> None:
    case(optout_cleared)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-optout-uncleared", source=SOURCE)
def test_merge_tier_optout_uncleared(case: Case) -> None:
    case(optout_uncleared)


def test_merge_tier_optout_demo(case: Case) -> None:
    case(demo)
