"""The pytest items of tests/gate/kit/qc_sandbox.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_sandbox import by_hand, nested, network, refused_host, srt_missing

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
def test_by_hand(case: Case) -> None:
    case(by_hand)


def test_srt_missing(case: Case) -> None:
    case(srt_missing)


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
def test_network(case: Case) -> None:
    case(network)


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
def test_nested(case: Case) -> None:
    case(nested)


@pytest.mark.e2e  # real srt and namespaces (quality spec #test-kinds)
def test_refused_host(case: Case) -> None:
    case(refused_host)
