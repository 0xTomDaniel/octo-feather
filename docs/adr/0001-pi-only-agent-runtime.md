# Pi is the only agent runtime

Every agent octo-feather spawns runs Pi, and `AGENTS.md` is the only instruction file: no Claude Code or Codex surface, no `CLAUDE.md`. octo-lite defaults to Claude and installs `.claude`/`.codex` projections, so this departs from it on purpose: one runtime means one spawn path, one set of role contracts and one auth route (cliproxy). Decided by Tom, 2026-10-18.
