"""The pytest item of tests/gate/kit/lane_merge_declaration.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py), tagged with the
criterion it proves, its source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_declaration import tier_declaration

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_merge_declaration.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-tier-declaration", source=SOURCE)
def test_merge_tier_declaration(case: Case) -> None:
    case(tier_declaration)
