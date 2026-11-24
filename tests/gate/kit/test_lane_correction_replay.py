"""The pytest items of tests/gate/kit/lane_correction_replay.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). They
prove their criterion, so carry its tag, their source that file (quality #qc-capture). Those
running rows start the real qc sandbox, so are e2e (quality spec #test-kinds)."""

import sys
from collections.abc import Callable

import pytest
from lane_correction_replay import contained, masked, missing, read, recorded_1233, shown, untrue

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_correction_replay.py"
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-missing", source=SOURCE)
def test_correction_replay_missing(case: Case) -> None:
    case(missing)


@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-missing", source=SOURCE)
def test_correction_replay_read(case: Case) -> None:
    case(read)


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


@pytest.mark.e2e
@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-shown", source=SOURCE)
def test_correction_replay_masked(case: Case) -> None:
    case(masked)


@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-missing", source=SOURCE)
@pytest.mark.criterion("issue-lifecycle#acceptance-correction-replay-shown", source=SOURCE)
def test_correction_replay_recorded_1233(case: Case) -> None:
    case(recorded_1233)
