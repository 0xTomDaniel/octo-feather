"""The pytest item of tests/gate/kit/lane_merge_ask_hunks.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py), tagged with
the criterion it proves, its source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_ask_hunks import one_head_hunks

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-one-head-hunks", source="tests/gate/kit/lane_merge_ask_hunks.py"
)
def test_merge_ask_one_head_hunks(case: Case) -> None:
    case(one_head_hunks)
