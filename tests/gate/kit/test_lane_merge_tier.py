"""The pytest items of tests/gate/kit/lane_merge_tier.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). The
items proving a criterion carry its tag, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_tier import (
    failing_ask,
    order_waits,
    owner_decision,
    spec_pr,
    tier_failed,
    tier_one,
)

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_merge_tier.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-one", source=SOURCE)
def test_merge_tier_one(case: Case) -> None:
    case(tier_one)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-failed", source=SOURCE)
def test_merge_tier_failed(case: Case) -> None:
    case(tier_failed)


def test_merge_tier_owner_decision(case: Case) -> None:
    case(owner_decision)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-order-waits", source=SOURCE)
def test_merge_tier_order_waits(case: Case) -> None:
    case(order_waits)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-spec-pr", source=SOURCE)
def test_merge_tier_spec_pr(case: Case) -> None:
    case(spec_pr)


def test_merge_tier_failing_ask(case: Case) -> None:
    case(failing_ask)
