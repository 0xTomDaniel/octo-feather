"""The pytest item of tests/gate/kit/lane_post_merge.py's scenarios (what they prove: its
docstring), all run as that file's command, one item (testkit.together), through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_post_merge import LANE_POST_MERGE

Case = Callable[..., None]


def test_lane_post_merge(case: Case) -> None:
    case(LANE_POST_MERGE)
