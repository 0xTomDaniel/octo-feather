"""Public coverage validation against real eval input copies."""

from collections.abc import Callable

from qa_coverage import coverage_gap, tracker_coverage


def test_coverage_gap(case: Callable[..., None]) -> None:
    case(coverage_gap)


def test_tracker_coverage(case: Callable[..., None]) -> None:
    case(tracker_coverage)
