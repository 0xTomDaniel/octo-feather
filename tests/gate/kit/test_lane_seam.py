"""The pytest items of tests/gate/kit/lane_seam.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_seam import github, linear, rule

Case = Callable[..., None]


def test_lane_seam_github(case: Case) -> None:
    case(github)


def test_lane_seam_rule(case: Case) -> None:
    case(rule)


def test_lane_seam_linear(case: Case) -> None:
    case(linear)
