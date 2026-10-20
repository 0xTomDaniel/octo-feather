# Pi is the only agent runtime

Every agent octo-feather spawns runs Pi, and `AGENTS.md` is the only instruction file: no Claude Code or Codex surface, no `CLAUDE.md`, no `.claude` or `.codex` projections. One runtime means one spawn path, one set of role files and one auth route (cliproxy). Decided by Tom, 2026-10-18.

Clarified by Tom, 2026-10-20: inert upstream files inside a vendored skill folder (such as `agents/openai.yaml` from mattpocock/skills) are not a Codex surface; they stay committed verbatim so the folder equals upstream at its pin plus patches (`just check-vendored`).

## Considered options

- octo-lite's default: Claude, with `.claude`/`.codex` projections installed. Rejected: two runtimes double every launch path and role contract.
