"""The pytest items of tests/gate/kit/lane_digest.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_digest import digest_lists_the_day, due_from_merge, due_until_sent

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-digest", source="tests/gate/kit/lane_digest.py"
)
def test_lane_digest_lists_the_day(case: Case) -> None:
    case(digest_lists_the_day)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-digest", source="tests/gate/kit/lane_digest.py"
)
def test_lane_digest_due_from_merge(case: Case) -> None:
    case(due_from_merge)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-digest", source="tests/gate/kit/lane_digest.py"
)
def test_lane_digest_due_until_sent(case: Case) -> None:
    case(due_until_sent)
