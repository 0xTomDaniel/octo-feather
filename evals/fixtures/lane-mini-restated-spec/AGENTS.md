# app

Small Python app (an eval fixture of the octo-feather kit: a target repo with a spec, a lane's notes and diffs under review). Everything it does is reachable through its CLI, `app`, and every command prints JSON with `--json`.

Repo skills: python

## Rules

- Tests are integration and end-to-end only, through the CLI: `tests/test_cli.py` calls `app.cli.main` in-process and runs `app` as a subprocess.
- `app.cli` may import `app.core`; `app.core` never imports `app.cli`.
- Greeting text lives only in `app.core`; `app.cli` parses arguments and prints, nothing else.
- `just check` is the gate: a red gate blocks handoff.

## Layout

- `docs/specs/usage.spec.html` the CLI's usage page.
- `docs/specs/greet.spec.html` the accepted spec; `docs/specs/greet.status.json` its per-criterion status.
- `notes/` this lane's notes: `lane.toml` (a copy of the lane record), `handoffs.jsonl`, `tickets.md`.
- `review/` diffs waiting for code review.

## Commands

- `just check` the gate (ruff, pytest).
- `uv run pytest -q` the tests.
- `uv run app hello Ada --json` the app.
