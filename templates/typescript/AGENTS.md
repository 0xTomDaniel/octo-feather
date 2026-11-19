# app

TypeScript app built with the octo-feather kit. Node runs `src/*.ts` directly (type stripping, no build step). Everything the app does is reachable through its CLI, `app` (`src/cli.ts`), and every command prints JSON with `--json`.

Repo skills: typescript, pnpm, nodejs, verify-app

## Rules

- The gate has two tiers, `just fast` and `just check`: who runs which, octo-feather templates spec #tpl-gate, #tpl-hooks (each runs tsc strictest, typescript-eslint strict-type-checked, dependency-cruiser and knip: GATE_RECIPES in the `justfile`). The one a hand-off needs green: octo-feather quality spec #acceptance-gate-green; when a lane runs the full tier: octo-feather issue-lifecycle spec #lanes-checkpoints.
- Tests are integration and end-to-end only, each kind as octo-feather quality spec #test-kinds says (octo-feather templates spec #templates-tests-rule, #tpl-tests): integration `tests/*.test.ts`, end-to-end `tests/*.e2e.test.ts`, each kind a Vitest project (`vitest.config.ts`); shared read-only fixtures as `tests/shared-fixture.ts` (#acceptance-shared-fixture). What a test may stand in for, recordings and shared test support: the octo-feather `tdd` skill's mocking guide (`mocking.md`). One or two tests per acceptance criterion; keep the suite small. A criterion's acceptance test is a test tagged with it, which `just qc` judges it from (the verify-app skill, Acceptance).
- No test detail in production code: no test-only flags, env vars, hooks, parameters or branches. Reach the state from the test, mocking at the boundary.
- Data at the app's edges: octo-feather quality spec #acceptance-edge-validated, with Zod 4 `z.strictObject` (octo-feather templates spec #tpl-edge). Example: `app hello --request` (`src/cli.ts`).
- `src/core.ts` never imports `src/cli.ts` (dependency-cruiser enforces it).
- Only erasable TypeScript syntax (no enums, namespaces or parameter properties); `tsc` enforces it.
- Shell is for thin glue: calling commands, environment setup, mounts. Logic, parsing and rules go in TypeScript.
- Infrastructure (what counts, what fits, and the `Prior art:` line that reports the choice: the `code-review` skill, Verdict step, **Prior art**) comes from Node's built-ins, a popular, well-maintained library pinned with `pnpm add`, or the real tool. A broken library is patched in place (`pnpm patch`, its patch file committed), never replaced with a hand-written one. Hand-writing one needs its reason stated where it lives (a comment, the spec). Example: TOML is read with smol-toml (`parse`); a hand-written `toml.ts` is the failure.
- Integrate worker commits with `just integrate TICKET REF...` (the kit's `octo-feather-integrate`); keep the recipe.

## Layout

- `src/` the app; CLI entry, runtime requirements and dependency declarations: `package.json`. Dependency pins: `pnpm-lock.yaml`.
- `tests/` integration and E2E tests; gate recipes and setup: `justfile`, listed by `just --list`. `tests/trend-reporter.ts` appends one trend line per Vitest run, `tests/qc-capture.ts` is the qc capture's side of the gate and `tests/qc-tags.ts` its collector of tagged tests (each head says what); `gate-budget.toml` the gate-time budget (its head says what reads it). `shared-machinery.txt` the shared-machinery list (what it schedules: its header).
