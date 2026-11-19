"""The pytest items of tests/gate/kit/qc_gh.py's scenarios (what they prove: its docstring), each
run as that file's command through `case` (tests/gate/kit/conftest.py)."""

import sys
from collections.abc import Callable

import pytest
from qc_gh import (
    diff_too_large,
    fetch_fails,
    killed,
    kit_on_kit,
    no_github,
    refused_args,
    snapshot_misses,
    snapshot_read,
    snapshot_read_only,
    status_commit_fails,
    status_commit_owner,
)

Case = Callable[..., None]
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")


def test_refused_args(case: Case) -> None:
    case(refused_args)


@pytest.mark.e2e  # the real qc sandbox runs (quality spec #test-kinds)
def test_snapshot_read(case: Case) -> None:
    case(snapshot_read)


@pytest.mark.e2e
def test_snapshot_read_only(case: Case) -> None:
    case(snapshot_read_only)


@pytest.mark.e2e  # the real qc sandbox runs (quality spec #test-kinds)
def test_killed(case: Case) -> None:
    case(killed)


def test_fetch_fails(case: Case) -> None:
    case(fetch_fails)


@pytest.mark.e2e  # the real qc sandbox runs (quality spec #test-kinds)
def test_no_github(case: Case) -> None:
    case(no_github)


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
