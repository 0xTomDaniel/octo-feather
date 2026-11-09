"""Public QC accounting and native unwritable-ledger scenarios; legacy retained.

No cost exemption. Gross matched CPU and actual source-safe parity remain owed.
"""

from collections.abc import Callable

from spend_ledger_qc import accounting, unwritable

Case = Callable[..., None]


def test_spend_ledger_qc_accounting(case: Case) -> None:
    case(accounting)


def test_spend_ledger_qc_unwritable(case: Case) -> None:
    case(unwritable)
