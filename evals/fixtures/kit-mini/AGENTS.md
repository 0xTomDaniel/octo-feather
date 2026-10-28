# octo-feather (mini)

Agentic development kit: published commands in `scripts/`, each a short-lived CLI an owner or agent runs, and `just` recipes over them.

Repo skills: verify-octo-feather

## Rules

- `just check` is the only gate. A red gate blocks handoff.
- Tests are integration and end-to-end only: a test runs a script as a command and feeds it inputs, never loads or reads it.
- `AGENTS.md` is the only instruction file.

## Layout

- `scripts/` published commands: `octo-feather-contract` (validates a target's app-driver contract `qc.toml`), `octo-feather-evidence` (a target's evidence store), `octo-feather-new-repo` (`just new-repo`).
- `schemas/` the contract and evidence formats.
- `qc.toml` the kit's own driver contract.
- `docs/specs/` the kit's specs.
- `.agents/skills/verify-octo-feather/` the kit's own verify skill: drives the kit's commands and keeps the proof.
- `tests/` one shell test per command, run by `just check`.

## Commands

- `just check` the gate.
- `just new-repo LANG DEST`, `just install-check`.
