"""The pytest items of tests/gate/kit/qc_eval_verdict.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_eval_verdict import cli_rules, insufficient, same_verdict

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_same_verdict(case: Case) -> None:
    case(same_verdict)


@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_insufficient(case: Case) -> None:
    case(insufficient)


def test_cli_rules(case: Case) -> None:
    case(cli_rules)
