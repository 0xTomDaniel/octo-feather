"""The pytest items of tests/gate/kit/qc_open_record.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_open_record import not_whole, whole

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_whole(case: Case) -> None:
    case(whole)


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_not_whole(case: Case) -> None:
    case(not_whole)
