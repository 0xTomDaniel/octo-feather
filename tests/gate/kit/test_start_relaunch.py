"""The pytest items of tests/gate/kit/start_relaunch.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py).
relaunch_own_scope is end to end: it needs the box's real systemd user manager (CI: linger,
.github/workflows)."""

import sys
from collections.abc import Callable

import pytest
from start_relaunch import (
    relaunch_busy,
    relaunch_own_scope,
    relaunch_short_wait,
    resume_same_session,
)

Case = Callable[..., None]


@pytest.mark.criterion("comms#acceptance-director-relaunch-busy")
def test_relaunch_busy(case: Case) -> None:
    case(relaunch_busy)


@pytest.mark.criterion("comms#acceptance-director-relaunch-busy")
def test_relaunch_short_wait(case: Case) -> None:
    case(relaunch_short_wait)


@pytest.mark.e2e
@pytest.mark.criterion("comms#acceptance-director-relaunch-own-scope")
@pytest.mark.skipif(sys.platform == "darwin", reason="systemd user scopes are Linux only")
def test_relaunch_own_scope(case: Case) -> None:
    case(relaunch_own_scope)


@pytest.mark.criterion("comms#acceptance-director-relaunch-same-session")
def test_resume_same_session(case: Case) -> None:
    case(resume_same_session)
