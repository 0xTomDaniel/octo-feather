"""The pytest items of tests/gate/kit/install_check_auto_install.py's scenarios (what they prove:
its docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from install_check_auto_install import off, on

Case = Callable[..., None]


@pytest.mark.e2e  # the box's real mise installs and shim run (quality spec #test-kinds)
def test_on(case: Case) -> None:
    case(on)


@pytest.mark.e2e  # the box's real mise installs and shim run (quality spec #test-kinds)
def test_off(case: Case) -> None:
    case(off)
