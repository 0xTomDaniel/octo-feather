"""The pytest items of tests/gate/kit/lane_post_merge_map.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_post_merge_map import after_merge, build_failed, full_daily

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-map-after-merge")
def test_post_merge_maps_the_merge(case: Case) -> None:
    case(after_merge)


@pytest.mark.criterion("quality#acceptance-map-full-daily")
def test_post_merge_maps_full_daily(case: Case) -> None:
    case(full_daily)


@pytest.mark.criterion("quality#acceptance-map-build-failed")
def test_post_merge_map_build_failed(case: Case) -> None:
    case(build_failed)
