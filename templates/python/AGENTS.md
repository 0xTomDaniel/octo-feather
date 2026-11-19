# app

Python app built with the octo-feather kit. Everything it does is reachable through its CLI, `app`, and every command prints JSON with `--json`.

Repo skills: python, verify-app

## Rules

- The gate has two tiers, `just fast` and `just check`: who runs which, octo-feather templates spec #tpl-gate, #tpl-hooks. The one a hand-off needs green: octo-feather quality spec #acceptance-gate-green; when a lane runs the full tier: octo-feather issue-lifecycle spec #lanes-checkpoints.
- Tests are integration and end-to-end only, each kind as octo-feather quality spec #test-kinds says (octo-feather templates spec #templates-tests-rule, #tpl-tests): integration in `tests/integration/` (`app.cli.main` in-process), end-to-end in `tests/e2e/` (the `app` command as a process; its conftest.py marks each `e2e`); shared read-only fixtures as `tests/integration/conftest.py` (#acceptance-shared-fixture). What a test may stand in for, recordings and shared test support: the octo-feather `tdd` skill's mocking guide (`mocking.md`). One or two tests per acceptance criterion; keep the suite small. A criterion's acceptance test is a test marked with it (`criterion`), which `just qc` judges it from (the verify-app skill, Acceptance).
- No test detail in production code: no test-only flags, env vars, hooks, parameters or branches. Reach the state from the test, mocking at the boundary.
- Data at the app's edges: octo-feather quality spec #acceptance-edge-validated, with Pydantic v2 (octo-feather templates spec #tpl-edge). Example: `app hello --request` (`src/app/cli.py`).
- `app.cli` may import `app.core`; `app.core` never imports `app.cli` (import-linter enforces it).
- Shell is for thin glue: calling commands, environment setup, mounts. Logic, parsing and rules go in Python.
- Infrastructure (what counts, what fits, and the `Prior art:` line that reports the choice: the `code-review` skill, Verdict step, **Prior art**) comes from the standard library, a popular, well-maintained library pinned with `uv add`, or the real tool. A broken library is patched in place (a committed patch file, or a pinned fork in `[tool.uv.sources]`), never replaced with a hand-written one. Hand-writing one needs its reason stated where it lives (a comment, the spec). Example: YAML input is read with PyYAML (`yaml.safe_load`), TOML with `tomllib`; a hand-written line splitter for either is the failure.
- Integrate worker commits with `just integrate TICKET REF...` (the kit's `octo-feather-integrate`); keep the recipe.

## Layout

- `src/app/` the app package; CLI entry and dependency declarations: `pyproject.toml`. Dependency pins: `uv.lock`.
- `tests/` integration and E2E tests; gate recipes and setup: `justfile`, listed by `just --list`. `shared-machinery.txt` the shared-machinery list (what it schedules: its header). `tests/conftest.py` appends one trend line per pytest run and holds the qc capture's side of the gate (its docstring says what); `gate-budget.toml` the gate-time budget (its head says what reads it).
