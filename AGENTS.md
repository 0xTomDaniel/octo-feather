# octo-feather

Lightweight agentic development kit: one director, a few Pi workers in Herdr panes, a spec, and a validation gate tight enough that sloppy code cannot land.

This file governs work on the kit itself. Target repos get their own `AGENTS.md` from `templates/`.

## Rules

- Pi is the only agent runtime. No Claude/Codex config, no `CLAUDE.md`.
- `AGENTS.md` is the only instruction file in any repo the kit touches.
- Agents hand off to each other through Herdr (`skills/herdr-comms`). No workflow engine, no tracker, no daemon.
- Tests are integration and end-to-end only, driven through public surfaces (app CLI, HTTP, UI). No unit tests of internals.
- Every template exposes one gate command, `just check`, used identically by agents, git hooks and CI. A red gate blocks handoff.
- Enforce lessons in this order: architecture or types, then a lint or check whose error names the fix, then a test, then prose. Prose rules are the last resort.
- Vendored skills keep upstream license and provenance in `skills.lock`.

## Layout

- `roles/` role contracts appended to Pi's system prompt at spawn: director, implementer, verifier.
- `skills/` kit skills, vendored or local.
- `templates/python`, `templates/typescript` starter repos with gate, app CLI and verification skill wired.
- `scripts/` start and new-project helpers.
- `docs/decisions.md` dated decisions with who decided and why.
