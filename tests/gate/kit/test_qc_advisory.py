"""The pytest items of tests/gate/kit/qc_advisory.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_advisory import does_not_show, no_pi, node_shim, shows, unavailable

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_does_not_show(case: Case) -> None:
    case(does_not_show)


def test_shows(case: Case) -> None:
    case(shows)


def test_unavailable(case: Case) -> None:
    case(unavailable)


def test_node_shim(case: Case) -> None:
    case(node_shim)


@pytest.mark.parametrize("how", ["nopi", "loop"])
def test_no_pi(case: Case, how: str) -> None:
    case(no_pi, how)
