"""The pytest items of tests/gate/kit/qa_evidence.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from qa_evidence import block, usage

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-qa-evidence-block")
def test_block(case: Case) -> None:
    case(block)


def test_usage(case: Case) -> None:
    case(usage)
