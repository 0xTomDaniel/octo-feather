"""The pytest items of tests/gate/kit/lane_seam.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_seam import gh840, linear

Case = Callable[..., None]


def test_lane_seam_gh840(case: Case) -> None:
    case(gh840)


def test_lane_seam_linear(case: Case) -> None:
    case(linear)
