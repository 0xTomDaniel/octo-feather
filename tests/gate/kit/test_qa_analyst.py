"""The pytest items of tests/gate/kit/qa_analyst.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qa_analyst import analyze_usage, comparison, no_baseline, variance

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qa sandbox needs Linux")


def test_comparison(case: Case) -> None:
    case(comparison)


def test_variance(case: Case) -> None:
    case(variance)


def test_no_baseline(case: Case) -> None:
    case(no_baseline)


def test_analyze_usage(case: Case) -> None:
    case(analyze_usage)
