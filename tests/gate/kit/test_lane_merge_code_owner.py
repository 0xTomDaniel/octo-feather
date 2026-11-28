"""The pytest items of tests/gate/kit/lane_merge_code_owner.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). The item
proving the criterion carries its tag, its source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_code_owner import dropped_line, owner_path, real_file, refused

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_merge_code_owner.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-code-owner", source=SOURCE)
def test_merge_tier_code_owner(case: Case) -> None:
    case(owner_path)


def test_merge_tier_code_owner_real_file(case: Case) -> None:
    case(real_file)


def test_merge_tier_code_owner_refused(case: Case) -> None:
    case(refused)


def test_merge_tier_code_owner_dropped_line(case: Case) -> None:
    case(dropped_line)
