# gh530: principle-build-the-lever read at the moment it applies

Change: the skill's description (via `.skillfile/patches/skills/principle-build-the-lever/SKILL.md.patch`) names the repeat moment; the skill-load step line of agents/director.md and agents/supervisor.md names that role's repeat moment. The corrector step line was changed at 04ae8f9 and reverted (supervisor ruling: no case separates it). No skill text inlined (owner ruling 2026-11-04, #520).

Smoke: .agents/skills/principle-build-the-lever/SKILL.md .skillfile/patches/skills/principle-build-the-lever/SKILL.md.patch agents/director.md agents/supervisor.md agents/corrector.md, skill-triggers lever cases at kit 04ae8f9 (the skill materialized from the patch by --kit-ref) beside baseline origin/main ea7d779: runs 20261104T195144Z-b00744 (should-trigger, --runs 3) and 20261104T202158Z-aa9926 (should-not, once). Pre-change smoke: 20261104T194613Z-140cfb (dir-lever-teardown-again FAIL at ea7d779 and 780ea97).

Removed: nothing.

## Held-out cases (frozen before any run of them)

- dir-lever-event-lines
- dir-lever-near-verify-sha
- sup-lever-status-rows (removed, see Removed cases)
- sup-lever-near-finding-logged
- cor-lever-restated-comments
- cor-lever-near-owner

Train: dir-lever-teardown-again, dir-lever-near-one-ruling, sup-lever-record-merge-ask, sup-lever-near-set-waiting, cor-lever-restated-sites, cor-lever-near-one-pointer.

## Real moments the cases come from

- dir-lever-teardown-again: director.handoffs.jsonl:812,817,840, lanes gh206, gh421, gh436 torn down by hand in two days while post-merge step 5 was blocked (#439).
- dir-lever-event-lines: director.handoffs.jsonl:961, manual-director-event-recording: hand-written appends, one timestamp the report could not read.
- dir-lever-near-one-ruling: director.handoffs.jsonl:875, issue 127: one owner ruling recorded once.
- dir-lever-near-verify-sha: director.handoffs.jsonl:218, finding 57: one reported sha verified at source.
- sup-lever-record-merge-ask: gh436.handoffs.jsonl:27, manual-lane-bookkeeping: JSONL events hand-built, waiting_on and last_handoff_at edited apart.
- sup-lever-status-rows: gh127.handoffs.jsonl:15, status-tool-gap: eight planned criteria added to a status file by hand.
- sup-lever-near-set-waiting: gh436.handoffs.jsonl:27: the single waiting_on edit.
- sup-lever-near-finding-logged: gh439.handoffs.jsonl:13: whether a round 1 finding was already caught.
- cor-lever-restated-sites: gh118.handoffs.jsonl:74-83, review rounds 6-7: corrector-gh118 pointed restatements site by site, round 7 found more.
- cor-lever-restated-comments: gh121.handoffs.jsonl:25-44, PR 140 rounds 461779c, 6101554, 083a2f5: comments, docstrings, test headers restating owned rules, missed sites each round (fixer an implementer; the same fix-round moment a corrector meets).
- cor-lever-near-one-pointer: gh127.handoffs.jsonl:94, final review c5da94e: one restatement, one pointer.
- cor-lever-near-owner: gh160.handoffs.jsonl:5-16, duplicated-rule rounds: which file owns the rule, a read only.

Fixture `rules-restated-sites`: no existing fixture holds more than 2 restatements; the real moments had 4 to 6 files.

## Results (runner: lane 479 scripts/octo-feather-qa, scripts/check-evals and eval-cases skill files at fd62302, byte copies in a detached worktree of 04ae8f9; --evals that worktree's evals, --kit-ref 04ae8f9, --baseline origin/main)

Should-trigger, --runs 3, run 20261104T195144Z-b00744 (pass rate baseline -> head):

| split | case | origin/main | 04ae8f9 |
|---|---|---|---|
| train | dir-lever-teardown-again | 0/3 | 3/3 |
| train | sup-lever-record-merge-ask | 0/3 | 3/3 |
| train | cor-lever-restated-sites | 2/3 | 3/3 |
| held-out | dir-lever-event-lines | 0/3 | 3/3 |
| held-out | sup-lever-status-rows | 0/3 | 0/3 |
| held-out | cor-lever-restated-comments | 3/3 | 3/3 |

Should-not, once, run 20261104T202158Z-aa9926:

| split | case | origin/main | 04ae8f9 |
|---|---|---|---|
| train | dir-lever-near-one-ruling | PASS | FAIL |
| train | sup-lever-near-set-waiting | PASS | PASS |
| train | cor-lever-near-one-pointer | PASS | PASS |
| held-out | dir-lever-near-verify-sha | PASS | PASS |
| held-out | sup-lever-near-finding-logged | PASS | PASS |
| held-out | cor-lever-near-owner | PASS | PASS |

Findings:

- sup-lever-status-rows (held-out, frozen): never reaches the moment. The fixture's spec lacks the eight criteria, so in all 3 head runs the supervisor refuses after 3 reads (spec-status check would fail on the extra ids) and edits nothing. A case defect, not a trigger result; not edited (held-out).
- cor-lever-restated-comments (held-out): non-discriminating; the corrector on main already loads the lever with encode-lessons on a third-round class finding.
- cor-lever-restated-sites (train): weak separation, 2/3 on main.
- dir-lever-near-one-ruling (train): over-trigger at 04ae8f9; the director's thinking cites the step line's "an event line" for one append (the director logs every action as an event line).

## Rulings after the batch (supervisor, #530)

- Director step line tuned on the train over-trigger only (dir-lever-near-one-ruling): "an event line" became "several event lines", plus "one line or one edit is no repeat". dir-lever-event-lines (held-out) is rerun after this train-driven change and was never tuned on.
- Corrector step line reverted to origin/main's: no case separates it. On main the corrector already loads the lever with encode-lessons on these fix rounds. cor-lever-restated-comments (held-out) is non-discriminating (3/3 -> 3/3); cor-lever-restated-sites (train) is weak (2/3 -> 3/3). Both cases stay.

## Removed cases

- sup-lever-status-rows (held-out should-trigger), removed from the suite after its result was seen (run 20261104T195144Z-b00744: origin/main 0/3, 04ae8f9 0/3). Reason: defective, not a lever result: the lane-mini spec lacks the eight criteria the task names, so on both kits the supervisor refuses after reading (spec-status check would fail on the extra ids) and never reaches the moment. Not edited and no replacement written. Supervisor held-out should-trigger coverage is the pre-existing sup-lever-handoff-stamp only: the supervisor's held-out evidence for this change is that one pre-existing case, which was not rerun here.
