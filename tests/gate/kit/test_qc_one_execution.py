"""The pytest items of tests/gate/kit/qc_one_execution.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_one_execution import (
    artifacts_missing,
    capture,
    claims_refused,
    ids_refused,
    judged_from_records,
    metadata_only,
    partial,
    plain_gate,
    strict,
    two_specs,
)

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_claims_refused(case: Case) -> None:
    case(claims_refused)


def test_capture(case: Case) -> None:
    case(capture)


def test_judged_from_records(case: Case) -> None:
    case(judged_from_records)


def test_plain_gate(case: Case) -> None:
    case(plain_gate)


def test_strict(case: Case) -> None:
    case(strict)


def test_partial(case: Case) -> None:
    case(partial)


def test_metadata_only(case: Case) -> None:
    case(metadata_only)


def test_artifacts_missing(case: Case) -> None:
    case(artifacts_missing)


@pytest.mark.criterion("issue-lifecycle#acceptance-qc-interim", "quality#acceptance-one-execution")
def test_two_specs(case: Case) -> None:
    case(two_specs)


@pytest.mark.criterion("issue-lifecycle#acceptance-qc-interim")
def test_ids_refused(case: Case) -> None:
    case(ids_refused)
