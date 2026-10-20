# app

TypeScript app built with the octo-feather kit. Node runs `src/*.ts` directly (type stripping, no build step). Everything the app does is reachable through its CLI, `app` (`src/cli.ts`), and every command prints JSON with `--json`.

Repo skills: typescript, pnpm, nodejs

## Rules

- `just check` is the only gate: tsc strictest, typescript-eslint strict-type-checked, dependency-cruiser, knip, Vitest. Agents, the git hook and CI run the same command. A red gate blocks handoff.
- Tests are integration and end-to-end only, through the CLI: `tests/cli.test.ts` calls `main` in-process and runs `src/cli.ts` as a process. No unit tests of internals, no mocks of our own code. One or two tests per acceptance criterion; keep the suite small.
- No test detail in production code: no test-only flags, env vars, hooks, parameters or branches. Reach the state from the test, mocking at the boundary.
- `src/core.ts` never imports `src/cli.ts` (dependency-cruiser enforces it).
- Only erasable TypeScript syntax (no enums, namespaces or parameter properties); `tsc` enforces it.
- Integrate worker commits with `just integrate N REF...` (the kit's `octo-feather-integrate`); keep the recipe, every octo-feather target must define it.

## Commands

- `just setup` once: `pnpm install` and the git hook.
- `just check` the gate.
- `node src/cli.ts hello Ada --json` the app.
