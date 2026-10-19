# Build plan, Sun 2026-10-18

Done predicate: by tonight, on the dedicated remote, one rehearsal mini-project per language went spec-chat HTML spec, accepted, director dispatch, supervisor, Pi implementer, integrator, code-reviewer, green `just check`, evidence bundle, without Tom touching code.

Purpose: pass the Martell/Winly take-home (due EoD Thu 10-22) at Tom's best. The email stays unopened until the kit is ready, so the kit is stack-agnostic: Python and TypeScript both prepared. Submit the method (AGENTS.md, spec, evidence) with the code if the rules allow.

Base: skills are vendored from mattpocock/skills `49dd158` and pstack `0b8e952` (cursor/plugins) through `Skillfile`; octo-lite `cc6fa4e` supplies requirements and the wiring skeleton only. Lasting decisions live in `docs/adr/` (Matt's ADR format); there is no separate decisions file.

Role files: our own frontmatter read by `scripts/pi-role`, and every agent launches through `herdr-spawn` + `pi-role` (docs/adr/0013, 0016); models decided by Tom 2026-10-18 (opus-5-5 for director, supervisor, implementer, corrector; gpt-6.1-sol for code-reviewer). Escalation up the chain only: docs/adr/0015. Jev: nothing from Jev (capture, replay or judge) runs in `just check`, which stays deterministic; the product judge is `just qc` (interim cross-family judge until Jev, docs/adr/0022) and factory evals are `just qa`.

| # | Block | Est | Output |
|---|---|---|---|
| 0 | Remote box | 45m | Provider chosen by Tom; Debian/Ubuntu, 8+ GB RAM (several Pi agents plus pnpm/Playwright); Tailscale; git, gh, just, uv, node+pnpm, pi, herdr, jq; spec-chat review hosting reachable from Tom's browser |
| 1 | Repo, decisions, plan | done | this repo |
| 2 | Port octo-lite pieces into octo-feather + Pi delta | 60m | Built here in the octo-feather repo (octo-lite is a source, never installed on the remote); octo-lite-derived files with NOTICE; spawns default `-- pi`; `.claude`/`.codex` projections and `CLAUDE.md` removed; Linear removed (GitHub Issues); meta-operator kept as director, spawns Pi; installer `--check` green on the remote. Done 2026-10-18 17:36 MDT on the VM: ported (b3b8b09..), Pi-only herdr-comms with kit contracts, `--skill` loading and Pi parking, `just check` + `just install-check` green, `just start` / `just lane N` smoke-tested; role files still octo-lite format |
| 3 | Comms smoke | 45m | `octo-lite-start --runtime pi` director spawns a Pi implementer, `herdr-say` brief, result returns to director pane. Done 2026-10-18 20:16 MDT: director, supervisor, implementer via herdr-spawn + pi-role, change integrated with `just integrate`, `CHAIN OK` back at the director, $0.37 (evidence/block3-comms-smoke.md) |
| 4 | Python template | 90m | uv, ruff strict, basedpyright strict, import-linter, pytest integration+E2E, app CLI `--json`, `just check`, pre-commit, GitHub Actions; target `AGENTS.md` with `Repo skills:` line. Done 2026-10-18 20:21 MDT: `templates/python`, ruff ALL, basedpyright strict, one import-linter layer contract, 3 CLI tests (in-process and subprocess), `.githooks/pre-commit` instead of the pre-commit framework (lighter, not installed), `just check` green in a fresh copy |
| 5 | TypeScript template | 90m | pnpm, tsc strictest, typescript-eslint strict-type-checked, dependency-cruiser, knip, Vitest integration, Playwright E2E if UI, app CLI `--json`, same `just check`. Done 2026-10-18 20:23 MDT: `templates/typescript`, tsc strictest, typescript-eslint strict-type-checked, dependency-cruiser core-never-imports-cli, knip, Vitest CLI tests (in-process and built `app` subprocess), no Playwright (no UI), `.githooks/pre-commit`, `just check` green in a fresh copy |
| 6 | Skill deltas | 45m | `tdd` patch: seams = integration/E2E only; pstack create-verification-skill + selected principles; `skills.lock` with SHAs + licenses. Rebase done 2026-10-18 20:00 MDT: implement, implement-spec, to-tickets, grill-with-docs (+ grilling, domain-modeling), tdd, code-review from Matt 49dd158 and pstack `correct`, all through `Skillfile` with reason-headed patches (docs/adr/0012); supervisor briefs use pstack orchestrate's brief format. Left: create-verification-skill |
| 7 | Dress rehearsal | 60m+ | one tiny project per language through the full loop on the remote; fix what breaks |
| 8 | Submission bundle | 20m | `evidence/` layout, README "How this was built" |

Decided, not built (Tom, 2026-10-19):
- A kit `just` recipe registers `herdr-wake` as Spec Chat's wake provider.
- A kit `just` recipe creates a target repo from a template (`templates/python` or `templates/typescript`).
- `just spec-chat REPO` installs Spec Chat's skills into a target repo as `.agents/skills/spec-chat-*` links only, gitignored (they point into a machine-local clone); never `.claude/` or `.codex/` links (ADR 0001 unchanged). Built after spec-chat #170 merges and its installer can skip the provider links.

Estimates are guesses. Block 7 is the one that matters; cut 6 before cutting 7.

Sources pinned today: octo-lite `cc6fa4e` (Apache-2.0), pstack `0b8e952` (cursor/plugins, MIT), mattpocock/skills `49dd158d` (MIT).
