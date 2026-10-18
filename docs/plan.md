# Build plan, Sun 2026-10-18

Done predicate: by tonight, on the dedicated remote, one rehearsal mini-project per language went spec-chat HTML spec, accepted, director (orchestrator) dispatch, Pi implementer, integrator, code-reviewer, green `just check`, evidence bundle, without Tom touching code.

Purpose: pass the Martell/Winly take-home (due EoD Thu 10-22) at Tom's best. The email stays unopened until the kit is ready, so the kit is stack-agnostic: Python and TypeScript both prepared. Submit the method (AGENTS.md, spec, evidence) with the code if the rules allow.

Base: octo-lite `cc6fa4e`. Work is deltas on it. Lasting decisions live in `docs/adr/` (Matt's ADR format); there is no separate decisions file.

Pending: role-file format waits on the pi-subagents spike (VM, 10-18); Jev placement (`just check` or a merge gate) waits on Tom.

| # | Block | Est | Output |
|---|---|---|---|
| 0 | Remote box | 45m | Provider chosen by Tom; Debian/Ubuntu, 8+ GB RAM (several Pi agents plus pnpm/Playwright); Tailscale; git, gh, just, uv, node+pnpm, pi, herdr, jq; spec-chat review hosting reachable from Tom's browser |
| 1 | Repo, decisions, plan | done | this repo |
| 2 | Port octo-lite pieces into octo-feather + Pi delta | 60m | Built here in the octo-feather repo (octo-lite is a source, never installed on the remote); octo-lite-derived files with NOTICE; spawns default `-- pi`; `.claude`/`.codex` projections and `CLAUDE.md` removed; Linear removed (GitHub Issues); meta-operator kept as director, spawns Pi; installer `--check` green on the remote. Done 2026-10-18 17:36 MDT on the VM: ported (b3b8b09..), Pi-only herdr-comms with kit contracts, `--skill` loading and Pi parking, `just check` + `just install-check` green, `just start` / `just lane N` smoke-tested; role files still octo-lite format |
| 3 | Comms smoke | 45m | `octo-lite-start --runtime pi` director spawns a Pi implementer, `herdr-say` brief, result returns to director pane |
| 4 | Python template | 90m | uv, ruff strict, basedpyright strict, import-linter, pytest integration+E2E, app CLI `--json`, `just check`, pre-commit, GitHub Actions; target `AGENTS.md` with `Repo skills:` line |
| 5 | TypeScript template | 90m | pnpm, tsc strictest, typescript-eslint strict-type-checked, dependency-cruiser, knip, Vitest integration, Playwright E2E if UI, app CLI `--json`, same `just check` |
| 6 | Skill deltas | 45m | `tdd` patch: seams = integration/E2E only; pstack create-verification-skill + selected principles; `skills.lock` with SHAs + licenses |
| 7 | Dress rehearsal | 60m+ | one tiny project per language through the full loop on the remote; fix what breaks |
| 8 | Submission bundle | 20m | `evidence/` layout, README "How this was built" |

Estimates are guesses. Block 7 is the one that matters; cut 6 before cutting 7.

Sources pinned today: octo-lite `cc6fa4e` (Apache-2.0), pstack `0b8e952` (cursor/plugins, MIT), mattpocock/skills `49dd158d` (MIT).
