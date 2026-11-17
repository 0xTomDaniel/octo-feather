"""The pytest items of tests/gate/kit/lane_ci_start.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). Each
proves part of its criterion, so carries the tag, its source that file (quality #qc-capture).
started and not_started wait on the wall clock (ci-start's polls), so are end-to-end (quality
#test-kinds)."""

from collections.abc import Callable

import pytest
from lane_ci_start import not_started, refusals, started

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_ci_start.py"
CRITERION = "issue-lifecycle#acceptance-ci-alongside"


@pytest.mark.criterion(CRITERION, source=SOURCE)
def test_lane_ci_start_refusals(case: Case) -> None:
    case(refusals)


@pytest.mark.e2e
@pytest.mark.criterion(CRITERION, source=SOURCE)
def test_lane_ci_start_started(case: Case) -> None:
    case(started)


@pytest.mark.e2e
@pytest.mark.criterion(CRITERION, source=SOURCE)
def test_lane_ci_start_not_started(case: Case) -> None:
    case(not_started)
