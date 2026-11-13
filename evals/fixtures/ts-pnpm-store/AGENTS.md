# relay

Small TypeScript service on Node.js (an eval fixture of the octo-feather kit). It reads its settings from `relay.json` and forwards each message it receives to the configured endpoint.

Repo skills: typescript, nodejs, pnpm

## Rules

- `just check` is the only gate: the compiler and the Node test runner. Agents, the git hook and CI run the same command.
- Tests are integration and end-to-end only: they drive `src/main.ts` or a real recipe in a subprocess. No mocks of our own code.
- A test that spawns a process registers it with `reaped` (test/reap.ts), so a failed run leaves nothing behind.
- How dependencies are installed: docs/pnpm-setup.md (`just setup-dependencies`).

## Commands

- `just setup` once: dependencies and the git hook.
- `just check` the gate.
- `pnpm relay --config relay.json` the service.
