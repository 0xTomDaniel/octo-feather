"""The pytest items of tests/gate/kit/qc_copies.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_copies import credential_copies, pi_refresh, pi_rewrite

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_qc_copies_credential_copies(case: Case) -> None:
    case(credential_copies)


def test_qc_copies_pi_rewrite(case: Case) -> None:
    case(pi_rewrite)


def test_qc_copies_pi_refresh(case: Case) -> None:
    case(pi_refresh)
