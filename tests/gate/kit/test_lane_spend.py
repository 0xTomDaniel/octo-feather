"""The pytest item of tests/gate/kit/lane_spend.py's scenarios (what they prove: its docstring), all
run as that file's command, one item (testkit.together), through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_spend import LANE_SPEND

Case = Callable[..., None]


def test_lane_spend(case: Case) -> None:
    case(LANE_SPEND)
