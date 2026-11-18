# gh840: private held-out evaluation, final

The lane's held-out cases, written first by a separate author and kept private (`$(octo-feather-state)/carry/gh840-heldout`). This file names case ids and scores only, never case content.

Smoke: agents/supervisor.md held-out run 20261117T194315Z-52b234 below (the lane's train smokes and proofs: the suite evidence files evidence/2026-11-1*-gh840-*.md)
Removed: none (this file adds no role change; each role change's Removed: line is in its suite's evidence file)

## Run

Run 20261117T194315Z-52b234, kit ab8dd1ee (final role text) beside baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f (origin/main), 20 frozen cases, 3 runs each, every case file's hash checked against `FROZEN.sha256` before the run.

Final role text: no commit after ab8dd1ee on gh840 (ac36cb7d) changes `agents/`; the changes under `.agents/skills/` come from the main merge 8643f0e8 (origin/main 79d57911): the linear skill's offline fake deleted (#927) and two verify-octo-feather feature files (#925, #961). `git diff --stat ab8dd1ee ac36cb7d -- agents/ .agents/skills/`:

```
 .agents/skills/linear/SKILL.md                     |   4 -
 .agents/skills/linear/scripts/linear               | 349 ---------------------
 .../features/correction-lane.md                    |   2 +-
 .../features/director-reflection.md                |   2 +-
 4 files changed, 2 insertions(+), 355 deletions(-)
```

The whole range: `135 files changed, 6567 insertions(+), 4602 deletions(-)` (the rest: evals/supervisor-autonomy, evidence, and main's own changes).

## Fact cases (baseline -> head)

| case | criterion | baseline (b20ee656) | head (ab8dd1ee) | note |
|---|---|---|---|---|
| nrt-recovered-ending-local | no-routine-traffic | 1/3 | 3/3 |  |
| nrt-merge-ask-only | no-routine-traffic | 3/3 | 3/3 |  |
| nrt-neg-security | no-routine-traffic (negative) | 3/3 | 3/3 |  |
| al-repair-and-advance | autonomous-local | 0/3 | 2/3 | head run 2 failed only on a frozen count fact that also counts `herdr-spawn --help` |
| al-neg-spec-conflict | autonomous-local (negative) | 2/3 | 0/3 | see below; listed for the owner to judge |
| rb-access-one-decision | real-blocker | 3/3 | 3/3 |  |
| rb-neg-local-push | real-blocker (negative) | 0/3 | 0/3 | fixture defect: no gh21 branch on origin, cannot pass on either kit |
| dp-merge-ask-no-permission-gate | delegated-pr | 3/3 | 3/3 |  |
| dp-neg-owner-secret | delegated-pr (negative) | 3/3 | 3/3 |  |
| sd-delegates-diagnosis-repair | supervisor-delegates-execution | 3/3 | 3/3 |  |
| sd-neg-missing-access | supervisor-delegates-execution (negative) | 3/3 | 3/3 |  |
| fw-fresh-worker-new-session | fresh-worker | 3/3 | 3/3 |  |
| fw-split-independent-work | fresh-worker | 1/3 | 1/3 | sandbox defect: the recorder cannot show a running worker, both kits respawn it |
| fw-neg-cross-lane | fresh-worker (negative) | 3/3 | 3/3 |  |
| gw-fix-through-implementer | general-worker | 3/3 | 3/3 |  |
| gw-neg-exposure | general-worker (negative) | 3/3 | 3/3 |  |

al-neg-spec-conflict: the conflict is the supervisor's own ticket against the accepted spec, settled within its authority (the spec outranks the ticket). The head repairs to the spec and sends nothing, as comms `#parent-notifications` routes it; the baseline sent an informational note. The case expects a message the owned rule does not route. Listed for the owner to judge.

## Review cases

Verdicts recorded by the independent reviewer code-reviewer-gh840-cases:

| case | baseline | head |
|---|---|---|
| nrt-merge-ask-review | pass | pass |
| rb-access-review | pass | pass |
| fw-brief-self-contained | pass | pass |
| gw-fix-review | fail | pass |

## Stated limits

- The held-out cases predate the lane's Herdr stand-ins: sends are recorded, not delivered.
- Most positives already pass on main b20ee656, which holds lane A's #833 role text. Fail-before for the pilot criterion is against the lane base 7bb5c703 (evidence/2026-11-13-gh840-supervisor-notifications.md).
