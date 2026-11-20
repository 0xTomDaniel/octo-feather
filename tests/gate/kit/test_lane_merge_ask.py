"""The pytest items of tests/gate/kit/lane_merge_ask.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py). The
items proving a criterion carry its tag, their source that file (quality #qc-capture)."""

from collections.abc import Callable

import pytest
from lane_merge_ask import (
    ci_status_only,
    criterion_claimed,
    current_head_checks,
    current_head_identity,
    failed_triage,
    fields,
    full_pass,
    gate_time,
    judged_rows,
    main_merges,
    many_commits,
    merge_ask_passes,
    no_ci,
    no_criterion_lane,
    offline_gh,
    one_judged_head,
    review_link,
    rows_and_built,
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


def test_merge_ask_failed_triage(case: Case) -> None:
    case(failed_triage)


def test_merge_ask_single_gaps(case: Case) -> None:
    case(single_gaps)


def test_merge_ask_no_ci(case: Case) -> None:
    case(no_ci)


@pytest.mark.criterion("issue-lifecycle#acceptance-ci-status-only", source=SOURCE)
def test_merge_ask_ci_status_only(case: Case) -> None:
    case(ci_status_only)


@pytest.mark.criterion("issue-lifecycle#acceptance-ci-status-only", source=SOURCE)
def test_merge_ask_current_head_checks(case: Case) -> None:
    case(current_head_checks)


@pytest.mark.criterion("issue-lifecycle#acceptance-ci-status-only", source=SOURCE)
def test_merge_ask_current_head_identity(case: Case) -> None:
    case(current_head_identity)


def test_merge_ask_rows_and_built(case: Case) -> None:
    case(rows_and_built)


def test_merge_ask_review_link(case: Case) -> None:
    case(review_link)


def test_merge_ask_one_judged_head(case: Case) -> None:
    case(one_judged_head)


def test_merge_ask_main_merges(case: Case) -> None:
    case(main_merges)


@pytest.mark.criterion("issue-lifecycle#acceptance-merge-ask-full-proof", source=SOURCE)
def test_merge_ask_full_pass(case: Case) -> None:
    case(full_pass)


def test_merge_ask_judged_rows(case: Case) -> None:
    case(judged_rows)


def test_merge_ask_usage_failures(case: Case) -> None:
    case(usage_failures)


def test_merge_ask_no_criterion_lane(case: Case) -> None:
    case(no_criterion_lane)


def test_merge_ask_criterion_claimed(case: Case) -> None:
    case(criterion_claimed)


def test_merge_ask_many_commits(case: Case) -> None:
    case(many_commits)


def test_fields(case: Case) -> None:
    case(fields)
