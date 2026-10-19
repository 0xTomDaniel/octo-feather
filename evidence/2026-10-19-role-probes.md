# Role probes, 2026-10-19

Smoke runs for this batch's behaviour changes to role files and skills (ADR 0008, until `just qa` exists).

Setup: each probe starts the real role headless (`pi-role agents/<role>.md --model anthropic/claude-sonnet-5-5 --thinking off -p "<scenario>"`) in an empty git repo, with no Herdr session. The prompt asks for its next actions and their commands, and says to run nothing. A probe shows how the role text reads to a model. It is weaker than a live chain like block 3, and is no substitute for the owed eval cases in `docs/future.md`. The lane-level behaviours were also seen live in `2026-10-19-qc-smoke.md` and `2026-10-19-language-skills-smoke.md`.

| Probe | Change under test | Answer (abridged) | Result |
|---|---|---|---|
| director, chat acceptance | ADR 0021: the button is the only acceptance | "Record nothing. Chat acceptance does not count." Re-sends the review link and waits for Accept spec; after acceptance, runs the spec PR steps. | as designed |
| director, repeat trigger | ADR 0020 / F08 | Two lines older than the closed #12: skip, after checking `gh issue view 12 --json closedAt`. A third line dated after the close: starts a correction lane (issue, worktree, `octo-feather-start`, corrector brief). | as designed |
| supervisor, lane | F02, F05, ADR 0022, fan-out | Integrates `w8` itself, opens the draft PR, runs `just qc ... acceptance-a`, then reviews the head QC left. Runs `#9` and `#10` in parallel. Non-blocking notes go in the PR body. Self-checks "QC and review on the same head with only QC's status commit between them". | as designed, with one gap (below) |
| supervisor, revision | F03, one review row per spec | Not wording-only, so it revises with `spec-chat-shape`. Registers with `review-host register --slug templates` ("the spec's slug, not gh7"). The message up lists `acceptance-layer-break` as affected through the governing clause. After acceptance it moves `accepted_commit`, resets that criterion to planned, then rebuilds it and runs `just qc`. | as designed |
| `just shape`, before its prompt line | ADR 0021 shaping chat | Planned to edit `scripts/octo-feather-integrate` itself, with "no skill needed". | gap, fixed |
| `just shape`, after | same | "I won't touch the script, since changes are built by the factory after you accept the spec." Plans sharpen, grilling or grill-with-docs, then spec-chat-shape, and reports that spec-chat-shape is not installed. | as designed |

Gaps found and fixed:
- `just shape` had only the skills, and no line saying it is a shaping chat, so it would implement. `octo-feather-shape` now appends a three-sentence prompt.
- At the end of the lane, the supervisor ran the final `just qc` on `acceptance-b acceptance-c` only, because the pilot line said "the criteria claimed so far". ADR 0022 has QC judge the whole head against every criterion the lane claims. The supervisor's Delivery section now says the final run names every criterion of the lane, the pilot's included.

Cost: the four role probes $0.15, the two shape probes $0.04.

Spec Chat's skills were absent in every probe (`pi-role: external skill spec-chat-shape not installed in <repo>/.agents/skills; skipped`), as expected now that roles read only the target repo's `.agents/skills`. See the report on spec-chat PR #170.
