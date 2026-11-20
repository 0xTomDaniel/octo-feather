"""The pytest items of tests/gate/kit/lane_merge_ask.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). The
items proving a criterion carry its tag, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_ask import (
    ci_status_only,
    current_head_checks,
    current_head_identity,
    fields,
    full_pass,
    gate_time,
    main_merges,
    many_commits,
    merge_ask_passes,
    no_ci,
    no_ci_unread,
    no_criterion_lane,
    offline_gh,
    one_judged_head,
    single_gaps,
    usage_failures,
    verdict_posts,
    verdict_reader_scope,
    verdict_refusals,
    verdict_write_fails,
)

Case = Callable[..., None]
SOURCE = "tests/gate/kit/lane_merge_ask.py"


def test_verdict_posts(case: Case) -> None:
    case(verdict_posts)


def test_verdict_reader_scope(case: Case) -> None:
    case(verdict_reader_scope)


def test_verdict_refusals(case: Case) -> None:
    case(verdict_refusals)


def test_verdict_write_fails(case: Case) -> None:
    case(verdict_write_fails)


def test_merge_ask_offline_gh(case: Case) -> None:
    case(offline_gh)


def test_merge_ask_passes(case: Case) -> None:
    case(merge_ask_passes)


def test_merge_ask_gate_time(case: Case) -> None:
    case(gate_time)


def test_merge_ask_single_gaps(case: Case) -> None:
    case(single_gaps)


def test_merge_ask_no_ci(case: Case) -> None:
    case(no_ci)


def test_merge_ask_no_ci_unread(case: Case) -> None:
    case(no_ci_unread)


@pytest.mark.criterion("issue-lifecycle#acceptance-ci-status-only", source=SOURCE)
def test_merge_ask_ci_status_only(case: Case) -> None:
    case(ci_status_only)


@pytest.mark.criterion("issue-lifecycle#acceptance-ci-status-only", source=SOURCE)
def test_merge_ask_current_head_checks(case: Case) -> None:
    case(current_head_checks)


@pytest.mark.criterion("issue-lifecycle#acceptance-ci-status-only", source=SOURCE)
def test_merge_ask_current_head_identity(case: Case) -> None:
    case(current_head_identity)


def test_merge_ask_one_judged_head(case: Case) -> None:
    case(one_judged_head)


def test_merge_ask_main_merges(case: Case) -> None:
    case(main_merges)


@pytest.mark.criterion("issue-lifecycle#acceptance-merge-ask-full-proof", source=SOURCE)
def test_merge_ask_full_pass(case: Case) -> None:
    case(full_pass)


def test_merge_ask_usage_failures(case: Case) -> None:
    case(usage_failures)


def test_merge_ask_no_criterion_lane(case: Case) -> None:
    case(no_criterion_lane)


def test_merge_ask_many_commits(case: Case) -> None:
    case(many_commits)


def test_fields(case: Case) -> None:
    case(fields)
