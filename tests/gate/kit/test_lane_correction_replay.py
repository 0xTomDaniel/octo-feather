"""The pytest items of tests/gate/kit/lane_correction_replay.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). They
prove their criterion, so carry its tag, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_correction_replay import missing, shown, untrue

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_correction_replay.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-missing", source=SOURCE)
def test_correction_replay_missing(case: Case) -> None:
    case(missing)


@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-shown", source=SOURCE)
def test_correction_replay_shown(case: Case) -> None:
    case(shown)


@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-shown", source=SOURCE)
def test_correction_replay_untrue(case: Case) -> None:
    case(untrue)
