"""The pytest item of tests/gate/kit/lane_correction.py's scenarios (what they prove: its
docstring), all run as that file's command, one item (testkit.together), through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_correction import LANE_CORRECTION

Case = Callable[..., None]


def test_lane_correction(case: Case) -> None:
    case(LANE_CORRECTION)
