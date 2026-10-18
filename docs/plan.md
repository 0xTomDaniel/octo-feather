# Build plan, Sun 2026-10-18

Done predicate: by tonight, a rehearsal mini-project in each language went spec, director, implementer, verifier, green `just check`, evidence bundle, without Tom touching code.

| # | Block | Est | Output |
|---|---|---|---|
| 1 | Repo, decisions, plan | 30m | this repo |
| 2 | Comms smoke | 60m | `scripts/feather-start`, ported `herdr-comms` (Pi only); director pane spawns an implementer pane, sends brief, gets report back |
| 3 | Python template | 90m | uv, ruff (strict rule set), basedpyright strict, import-linter, pytest integration+E2E, Typer app CLI `--json`, `just check`, pre-commit hook, GitHub Actions |
| 4 | TypeScript template | 90m | pnpm, tsc strictest, typescript-eslint strict-type-checked, dependency-cruiser, knip, Vitest integration, Playwright E2E if UI, app CLI `--json`, same `just check` |
| 5 | Roles | 60m | director (pstack brief: GOAL, SCOPE, CONTEXT, ACCEPTANCE, VERIFY, TIMEBOX, FORBIDDEN, REPORT, STANDING), implementer, verifier; escalation rules |
| 6 | Skills | 45m | pinned: pocock to-spec, grill-with-docs, tdd (patched to integration/E2E); pstack create-verification-skill, interrogate, selected principles (paths adapted from `.cursor` to `.agents`); `skills.lock` with SHAs + licenses |
| 7 | Dress rehearsal | 60m+ | one tiny project per language through the full loop; fix what breaks |
| 8 | Submission bundle | 20m | `evidence/` layout, README section "How this was built" |

Estimates are guesses. Block 7 is the one that matters; cut 6 before cutting 7.

Sources pinned today: octo-lite `cc6fa4e`, pstack `0b8e952` (cursor/plugins, MIT), mattpocock/skills `49dd158d` (MIT).
