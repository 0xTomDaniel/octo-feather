"""The pytest items of tests/gate/kit/lane_digest.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_digest import digest_lists_the_day

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-digest", source="tests/gate/kit/lane_digest.py"
)
def test_lane_digest_lists_the_day(case: Case) -> None:
    case(digest_lists_the_day)
