"""The pytest items of tests/gate/kit/lane_post_merge_teardown.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_post_merge_teardown import kept, no_ci, not_archived, own_space, shared_space

Case = Callable[..., None]


def test_lane_post_merge_teardown_not_archived(case: Case) -> None:
    case(not_archived)


def test_lane_post_merge_teardown_own_space(case: Case) -> None:
    case(own_space)


def test_lane_post_merge_teardown_no_ci(case: Case) -> None:
    case(no_ci)


def test_lane_post_merge_teardown_shared_space(case: Case) -> None:
    case(shared_space)


def test_lane_post_merge_teardown_kept(case: Case) -> None:
    case(kept)
