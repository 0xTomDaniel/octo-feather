"""The pytest items of tests/gate/kit/hook_guards.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from hook_guards import refused, skipped

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-setup-not-factory")
def test_setup_refused_in_factory(case: Case) -> None:
    case(refused)


@pytest.mark.criterion("quality#acceptance-hook-machine-commit")
def test_machine_commit_skips_fast_tier(case: Case) -> None:
    case(skipped)
