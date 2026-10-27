# app

Python app built with the octo-feather kit. Everything it does is reachable through its CLI, `app`, and every command prints JSON with `--json`.

Repo skills: python, verify-app

## Rules

- `just check` is the only gate: lint, types, import boundaries, tests. Agents, the git hook and CI run the same command. A red gate blocks handoff.
- Tests are integration and end-to-end only, through the CLI: `tests/test_cli.py` calls `app.cli.main` in-process and runs `app` as a subprocess. No unit tests of internals, no mocks of our own code. One or two tests per acceptance criterion; keep the suite small.
- No test detail in production code: no test-only flags, env vars, hooks, parameters or branches. Reach the state from the test, mocking at the boundary.
- `app.cli` may import `app.core`; `app.core` never imports `app.cli` (import-linter enforces it).
- Integrate worker commits with `just integrate TICKET REF...` (the kit's `octo-feather-integrate`); keep the recipe.

## Commands

- `just setup` once: `uv sync` and the git hook.
- `just check` the gate: each step and test a pytest item, run in parallel (`GATE_WORKERS` workers; default: justfile `check-tests`), each timed, failures listed at the end, one trend line per run in the octo-feather state dir.
- `just test [PYTEST ARGS]` the same items, a subset: `just test -k check-types`, `just test --lf` reruns the last failures.
- `uv run app hello Ada --json` the app.
