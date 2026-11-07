"""The pytest item of tests/gate/kit/lane_ci_start.py's scenarios (what they prove: its docstring),
all run as that file's command, one item (testkit.together), through `case`
(tests/gate/kit/conftest.py). It proves its criterion, so carries the tag, its source that file
(quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_ci_start import LANE_CI_START

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_ci_start.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-ci-alongside", source=SOURCE)
def test_lane_ci_start(case: Case) -> None:
    case(LANE_CI_START)
