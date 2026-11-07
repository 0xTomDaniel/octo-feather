"""The pytest items of tests/gate/kit/review_host.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from review_host import refusals, servers

Case = Callable[..., None]


def test_review_host_refusals(case: Case) -> None:
    case(refusals)


# e2e (quality#test-kinds): its purpose is Spec Chat's real review server working on loopback.
@pytest.mark.e2e
@pytest.mark.skipif(
    sys.platform == "darwin", reason="its subreaper and no-/proc namespace need Linux"
)
def test_review_host_servers(case: Case) -> None:
    case(servers)
