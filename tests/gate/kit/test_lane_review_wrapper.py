"""The pytest items of tests/gate/kit/lane_review_wrapper.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). Each
proves its criterion, so carries the tag, its source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_review_wrapper import wrapper_clean, wrapper_refused, wrapper_resolved

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_review_wrapper.py"


@pytest.mark.criterion("issue-lifecycle#acceptance-review-wrapper-clean", source=SOURCE)
def test_review_wrapper_clean(case: Case) -> None:
    case(wrapper_clean)


@pytest.mark.criterion("issue-lifecycle#acceptance-review-wrapper-resolved", source=SOURCE)
def test_review_wrapper_resolved(case: Case) -> None:
    case(wrapper_resolved)


@pytest.mark.criterion("issue-lifecycle#acceptance-review-wrapper-refused", source=SOURCE)
def test_review_wrapper_refused(case: Case) -> None:
    case(wrapper_refused)
