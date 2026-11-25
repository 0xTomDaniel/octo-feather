"""The pytest items of tests/gate/kit/start_relaunch.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py).
relaunch_own_scope is end to end: it needs the box's real systemd user manager (CI: linger,
.github/workflows)."""

import sys
from collections.abc import Callable

import pytest
from start_relaunch import relaunch_busy, relaunch_own_scope, resume_same_session

Case = Callable[..., None]


def test_relaunch_busy(case: Case) -> None:
    case(relaunch_busy)


@pytest.mark.e2e
@pytest.mark.skipif(sys.platform == "darwin", reason="systemd user scopes are Linux only")
def test_relaunch_own_scope(case: Case) -> None:
    case(relaunch_own_scope)


def test_resume_same_session(case: Case) -> None:
    case(resume_same_session)
