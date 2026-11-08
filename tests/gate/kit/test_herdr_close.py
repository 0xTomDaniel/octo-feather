"""The pytest items of tests/gate/kit/herdr_close.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from herdr_close import close_ids, park

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="herdr-close's sweep reads /proc")


def test_herdr_close_ids(case: Case) -> None:
    case(close_ids)


def test_herdr_close_park(case: Case) -> None:
    case(park)
