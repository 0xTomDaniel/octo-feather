"""The pytest items of tests/gate/kit/lane_correction.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_correction import counts, lifecycle, other_lane, routed

Case = Callable[..., None]


def test_lane_correction_lifecycle(case: Case) -> None:
    case(lifecycle)


def test_lane_correction_other_lane(case: Case) -> None:
    case(other_lane)


def test_lane_correction_routed(case: Case) -> None:
    case(routed)


def test_lane_correction_counts(case: Case) -> None:
    case(counts)
