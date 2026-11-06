"""The pytest items of tests/gate/kit/lane_post_merge.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_post_merge import kit_refresh, main_ci, merged_step, superseded

Case = Callable[..., None]


def test_lane_post_merge_merged_step(case: Case) -> None:
    case(merged_step)


def test_lane_post_merge_main_ci(case: Case) -> None:
    case(main_ci)


def test_lane_post_merge_superseded(case: Case) -> None:
    case(superseded)


def test_lane_post_merge_kit_refresh(case: Case) -> None:
    case(kit_refresh)
