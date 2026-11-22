"""The pytest items of tests/gate/kit/lane_verdict_rounds.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). They
prove their criteria, so carry their tags, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_verdict_rounds import (
    covers_lane,
    declaration_shown,
    declaration_verdict,
    legacy,
    range_refusals,
)

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_verdict_rounds.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-verdict-covers-lane", source=SOURCE)
def test_verdict_covers_lane(case: Case) -> None:
    case(covers_lane)


@pytest.mark.criterion("issue-lifecycle#acceptance-verdict-covers-lane", source=SOURCE)
def test_verdict_range_refusals(case: Case) -> None:
    case(range_refusals)


@pytest.mark.criterion("issue-lifecycle#acceptance-verdict-covers-lane", source=SOURCE)
def test_verdict_legacy_comment(case: Case) -> None:
    case(legacy)


@pytest.mark.criterion("issue-lifecycle#acceptance-declaration-check-shown", source=SOURCE)
def test_declaration_check_shown(case: Case) -> None:
    case(declaration_shown)


@pytest.mark.criterion("issue-lifecycle#acceptance-declaration-check-shown", source=SOURCE)
def test_declaration_check_verdict(case: Case) -> None:
    case(declaration_verdict)
