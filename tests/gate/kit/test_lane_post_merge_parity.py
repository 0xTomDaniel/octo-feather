"""The pytest items of tests/gate/kit/lane_post_merge_parity.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

import pytest
from lane_post_merge_parity import capped, due, network_free, told

Case = Callable[..., None]


@pytest.mark.criterion("quality#acceptance-parity-pass-due")
def test_post_merge_starts_the_due_pass(case: Case) -> None:
    case(due)


@pytest.mark.criterion("quality#acceptance-parity-pass-capped")
def test_post_merge_pass_capped(case: Case) -> None:
    case(capped)


@pytest.mark.criterion("quality#acceptance-parity-pass-told")
def test_post_merge_pass_told(case: Case) -> None:
    case(told)


@pytest.mark.criterion("quality#acceptance-parity-network-free")
def test_post_merge_pass_network_free(case: Case) -> None:
    case(network_free)
