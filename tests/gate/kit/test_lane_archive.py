"""The pytest items of tests/gate/kit/lane_archive.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_archive import archived, read_only, refusals

Case = Callable[..., None]


def test_lane_archive_archived(case: Case) -> None:
    case(archived)


def test_lane_archive_refusals(case: Case) -> None:
    case(refusals)


def test_lane_archive_read_only(case: Case) -> None:
    case(read_only)
