# app

Python app built with the octo-feather kit. Everything it does is reachable through its CLI, `app`, and every command prints JSON with `--json`.

Repo skills: python

## Rules

- `just check` is the only gate: lint, types, import boundaries, tests. Agents, the git hook and CI run the same command. A red gate blocks handoff.
- Tests are integration and end-to-end only, through the CLI: `tests/test_cli.py` calls `app.cli.main` in-process and runs `app` as a subprocess. No unit tests of internals, no mocks of our own code.
- `app.cli` may import `app.core`; `app.core` never imports `app.cli` (import-linter enforces it).
- Integrate worker commits with `just integrate N REF...` (the kit's `octo-feather-integrate`).

## Commands

- `just setup` once: `uv sync` and the git hook.
- `just check` the gate.
- `uv run app hello Ada --json` the app.
