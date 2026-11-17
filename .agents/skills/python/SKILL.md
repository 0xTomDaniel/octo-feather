---
name: python
description: "Python stack policy for implementer work. Use whenever durable repo signals (pyproject.toml, uv.lock, a `Repo skills: python` line) show a Python project and work touches Python code, packaging, virtual environments, type checking, testing, linting, or command execution."
---

# Python

## When To Use

Use this skill only when the issue body, specs, ADRs, or repository files show
that Python implementation or tooling is in scope. Durable repository signals
include `.py` files, `pyproject.toml`, `requirements*.txt`, `uv.lock`,
`poetry.lock`, `Pipfile`, Python test files, Python CI jobs, or Python-specific
handoff notes.

Do not impose Python conventions on unrelated repositories or issues. Existing
project tooling and validation commands take precedence over defaults here.

## Tooling Defaults

The project's own tooling wins. A project on pip and `requirements*.txt` stays on it: a `.venv` from `pip install -r requirements.txt`, its existing test runner (stdlib `unittest` when it has none), and no `pyproject.toml`, `uv.lock`, formatter or linter it does not already have. The defaults below are for new projects (`templates/python`) and projects already on `uv`.

- Use `uv` for environment management, dependency management, and command execution.
- Prefer `pyproject.toml` as the package and tool configuration surface.
- Use `uv add`, `uv remove`, and `uv sync` instead of editing dependency lists by hand when a managed Python project is in scope.
- Use `uv run` for repo commands so the managed environment stays authoritative.

## Type Safety

- Prefer fully typed code, including function signatures, return types on public interfaces, and structured data models.
- Avoid `Any` except at unavoidable third-party boundaries, and narrow it immediately when you must use it.
- Prefer `Protocol`, `TypedDict`, `dataclass`, or Pydantic-style models over unstructured dictionaries for stable contracts.

## Data At Edges

The rule for data crossing the product's edge: quality spec `#acceptance-edge-validated`. Python practice:

- Use the repo's established schema library. A repo with none adds the one templates spec `#tpl-edge` names, through its own tooling (`uv add pydantic` on `uv`).
- Parse, then validate: `Model.model_validate_json(raw)` for JSON; for another format, its real parser (`tomllib`, a YAML library, `csv`) then `Model.model_validate(parsed)`.
- Edge models extend one base model with `model_config = ConfigDict(strict=True, extra="forbid")`.
- Map the validated model to the domain's types; code past the edge takes typed values, never the parsed `dict`. Output another tool reads is built from a model (`model_dump_json()`).
- No `isinstance` chains or key checks over a parsed `dict` in the library's place, unless the rule's stated reason stands beside them.

## Testing And Quality

- Prefer `pytest` for tests in new projects; otherwise keep the project's own runner.
- Prefer `ruff` for linting and formatting. Never reformat lines a ticket does not change.
- Use `basedpyright` in strict mode for static type checking, as `templates/python` does.
- Use replay-based integration tests when realistic HTTP payloads matter. How a test stands in for what the repo does not own, replays a recording and shares its support: the `tdd` skill's mocking guide (`../tdd/mocking.md`).

## Workflow Notes

- Keep environment setup reproducible in the repo, not in ad hoc shell state.
- Separate linting, formatting, tests, and type checking into explicit commands; the gate's tiers, `just fast` and `just check`, run them (which runs what and when: quality spec `#recipes-table`; the full tier in `templates/python`: ruff check, ruff format, basedpyright, import-linter, pytest), and `just setup` installs the environment.
- If a repo has multiple implementation languages, apply each relevant language policy before making cross-language changes.
