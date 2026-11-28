"""The pytest items of tests/gate/kit/qa_pinned_opens.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from qa_pinned_opens import mismatch, no_record, opened, ran_mismatch

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_no_record(case: Case) -> None:
    case(no_record)


@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_opened(case: Case) -> None:
    case(opened)


@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_mismatch(case: Case) -> None:
    case(mismatch)


@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_ran_mismatch(case: Case) -> None:
    case(ran_mismatch)
