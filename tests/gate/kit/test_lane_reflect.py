"""The pytest items of tests/gate/kit/lane_reflect.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_reflect import alone, archive_findings, refusals

Case = Callable[..., None]


def test_lane_reflect_alone(case: Case) -> None:
    case(alone)


def test_lane_reflect_archive_findings(case: Case) -> None:
    case(archive_findings)


def test_lane_reflect_refusals(case: Case) -> None:
    case(refusals)
