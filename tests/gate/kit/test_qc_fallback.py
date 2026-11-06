"""The pytest items of tests/gate/kit/qc_fallback.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_fallback import cap_stops, kill_stops, own_judges

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_qc_fallback_own_judges(case: Case) -> None:
    case(own_judges)


def test_qc_fallback_cap_stops(case: Case) -> None:
    case(cap_stops)


def test_qc_fallback_kill_stops(case: Case) -> None:
    case(kill_stops)
