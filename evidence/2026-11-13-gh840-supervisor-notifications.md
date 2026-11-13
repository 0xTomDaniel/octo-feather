# gh840 #873: supervisor notifies the director only on allowed events

Criterion: comms `#acceptance-no-routine-traffic`. Suite `evals/supervisor-notifications` (train cases), graded on the supervisor's runs of `herdr-say --parent` in the qa sandbox's run record, with the `ran` fact's new `count` (schema.md, Run record).

Smoke: agents/supervisor.md .agents/skills/eval-cases/references/schema.md run below: smokes at `--runs 1 --baseline origin/main` (runs 20261113T054416Z-dcda93, 20261113T054708Z-69cf1a, 20261113T062902Z-9ac316, 20261113T070257Z-4d8110), then the 3-run proof 20261113T073528Z-9dcd58.
Removed: agents/supervisor.md "Either way tell the director which worker ended without reporting and what you did: the result you consumed, or the worker started in its place." (live-caught, PR #833 evidence/2026-11-13-gh785-live-role-smokes.md, Supervisor (b)); "Notify the parent after meaningful gate or risk change."; the Output line "Concise status with exact gate, health, material change, blocker, and next action, sent to its recipient by `herdr-say`", each replaced by a pointer to comms `#parent-notifications`.

## Proof

`scripts/octo-feather-qa --suite supervisor-notifications --runs 3 --baseline origin/main`, run 20261113T073528Z-9dcd58, kit 71ae5bdfa85c (head) beside baseline 7bb5c70399dc (origin/main):

| case | baseline pass rate | head pass rate |
|---|---|---|
| routine-results-no-director | 0.00 (0/3) | 1.00 (3/3) |
| merge-ready-only-merge-ask | 0.00 (0/3) | 1.00 (3/3) |
| owner-blocker-reaches-director (negative) | 1.00 (3/3) | 1.00 (3/3) |

```
  compare supervisor-notifications/routine-results-no-director: baseline kit 7bb5c70399dc beside current kit 71ae5bdfa85c
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
  compare supervisor-notifications/merge-ready-only-merge-ask: baseline kit 7bb5c70399dc beside current kit 71ae5bdfa85c
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
  compare supervisor-notifications/owner-blocker-reaches-director: baseline kit 7bb5c70399dc beside current kit 71ae5bdfa85c
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
qa: 3/3 passed (run 20261113T073528Z-9dcd58)
```

- routine: every baseline run sent the director a check-in (`herdr-say --parent gh12 check-in ...`); every head run sent nothing.
- merge-ready: every baseline run sent one director message, the merge ask with the recovered reviewer's routine note before it ("Worker note: code-reviewer-gh15 (w2:p7) went idle without reporting ..."), so the exact-section fact failed; the `count 1` fact passed on both kits (the analysis flags it non-discriminating: the bundled note, not a second send, is the baseline's routine traffic). Every head run sent exactly the printed section. No trailing-whitespace fragility seen: the head's three recorded arguments equal the section.
- owner blocker (negative): a real owner-held blocker reached the director on both kits, as it must.

Smoke finding that changed the role: at the first head smoke (20261113T062902Z-9ac316) the supervisor sent the section with a line "gh12 merge ask (owner gate):" before it, against supervisor.md's "send only the section it prints"; that sentence now says "exactly as printed: no line added before or after it" (20261113T070257Z-4d8110 PASS).

Held-out cases are written and scored by their separate author, not here.

Stated limit: the director is reached through `herdr-say --parent`; a message sent to the director's pane by id is not counted. The tasks never name the director's pane.
