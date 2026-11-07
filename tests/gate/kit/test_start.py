"""The pytest items of tests/gate/kit/start.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from start import lanes, session

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="settled's subreaper needs Linux")


def test_start_session(case: Case) -> None:
    case(session)


def test_start_lanes(case: Case) -> None:
    case(lanes)
