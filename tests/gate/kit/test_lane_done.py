"""The pytest item of tests/gate/kit/lane_done.py's scenarios (what they prove: its docstring), all
run as that file's command, one item (testkit.together), through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_done import LANE_DONE

Case = Callable[..., None]


def test_lane_done(case: Case) -> None:
    case(LANE_DONE)
