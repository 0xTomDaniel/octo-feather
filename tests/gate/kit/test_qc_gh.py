"""The pytest items of tests/gate/kit/qc_gh.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_gh import (
    diff_too_large,
    kit_on_kit,
    notes_query,
    refused_args,
    snapshot_misses,
    status_commit_fails,
    status_commit_owner,
)

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


@pytest.mark.e2e  # a real `unshare -cn` namespace (qc_gh.qc; quality spec #test-kinds)
def test_refused_args(case: Case) -> None:
    case(refused_args)


@pytest.mark.e2e  # the real qc sandbox runs (quality spec #test-kinds)
def test_status_commit_fails(case: Case) -> None:
    case(status_commit_fails)


@pytest.mark.e2e  # the real qc sandbox runs (quality spec #test-kinds)
def test_status_commit_owner(case: Case) -> None:
    case(status_commit_owner)


def test_snapshot_misses(case: Case) -> None:
    case(snapshot_misses)


def test_diff_too_large(case: Case) -> None:
    case(diff_too_large)


@pytest.mark.e2e  # the real qc sandbox runs (quality spec #test-kinds)
def test_kit_on_kit(case: Case) -> None:
    case(kit_on_kit)


def test_notes_query(case: Case) -> None:
    case(notes_query)
