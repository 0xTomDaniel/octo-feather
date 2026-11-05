# app

Small Python app (an eval fixture of the octo-feather kit: diffs waiting for code review). Everything it does is reachable through its CLI, `app`, and every command prints JSON with `--json`.

Repo skills: python

## Rules

- Tests are integration and end-to-end only, through the CLI: `tests/test_cli.py` calls `app.cli.main` in-process and runs `app` as a subprocess.
- `app.cli` may import `app.core`; `app.core` never imports `app.cli`.

## Layout

- `review/` diffs waiting for code review, each against this tree.

## Commands

- `uv run pytest -q` the tests.
- `uv run app hello Ada --json` the app.
