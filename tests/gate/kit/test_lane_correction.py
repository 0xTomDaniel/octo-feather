"""The pytest items of tests/gate/kit/lane_correction.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_correction import (
    counts,
    kit_lane,
    legacy_quote,
    lifecycle,
    malformed,
    missed_at_once,
    one_target,
    other_lane,
    recurrence,
    reflection_missed,
    refusal,
    route_owner,
    routed,
    two_targets,
)

Case = Callable[..., None]


@pytest.mark.criterion("comms#acceptance-reflect-files-route-owner")
def test_lane_correction_route_owner(case: Case) -> None:
    case(route_owner)


def test_lane_correction_refusal(case: Case) -> None:
    case(refusal)


@pytest.mark.criterion("comms#acceptance-reflect-recurrence-comments")
def test_lane_correction_recurrence(case: Case) -> None:
    case(recurrence)


@pytest.mark.criterion("comms#acceptance-reflect-recurrence-comments")
def test_lane_correction_legacy_quote(case: Case) -> None:
    case(legacy_quote)


@pytest.mark.criterion("issue-lifecycle#acceptance-reflection-missed-lane")
def test_lane_correction_reflection_missed(case: Case) -> None:
    case(reflection_missed)


def test_lane_correction_kit_lane(case: Case) -> None:
    case(kit_lane)


def test_lane_correction_malformed(case: Case) -> None:
    case(malformed)


def test_lane_correction_two_targets(case: Case) -> None:
    case(two_targets)


def test_lane_correction_one_target(case: Case) -> None:
    case(one_target)


def test_lane_correction_missed_at_once(case: Case) -> None:
    case(missed_at_once)


def test_lane_correction_routed(case: Case) -> None:
    case(routed)


def test_lane_correction_counts(case: Case) -> None:
    case(counts)


def test_lane_correction_lifecycle(case: Case) -> None:
    case(lifecycle)


def test_lane_correction_other_lane(case: Case) -> None:
    case(other_lane)
