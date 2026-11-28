"""The pytest items of tests/gate/kit/lane_veto.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_veto import veto_files_repair, veto_refused

Case = Callable[..., None]


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-digest-veto", source="tests/gate/kit/lane_veto.py"
)
def test_lane_veto_refused(case: Case) -> None:
    case(veto_refused)


@pytest.mark.criterion(
    "issue-lifecycle#acceptance-merge-digest-veto", source="tests/gate/kit/lane_veto.py"
)
def test_lane_veto_files_repair(case: Case) -> None:
    case(veto_files_repair)
