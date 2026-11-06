"""The pytest items of tests/gate/kit/integrate.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py); items proving a
criterion carry its tag, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from integrate import brownfield, lanes, tiers

Case = Callable[..., None]
SOURCE = "tests/gate/kit/integrate.py"


def test_integrate_lanes(case: Case) -> None:
    case(lanes)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-pilot-full",
    "issue-lifecycle#acceptance-integrate-fast",
    "issue-lifecycle#acceptance-integrate-checkpoint",
    source=SOURCE,
)
def test_integrate_tiers(case: Case) -> None:
    case(tiers)


@pytest.mark.criterion("issue-lifecycle#acceptance-brownfield-full", source=SOURCE)
def test_integrate_brownfield(case: Case) -> None:
    case(brownfield)
