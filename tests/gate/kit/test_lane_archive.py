"""The pytest item of tests/gate/kit/lane_archive.py's scenarios (what they prove: its docstring),
all run as that file's command, one item (testkit.together), through `case`
(tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_archive import LANE_ARCHIVE

Case = Callable[..., None]


def test_lane_archive(case: Case) -> None:
    case(LANE_ARCHIVE)
