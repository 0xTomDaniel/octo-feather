# app

Small TypeScript app on Node.js (an eval fixture of the octo-feather kit). Everything it does is reachable through its CLI, `app`; every command prints JSON with `--json`.

Repo skills: typescript, nodejs, pnpm

## Rules

- Tests are integration and end-to-end only, through the CLI: `tests/cli.test.ts` runs `src/cli.ts` as a subprocess.
- `src/cli.ts` may import `src/core.ts`; `src/core.ts` never imports `src/cli.ts`.

## Commands

- `pnpm install` the dependencies. This box has no package registry: pnpm installs offline from its local store (`.npmrc`).
- `pnpm test` the tests; `pnpm typecheck` the compiler.
- `pnpm app hello Ada --json` the app.
