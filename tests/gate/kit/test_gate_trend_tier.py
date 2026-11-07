"""The pytest item of tests/gate/kit/gate_trend_tier.py's scenario (what it proves: its
docstring), run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from gate_trend_tier import tier

Case = Callable[..., None]


def test_gate_trend_tier(case: Case) -> None:
    case(tier)
