# app

Python app built with the octo-feather kit. Everything it does is reachable through its CLI, `app`, and every command prints JSON with `--json`.

Repo skills: python

## Rules

- The gate has two tiers, `just fast` and `just check`: who runs which, octo-feather templates spec #tpl-gate, #tpl-hooks. A red gate blocks handoff.
- Tests are integration and end-to-end only, through the CLI: `tests/test_cli.py` calls `app.cli.main` in-process and runs `app` as a subprocess. No unit tests of internals, no mocks of our own code. One or two tests per acceptance criterion; keep the suite small.
- No test detail in production code: no test-only flags, env vars, hooks, parameters or branches. Reach the state from the test, mocking at the boundary.
- `app.cli` may import `app.core`; `app.core` never imports `app.cli` (import-linter enforces it).
- Integrate worker commits with `just integrate TICKET REF...` (the kit's `octo-feather-integrate`); keep the recipe.

## Commands

- `just setup` once: `uv sync`.
- `just fast` and `just check` the gate's tiers.
- `uv run app hello Ada --json` the app.
