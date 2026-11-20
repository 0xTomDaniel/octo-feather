"""The pytest items of tests/gate/kit/lane_tickets.py's scenarios (what they prove: its
docstring), each run as that file's command through `case` (tests/gate/kit/conftest.py)."""

from collections.abc import Callable

from lane_tickets import (
    comment_overrides,
    creates,
    drafts,
    errors,
    just_demos,
    just_recipes,
    linear,
    mcp_demos,
    rules,
    scopes,
    scripts,
    skills_lines,
    tickets_github,
    transition,
)

Case = Callable[..., None]


def test_tickets_github(case: Case) -> None:
    case(tickets_github)


def test_drafts(case: Case) -> None:
    case(drafts)


def test_rules(case: Case) -> None:
    case(rules)


def test_scripts(case: Case) -> None:
    case(scripts)


def test_just_recipes(case: Case) -> None:
    case(just_recipes)


def test_scopes(case: Case) -> None:
    case(scopes)


def test_creates(case: Case) -> None:
    case(creates)


def test_just_demos(case: Case) -> None:
    case(just_demos)


def test_errors(case: Case) -> None:
    case(errors)


def test_linear(case: Case) -> None:
    case(linear)


def test_mcp_demos(case: Case) -> None:
    case(mcp_demos)


def test_skills_lines(case: Case) -> None:
    case(skills_lines)


def test_transition(case: Case) -> None:
    case(transition)


def test_comment_overrides(case: Case) -> None:
    case(comment_overrides)
