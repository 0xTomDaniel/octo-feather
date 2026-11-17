"""The pytest item of tests/gate/kit/lane_intake.py's scenario (what it proves: its docstring),
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_intake import intake

Case = Callable[..., None]


def test_lane_intake(case: Case) -> None:
    case(intake)
