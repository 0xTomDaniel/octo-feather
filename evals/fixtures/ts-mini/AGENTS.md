# app

Small TypeScript app on Node.js (an eval fixture of the octo-feather kit). Everything it does is reachable through its CLI, `app`, and its HTTP server; every CLI command prints JSON with `--json`.

Repo skills: typescript, nodejs, pnpm

## Rules

- Tests are integration and end-to-end only, through the CLI and HTTP: `tests/cli.test.ts` runs `src/cli.ts` as a subprocess.
- `src/cli.ts` and `src/server.ts` may import `src/core.ts`; `src/core.ts` imports neither.

## Commands

- `pnpm install` the dependencies.
- `pnpm test` the tests; `pnpm typecheck` the compiler.
- `pnpm app hello Ada --json` the app; `pnpm serve` the server.
