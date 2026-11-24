"""The pytest item of tests/gate/kit/qc_ghsnap_named.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_ghsnap_named import named_issue

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="unshare needs Linux")


@pytest.mark.e2e  # a real `unshare -cn` namespace: the offline reads have no network (#test-kinds)
def test_named_issue(case: Case) -> None:
    case(named_issue)
