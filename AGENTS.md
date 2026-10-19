# octo-feather

Lightweight agentic development kit built on octo-lite (`varelaseb/octo-lite`, Apache-2.0): one director over one supervisor per work item, Pi workers in Herdr panes, a spec-chat HTML spec, and a validation gate tight enough that sloppy code cannot land.

This file governs work on the kit itself. Terms (director, supervisor, worker, work item, lane) are defined in [GLOSSARY.md](GLOSSARY.md). Target repos get their own `AGENTS.md` from `templates/`.

## Rules

- Pi is the only agent runtime. No Claude/Codex config, no `CLAUDE.md`.
- `AGENTS.md` is the only instruction file in any repo the kit touches.
- Agents hand off to each other through Herdr (`.agents/skills/herdr-comms`). No workflow engine, no tracker, no daemon.
- Tests are integration and end-to-end only, driven through public surfaces (app CLI, HTTP, UI). No unit tests of internals.
- Every template exposes one gate command, `just check`, used identically by agents, git hooks and CI. A red gate blocks handoff.
- Enforce lessons in this order: architecture or types, then a lint or check whose error names the fix, then a test, then prose. Prose rules are the last resort.
- Vendored skills are pinned in `Skillfile` and `Skillfile.lock`, materialized into `.agents/skills/`, and changed only through patches in `.skillfile/patches/`. Upstream license and attribution live in `NOTICE`.

## Layout

- `agents/` role files, our frontmatter format read by `scripts/pi-role` (docs/adr/0013): director, supervisor, implementer, code-reviewer, corrector. Integration is a script, not an agent: `just integrate N REF...` (`scripts/octo-feather-integrate`, docs/adr/0017). Every agent launches through `scripts/pi-role`: in a Herdr pane via `herdr-spawn --role`, or headless with `-p`. `.agents/skills/` holds the skillfile-managed upstream skills (mattpocock/skills and pstack; each patch's first line gives its reason).
- `spec/` spec-chat HTML specs (`*.spec.html`). Today it holds octo-lite's own spec, kept as the format reference and for the `#anchors` the role contracts cite; it still describes Claude and Linear, so `docs/adr/` wins where they differ.
- `.agents/skills/` every kit skill, vendored (Skillfile `github` entries) or local (docs/adr/0018). Role files stay in `agents/`.
- `templates/python`, `templates/typescript` starter target repos: app CLI with `--json`, integration and E2E tests through it, `just check` (also run by `.githooks/pre-commit` and CI), `just integrate`, and an `AGENTS.md` with a `Repo skills:` line. Copy one, then `just setup`.
- `scripts/` published commands on every agent's `PATH`: `octo-feather-start` (director or lane workspace), `octo-feather-state` (state dir), `octo-feather-integrate` (`just integrate`), `octo-feather-accepted` (kickoff check: is a spec accepted at an exact commit), `octo-feather-spec-status` (per-criterion status file beside a spec, docs/adr/0021).
- `justfile` kit commands: `just check` (the gate), `just install-check`, `just start`, `just supervise N`, `just integrate N REF...`, `just state`, and the stubs `just qc` (Jev product judge) and `just qa` (factory evals), which never run inside `just check`.
- `NOTICE`, `LICENSE` Apache-2.0 attribution for the octo-lite-derived files.
- `docs/adr/` lasting decisions (Matt's ADR format); `docs/plan.md` the build plan; `docs/future.md` deferred ideas.
