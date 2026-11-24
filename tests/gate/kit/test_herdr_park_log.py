"""The pytest items of tests/gate/kit/herdr_park_log.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from herdr_park_log import park_close_fails, park_line, park_no_log

Case = Callable[..., None]


@pytest.mark.criterion("comms#acceptance-park-line")
def test_park_line(case: Case) -> None:
    case(park_line)


def test_park_no_log(case: Case) -> None:
    case(park_no_log)


def test_park_close_fails(case: Case) -> None:
    case(park_close_fails)
