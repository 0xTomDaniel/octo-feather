"""The pytest item of tests/gate/kit/mise_offline.py's scenario (what it proves: its docstring),
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from mise_offline import empty_data_dir

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="unshare -rn needs Linux")


def test_empty_data_dir(case: Case) -> None:
    case(empty_data_dir)
