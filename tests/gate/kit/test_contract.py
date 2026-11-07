"""The pytest items of tests/gate/kit/contract.py's scenarios (what they prove: its docstring),
each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from contract import ts_drive, variants

Case = Callable[..., None]


def test_contract_variants(case: Case) -> None:
    case(variants)


def test_contract_ts_drive(case: Case) -> None:
    case(ts_drive)
