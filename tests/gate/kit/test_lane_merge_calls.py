"""The pytest items of tests/gate/kit/lane_merge_calls.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). The
items proving a criterion carry its tag, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_calls import (
    tier_adds,
    tier_clarify,
    tier_denied,
    tier_highest,
    tier_ruled,
    tier_ruling_unconfirmed,
    tier_weakens,
)

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_merge_calls.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-clarify", source=SOURCE)
def test_merge_tier_clarify(case: Case) -> None:
    case(tier_clarify)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-adds", source=SOURCE)
def test_merge_tier_adds(case: Case) -> None:
    case(tier_adds)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-weakens", source=SOURCE)
def test_merge_tier_weakens(case: Case) -> None:
    case(tier_weakens)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-ruled", source=SOURCE)
def test_merge_tier_ruled(case: Case) -> None:
    case(tier_ruled)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-ruling-unconfirmed", source=SOURCE)
def test_merge_tier_ruling_unconfirmed(case: Case) -> None:
    case(tier_ruling_unconfirmed)


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-highest", source=SOURCE)
def test_merge_tier_highest(case: Case) -> None:
    case(tier_highest)


def test_merge_tier_denied(case: Case) -> None:
    case(tier_denied)
