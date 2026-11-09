"""qc-creds.sh's three planned paths and actual built-state sequence. Legacy remains pending
parity. Public CLI scenarios, no model; fact map: tests/parity/qc-creds/migration-map.md.
"""

from collections.abc import Callable

from qc_creds import built_status_carry, demo_only, incomplete, mixed

Case = Callable[..., None]


def test_qc_creds_demo_only(case: Case) -> None:
    case(demo_only)


def test_qc_creds_mixed(case: Case) -> None:
    case(mixed)


def test_qc_creds_incomplete(case: Case) -> None:
    case(incomplete)


def test_qc_creds_built_status_carry(case: Case) -> None:
    case(built_status_carry)
