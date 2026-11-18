"""The pytest items of tests/gate/kit/qc_sandbox_gone.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_sandbox_gone import repo_gone, repo_recreated, worktrees_gone

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
def test_repo_gone(case: Case) -> None:
    case(repo_gone)


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
def test_worktrees_gone(case: Case) -> None:
    case(worktrees_gone)


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
def test_repo_recreated(case: Case) -> None:
    case(repo_recreated)
