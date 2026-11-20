"""The pytest items of tests/gate/kit/lane_judge.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from lane_judge import (
    PICK,
    judge_posts,
    model_unavailable,
    no_gate_reads_it,
    real_suite,
    refusals,
    rerun_in_place,
    threshold,
)

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qa sandbox needs Linux")


def test_refusals(case: Case) -> None:
    case(refusals)


@pytest.mark.e2e  # the judge's classify in the real qa sandbox (quality spec #test-kinds)
def test_model_unavailable(case: Case) -> None:
    case(model_unavailable)


@pytest.mark.e2e  # the judge's classify in the real qa sandbox (quality spec #test-kinds)
def test_judge_posts(case: Case) -> None:
    case(judge_posts)


@pytest.mark.e2e  # the judge's classify in the real qa sandbox (quality spec #test-kinds)
def test_rerun_in_place(case: Case) -> None:
    case(rerun_in_place)


@pytest.mark.e2e  # the judge's classify in the real qa sandbox (quality spec #test-kinds)
def test_no_gate_reads_it(case: Case) -> None:
    case(no_gate_reads_it)


@pytest.mark.parametrize("q", sorted(set(PICK) - {"test-quality"}))
@pytest.mark.e2e  # the judge's classify in the real qa sandbox (quality spec #test-kinds)
def test_real_suite(case: Case, q: str) -> None:
    case(real_suite, q)


@pytest.mark.parametrize("which", ["below", "meets"])
@pytest.mark.e2e  # the judge's classify in the real qa sandbox (quality spec #test-kinds)
def test_threshold(case: Case, which: str) -> None:
    case(threshold, which)
