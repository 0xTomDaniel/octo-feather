"""The pytest items of tests/gate/kit/lane_correction_replay.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). They
prove their criterion, so carry its tag, their source that file (quality #qc-capture). Those
running rows start the real qc sandbox, so are e2e (quality spec #test-kinds)."""

import sys
from collections.abc import Callable

import pytest
from lane_correction_replay import contained, missing, shown, untrue

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_correction_replay.py"
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-missing", source=SOURCE)
def test_correction_replay_missing(case: Case) -> None:
    case(missing)


@pytest.mark.e2e
@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-shown", source=SOURCE)
def test_correction_replay_shown(case: Case) -> None:
    case(shown)


@pytest.mark.e2e
@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-shown", source=SOURCE)
def test_correction_replay_untrue(case: Case) -> None:
    case(untrue)


@pytest.mark.e2e
@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-missing", source=SOURCE)
@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-shown", source=SOURCE)
def test_correction_replay_contained(case: Case) -> None:
    case(contained)
