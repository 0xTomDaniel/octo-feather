"""The pytest item of tests/gate/kit/qc_sandbox_cost.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_sandbox_cost import cost, selection

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_installed_herdr(case: Case) -> None:
    case(selection)


@pytest.mark.e2e  # a CPU check over real sandbox runs (quality spec #test-kinds)
def test_cost(case: Case) -> None:
    case(cost)
