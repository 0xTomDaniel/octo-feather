# octo-feather

Lightweight agentic development kit built on octo-lite (`varelaseb/octo-lite`, Apache-2.0): one director over one supervisor per work item, Pi workers in Herdr panes, a spec-chat HTML spec, and a validation gate tight enough that sloppy code cannot land.

This file governs work on the kit itself. Terms (director, supervisor, worker, work item, lane) are defined in [GLOSSARY.md](GLOSSARY.md). Target repos get their own `AGENTS.md` from `templates/`.

## Rules

- Pi is the only agent runtime. No Claude/Codex config, no `CLAUDE.md`.
- `AGENTS.md` is the only instruction file in any repo the kit touches.
- Agents hand off to each other through Herdr (`skills/herdr-comms`). No workflow engine, no tracker, no daemon.
- Tests are integration and end-to-end only, driven through public surfaces (app CLI, HTTP, UI). No unit tests of internals.
- Every template exposes one gate command, `just check`, used identically by agents, git hooks and CI. A red gate blocks handoff.
- Enforce lessons in this order: architecture or types, then a lint or check whose error names the fix, then a test, then prose. Prose rules are the last resort.
- Vendored skills keep upstream license and provenance in `skills.lock`.

## Layout

- `agents/` role files in pi-subagents frontmatter (docs/adr/0013): meta-operator (director), supervisor, implementer, integrator, code-reviewer. One file, two launchers: `scripts/pi-role` for Herdr panes (via `herdr-spawn`), pi-subagents' `subagent` tool for children. `agents/skills/` holds the skillfile-managed upstream skills (Matt's `tdd` with its seam-gate patch).
- `spec/` spec-chat HTML specs (`*.spec.html`). Today it holds octo-lite's own spec, kept as the format reference and for the `#anchors` the role contracts cite; it still describes Claude and Linear, so `docs/adr/` wins where they differ.
- `skills/` kit skills, vendored or local.
- `templates/python`, `templates/typescript` starter repos with gate, app CLI and verification skill wired.
- `scripts/` published commands on every agent's `PATH`: `octo-feather-start` (director or lane workspace), `octo-feather-state` (state dir).
- `.pi/settings.json` pins pi-subagents project-local; `just install` fetches it into ignored `.pi/npm`. Pi loads it inside this checkout only after project trust (`pi -a`).
- `justfile` kit commands: `just check` (the gate), `just install`, `just install-check`, `just start`, `just supervise N`, `just state`.
- `NOTICE`, `LICENSE` Apache-2.0 attribution for the octo-lite-derived files.
- `docs/adr/` lasting decisions (Matt's ADR format); `docs/plan.md` the build plan; `docs/future.md` deferred ideas.
