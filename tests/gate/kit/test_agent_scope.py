"""The pytest items of tests/gate/kit/agent_scope.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py).
End to end: each needs the box's real systemd user manager (CI: linger, .github/workflows)."""

import sys
from collections.abc import Callable

import pytest
from agent_scope import close_owned, close_unowned, spawn_no_manager, spawn_scoped

Case = Callable[..., None]
linux = pytest.mark.skipif(sys.platform == "darwin", reason="systemd user scopes are Linux only")


@pytest.mark.e2e
@linux
def test_spawn_scoped(case: Case) -> None:
    case(spawn_scoped)


@pytest.mark.e2e
@linux
def test_spawn_no_manager(case: Case) -> None:
    case(spawn_no_manager)


@pytest.mark.e2e
@linux
def test_close_owned(case: Case) -> None:
    case(close_owned)


@pytest.mark.e2e
@linux
def test_close_unowned(case: Case) -> None:
    case(close_unowned)
