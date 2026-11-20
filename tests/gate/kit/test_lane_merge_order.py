"""The pytest item of tests/gate/kit/lane_merge_order.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py), tagged with
the criterion it proves, its source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_order import siblings

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-ask-siblings", source="tests/gate/kit/lane_merge_order.py"
)
def test_merge_ask_siblings(case: Case) -> None:
    case(siblings)
