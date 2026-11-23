"""The pytest items of tests/gate/kit/fast_hook.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from fast_hook import green, red

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-fast-hook")
def test_red_commit_refused(case: Case) -> None:
    case(red)


@pytest.mark.criterion("quality#acceptance-fast-hook")
def test_fixed_commit_goes_through(case: Case) -> None:
    case(green)
