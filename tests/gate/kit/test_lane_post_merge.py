"""The pytest items of tests/gate/kit/lane_post_merge.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_post_merge import (
    checkout_follows,
    checkout_kept,
    install_kept,
    install_stops,
    kit_refresh,
    late_run,
    main_ci,
    merged_step,
    no_ci,
    superseded,
)

Case = Callable[..., None]


def test_lane_post_merge_merged_step(case: Case) -> None:
    case(merged_step)


def test_lane_post_merge_main_ci(case: Case) -> None:
    case(main_ci)


@pytest.mark.e2e  # post-merge's own poll waits on the wall clock (quality spec #test-kinds)
def test_lane_post_merge_late_run(case: Case) -> None:
    case(late_run)


def test_lane_post_merge_no_ci(case: Case) -> None:
    case(no_ci)


def test_lane_post_merge_superseded(case: Case) -> None:
    case(superseded)


def test_lane_post_merge_kit_refresh(case: Case) -> None:
    case(kit_refresh)


def test_lane_post_merge_install_stops(case: Case) -> None:
    case(install_stops)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-checkout-follows-main", source="tests/gate/kit/lane_post_merge.py"
)
def test_lane_post_merge_checkout_follows(case: Case) -> None:
    case(checkout_follows)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-checkout-kept", source="tests/gate/kit/lane_post_merge.py"
)
def test_lane_post_merge_checkout_kept(case: Case) -> None:
    case(checkout_kept)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-checkout-kept", source="tests/gate/kit/lane_post_merge.py"
)
def test_lane_post_merge_install_kept(case: Case) -> None:
    case(install_kept)
