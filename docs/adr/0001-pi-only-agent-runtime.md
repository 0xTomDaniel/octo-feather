# Pi is the only agent runtime

Every agent octo-feather spawns runs Pi, and `AGENTS.md` is the only instruction file: no Claude Code or Codex surface, no `CLAUDE.md`, no `.claude` or `.codex` projections. One runtime means one spawn path, one set of role files and one auth route (cliproxy). Decided by Tom, 2026-10-18.

## Considered options

- octo-lite's default: Claude, with `.claude`/`.codex` projections installed. Rejected: two runtimes double every launch path and role contract.
