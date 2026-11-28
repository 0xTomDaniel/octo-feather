"""The pytest items of tests/gate/kit/parity_lever.py's scenarios (what each proves: its
docstrings), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from parity_lever import needs_as_git_holds, network_unreached

Case = Callable[..., None]


def test_needs_as_git_holds(case: Case) -> None:
    case(needs_as_git_holds)


@pytest.mark.criterion("quality#acceptance-parity-network-free")
def test_network_unreached(case: Case) -> None:
    case(network_unreached)
