"""The pytest items of tests/gate/kit/qc_uv_cache.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_uv_cache import colored, not_a_dir

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


@pytest.mark.e2e  # the real qc sandbox runs (quality spec #test-kinds)
def test_colored(case: Case) -> None:
    case(colored)


def test_not_a_dir(case: Case) -> None:
    case(not_a_dir)
