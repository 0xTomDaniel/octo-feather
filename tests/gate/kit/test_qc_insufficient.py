"""The pytest items of tests/gate/kit/qc_insufficient.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_insufficient import kit_style, named, rerun

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_qc_insufficient_named(case: Case) -> None:
    case(named)


def test_qc_insufficient_rerun(case: Case) -> None:
    case(rerun)


def test_qc_insufficient_kit_style(case: Case) -> None:
    case(kit_style)
