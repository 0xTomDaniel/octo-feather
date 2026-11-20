"""The pytest items of tests/gate/kit/herdr_extension.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from herdr_extension import close_ends_extension, own_extension

Case = Callable[..., None]
linux = pytest.mark.skipif(sys.platform == "darwin", reason="the Herdr stand-in reads /proc")


@linux
def test_herdr_extension_own(case: Case) -> None:
    case(own_extension)


@linux
def test_herdr_extension_close(case: Case) -> None:
    case(close_ends_extension)
