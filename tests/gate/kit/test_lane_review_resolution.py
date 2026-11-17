"""The pytest item of tests/gate/kit/lane_review_resolution.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py). It proves its
criterion, so carries the tag, its source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_review_resolution import resolution

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_review_resolution.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-review-resolution", source=SOURCE)
def test_lane_review_resolution(case: Case) -> None:
    case(resolution)
