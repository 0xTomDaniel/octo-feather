"""The pytest items of tests/gate/kit/launch_stash_guard.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from launch_stash_guard import private_path, refused, unchanged, untrusted

Case = Callable[..., None]
SOURCE = "tests/gate/kit/launch_stash_guard.py"


@pytest.mark.criterion("roles#acceptance-stash-guard", source=SOURCE)
def test_refused(case: Case) -> None:
    case(refused)


@pytest.mark.criterion("roles#acceptance-stash-guard", source=SOURCE)
def test_unchanged(case: Case) -> None:
    case(unchanged)


@pytest.mark.criterion("roles#acceptance-stash-guard-private-path", source=SOURCE)
def test_private_path(case: Case) -> None:
    case(private_path)


@pytest.mark.criterion("roles#acceptance-stash-guard-private-path", source=SOURCE)
def test_untrusted(case: Case) -> None:
    case(untrusted)
