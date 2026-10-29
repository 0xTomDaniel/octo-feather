# app

TypeScript app built with the octo-feather kit. Node runs `src/*.ts` directly (type stripping, no build step). Everything the app does is reachable through its CLI, `app` (`src/cli.ts`), and every command prints JSON with `--json`.

Repo skills: typescript, pnpm, nodejs, verify-app

## Rules

- `just check` is the only gate: tsc strictest, typescript-eslint strict-type-checked, dependency-cruiser, knip, Vitest. Agents, the git hook and CI run the same command. A red gate blocks handoff.
- Tests are integration and end-to-end only, through the CLI: `tests/cli.test.ts` calls `main` in-process and runs `src/cli.ts` as a process. No unit tests of internals, no mocks of our own code. One or two tests per acceptance criterion; keep the suite small.
- No test detail in production code: no test-only flags, env vars, hooks, parameters or branches. Reach the state from the test, mocking at the boundary.
- `src/core.ts` never imports `src/cli.ts` (dependency-cruiser enforces it).
- Only erasable TypeScript syntax (no enums, namespaces or parameter properties); `tsc` enforces it.
- Shell is for thin glue: calling commands, environment setup, mounts. Logic, parsing and rules go in TypeScript.
- Infrastructure (a parser, test runner, protocol, file format, scheduler) comes from Node's built-ins, a popular, well-maintained library pinned with `pnpm add`, or the real tool; the implementer's `Prior art:` line reports the choice. A broken library is patched in place (`pnpm patch`, its patch file committed), never replaced with a hand-written one. Hand-writing one needs its reason stated where it lives (a comment, the spec). Example: TOML is read with smol-toml (`parse`); a hand-written `toml.ts` is the failure.
- Integrate worker commits with `just integrate TICKET REF...` (the kit's `octo-feather-integrate`); keep the recipe.

## Layout

- `src/` the app; CLI entry, runtime requirements and dependency declarations: `package.json`. Dependency pins: `pnpm-lock.yaml`.
- `tests/` integration and E2E tests; gate recipes and setup: `justfile`, listed by `just --list`. `just check` is the gate.
