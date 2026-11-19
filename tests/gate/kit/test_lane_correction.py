"""The pytest items of tests/gate/kit/lane_correction.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py): the
correction filer's wiring into the commands; its rules: test_lane_correction_filer.py."""

from collections.abc import Callable

from lane_correction import archive, reflect

Case = Callable[..., None]


def test_lane_correction_archive(case: Case) -> None:
    case(archive)


def test_lane_correction_reflect(case: Case) -> None:
    case(reflect)
