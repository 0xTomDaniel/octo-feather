# octo-feather

Lightweight agentic development kit built on octo-lite (`varelaseb/octo-lite`, Apache-2.0): one director (orchestrator), Pi workers in Herdr panes, a spec-chat HTML spec, and a validation gate tight enough that sloppy code cannot land. Runs on a dedicated remote box, never on the owner's Mac.

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

- `agents/` role contracts from octo-lite, appended to Pi's system prompt at spawn: orchestrator (director), implementer, integrator, code-reviewer.
- `spec/` spec-chat HTML specs (`*.spec.html`).
- `skills/` kit skills, vendored or local.
- `templates/python`, `templates/typescript` starter repos with gate, app CLI and verification skill wired.
- `scripts/` start and new-project helpers.
- `docs/adr/` lasting decisions (Matt's ADR format); `docs/plan.md` the build plan; `docs/future.md` deferred ideas.
