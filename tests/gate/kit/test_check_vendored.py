"""The pytest items of tests/gate/kit/check_vendored.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from check_vendored import cache_faults, findings, stalled_fetch

Case = Callable[..., None]


def test_check_vendored_findings(case: Case) -> None:
    case(findings)


def test_check_vendored_cache_faults(case: Case) -> None:
    case(cache_faults)


# A wall-clock proof (quality #test-kinds): each fetch waits out its own 2 s bound on a stalled or
# dripping proxy, so the full tier only.
@pytest.mark.e2e
def test_check_vendored_stalled_fetch(case: Case) -> None:
    case(stalled_fetch)
