"""The pytest items of tests/gate/kit/lane_correction.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_correction import kit_lane, recurrence, reflection_missed

Case = Callable[..., None]


def test_lane_correction_recurrence(case: Case) -> None:
    case(recurrence)


def test_lane_correction_reflection_missed(case: Case) -> None:
    case(reflection_missed)


def test_lane_correction_kit_lane(case: Case) -> None:
    case(kit_lane)
