"""The pytest item of tests/gate/kit/cpu_budget.py's scenario (what it proves: its docstring), run
as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from cpu_budget import changed, e2e

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-test-cpu-budget")
def test_changed(case: Case) -> None:
    case(changed)


@pytest.mark.criterion("quality#acceptance-test-cpu-budget")
def test_e2e(case: Case) -> None:
    case(e2e)
