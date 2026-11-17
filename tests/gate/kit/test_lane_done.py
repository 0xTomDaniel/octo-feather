"""The pytest items of tests/gate/kit/lane_done.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_done import github, linear

Case = Callable[..., None]


def test_lane_done_github(case: Case) -> None:
    case(github)


def test_lane_done_linear(case: Case) -> None:
    case(linear)
