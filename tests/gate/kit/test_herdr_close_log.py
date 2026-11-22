"""The pytest items of tests/gate/kit/herdr_close_log.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from herdr_close_log import close_line, close_no_log, close_not_recorded, close_space

Case = Callable[..., None]


@pytest.mark.criterion("comms#acceptance-close-line")
def test_close_line(case: Case) -> None:
    case(close_line)


@pytest.mark.criterion("comms#acceptance-close-no-log")
def test_close_no_log(case: Case) -> None:
    case(close_no_log)


def test_close_not_recorded(case: Case) -> None:
    case(close_not_recorded)


def test_close_space(case: Case) -> None:
    case(close_space)
