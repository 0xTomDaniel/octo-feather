# gh690: extended hand-built infrastructure needs its Prior art line

Change: the code-review skill's Verdict step, **Prior art** (patch `.skillfile/patches/skills/code-review/SKILL.md.patch`, materialized `.agents/skills/code-review/SKILL.md`): a diff extending hand-built infrastructure the repo already has needs its `Prior art:` line, blocked as `reinvented-library` without one (spec quality#acceptance-prior-art-extends). Cases: docs/owed-evals/690.md.

Smoke: .agents/skills/code-review/SKILL.md (the proof run below drives the code reviewer through it)
Smoke: .skillfile/patches/skills/code-review/SKILL.md.patch (the patch that materializes it; same run)
Removed: nothing deleted; the incident is #576 (lane #503 grew the kit's hand-built qc sandbox, its uv-cache overlay, after the 2026-10-28 prior-art rule, with no Prior art line).

## Proof run (eval slot, gh576 grant)

`scripts/octo-feather-qa --case prior-art-extends --case prior-art-extends-stated --case prior-art-extends-held-out --runs 3 --baseline 9fd7bff`, run 20261107T032137Z-c69b58.

- Baseline B 9fd7bff: cases (b5aad3a, fixture fix 1ccb39f) merged with gh576 efea1c6 (launcher stdout fix); no skill patch.
- Head H 35a0d04: B plus the patch (400fd71) and docs/owed-evals/690.md.

| case | H runs passed | B runs passed |
|---|---|---|
| prior-art-extends (train) | 3/3 | 3/3 |
| prior-art-extends-stated (negative) | 0/3 | 0/3 |
| prior-art-extends-held-out (held-out, scored apart) | 3/3 | 3/3 |

Analysis: `non-discriminating case` for all three; no high variance, no cost tradeoff. Cost per run, mean: train H $0.095, B $0.099; negative H $0.130, B $0.112; held-out H $0.093, B $0.078.

Class tags the reviewer put in its json block (shown, not graded: docs/owed-evals/541.md):

- train, B and H, 6/6 runs: `reinvented-library` (2 runs also a parsing finding). B run 1: "The existing justification at lines 3-5 covers only plain names in a block list, not T13's quoted scalars, comments and flow lists. The implementer's `Prior art: none` misses this infrastructure."
- held-out, B and H, 6/6 runs: `reinvented-library`.
- negative, B and H, 6/6 runs: parsing findings only (a `]` inside a comment ends the flow list; a tab before `#`); each run accepted the stated reason (H run 1: "The implementer states a dependency-avoidance reason, so no automatic `reinvented-library` finding").

## Result

Not separating: acceptance quality#acceptance-qa-fails-before is not met by these cases. The baseline reviewer already reads "adds or uses" as covering an extension of a small, plainly-parser piece; the gap #576 records does not reproduce on these fixtures. The negative measures the fixture parser's correctness, not the line. Earlier runs: 20261107T024302Z-fd5746 (no model ran: srt not installed), 20261107T024449Z-e94a2e (2 runs died on the qa watcher's non-blocking stdout, fixed in gh576 efea1c6; the negative blocked on fixture parser bugs, fixed in 1ccb39f).
