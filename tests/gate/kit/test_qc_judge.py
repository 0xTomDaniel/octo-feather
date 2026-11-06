"""The pytest items of tests/gate/kit/qc_judge.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_judge import no_sandbox, role_file, status_commit

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_qc_judge_no_sandbox(case: Case) -> None:
    case(no_sandbox)


def test_qc_judge_status_commit(case: Case) -> None:
    case(status_commit)


def test_qc_judge_role_file(case: Case) -> None:
    case(role_file)
