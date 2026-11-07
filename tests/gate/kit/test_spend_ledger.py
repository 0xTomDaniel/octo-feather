"""The pytest items of tests/gate/kit/spend_ledger.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from spend_ledger import agents, later

Case = Callable[..., None]


def test_spend_ledger_agents(case: Case) -> None:
    case(agents)


def test_spend_ledger_later(case: Case) -> None:
    case(later)
