"""The pytest items of tests/gate/kit/qc_capture.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_capture import fallback_beside, invalid_demo, twice

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_qc_capture_twice(case: Case) -> None:
    case(twice)


def test_qc_capture_fallback_beside(case: Case) -> None:
    case(fallback_beside)


def test_qc_capture_invalid_demo(case: Case) -> None:
    case(invalid_demo)
