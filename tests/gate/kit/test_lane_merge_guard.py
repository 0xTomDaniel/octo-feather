"""The pytest items of tests/gate/kit/lane_merge_guard.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). The
items proving a criterion carry its tag, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_guard import carry, head, order, owner, relay_director_only, relayed, self_merge

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_merge_guard.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-merge-guard-owner", source=SOURCE)
def test_merge_guard_owner(case: Case) -> None:
    case(owner)


@pytest.mark.criterion("issue-lifecycle#acceptance-merge-guard-order", source=SOURCE)
def test_merge_guard_order(case: Case) -> None:
    case(order)


@pytest.mark.criterion("issue-lifecycle#acceptance-merge-relay-director-only", source=SOURCE)
def test_merge_relay_director_only(case: Case) -> None:
    case(relay_director_only)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-self-merge", source=SOURCE)
def test_merge_tier_self_merge(case: Case) -> None:
    case(self_merge)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-relayed", source=SOURCE)
def test_merge_tier_relayed(case: Case) -> None:
    case(relayed)


@pytest.mark.criterion("issue-lifecycle#acceptance-merge-guard-head", source=SOURCE)
def test_merge_guard_head(case: Case) -> None:
    case(head)


def test_merge_relay_carried(case: Case) -> None:
    case(carry)
