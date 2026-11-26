"""The pytest items of tests/gate/kit/launch_stash_guard.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from launch_stash_guard import refused, unchanged

Case = Callable[..., None]
SOURCE = "tests/gate/kit/launch_stash_guard.py"


@pytest.mark.criterion("roles#acceptance-stash-guard", source=SOURCE)
def test_refused(case: Case) -> None:
    case(refused)


@pytest.mark.criterion("roles#acceptance-stash-guard", source=SOURCE)
def test_unchanged(case: Case) -> None:
    case(unchanged)
