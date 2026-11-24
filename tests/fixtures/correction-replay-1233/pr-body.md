Closes #1228

## Summary

`octo-feather-lane skills` no longer sends a worker back for a skill it read (#1228).
- #1231: the bash reader treats `#` as a comment only at a word's start, as bash does (a mid-word `#`, as in `spec#anchor`, dropped every later read on the line: #1199); `Skills:` names drop trailing punctuation (`python.`: #1134, #1136, #1137).
- #1232: when a session names a skill's SKILL.md only in a call the reader cannot resolve (grep, loop, `$VAR`/glob/brace path), the answer is `cannot tell`: exit 2, a non-blocking skills-unchecked finding, never a send-back. A real miss still exits 1 and sends back once.
- Scope: cmd_skills and its reader only; the report's skill-reach counts read the same read set.

## Replay (read-only, scratch state; before = 30086cb1, after = 0310af8c)

Command: `python3 /home/exedev/scratch/gh1228-replay/replay.py`; full table: /home/exedev/scratch/gh1228-replay/TABLE.md (rerun clean by the code reviewer). Each session cut at its finding time; each ticket read as it stood then.

| Ticket | Worker session | Skill | Verdict (#1228 report) | Exit before | Exit after | After says |
|---|---|---|---|---|---|---|
| #1134 | 16e53032 | codebase-design | true miss | 1 | 1 | not loaded |
| #1134 | 16e53032 | tdd | true miss | 1 | 1 | not loaded |
| #1134 | 16e53032 | python. | false | 1 | 1 (its 2 true misses) | loaded |
| #1136 | 7bb48357 | python. | false | 1 | 0 | loaded |
| #1137 | 79b09591 | python. | false | 1 | 0 | loaded |
| #1139 | fdc348b2 | tdd | true miss | 1 | 1 | not loaded |
| #1213 | 30aa6a82 | tdd | true miss | 1 | 1 | not loaded |
| #1213 | 30aa6a82 | python | true miss | 1 | 1 | not loaded |
| #1220 | 0528582e | python | true miss | 1 | 1 | not loaded |
| #1220 | 0528582e | codebase-design | true miss | 1 | 1 | not loaded |
| #1214 | d54187c9 | tdd | true miss | 1 | 1 | not offered |
| #1214 | d54187c9 | codebase-design | true miss | 1 | 1 | not offered |
| #1193 | 1169c21e | tdd | true miss | 1 | 1 | not loaded |
| #1193 | 1169c21e | python | true miss | 1 | 1 | not loaded |
| #1198 | 069e452c | python | true miss | 1 | 1 | not loaded |
| #1199 | 97e2c882 | tdd | false | 1 | 0 | loaded |
| #1199 | 97e2c882 | python | false | 1 | 0 | loaded |

17 items: the 12 true misses still exit 1; the 5 false items are now loaded. 59 report sessions: 0 rows off; every session whose named skills were all read exits 0 (also #1135, before 1, now 0); #1152 (131b16c8, python read only by grep) now says python cannot tell.

## Validation

- Final head 0310af8c: just integrate --full green (457 passed, 5 skipped), OCTO_FEATHER_QC_CLAIMS=issue-lifecycle#acceptance-ticket-skills.
- just qc: acceptance-ticket-skills PASS at 0310af8c (status commit 0b665281). Lane claims this criterion for qc: its demo (tests/gate/kit/lane_skills.py demo) changed.
- Code review clear at 0310af8c. Non-blocking notes: duplicated-rule (comments restating the cannot-tell rule), misleading-help (help line 459 lists write/edit beside cannot tell; the code keeps them misses).

## Merge ask
Head: 0b665281
Checks: scope and check SUCCESS on judged head 0310af8c; on 0b665281 scope SUCCESS, check SKIPPED (status-only commit)
Judged: 0310af8c5494 to 0b665281fec8: qc status commits 0b665281fec8 change only docs/specs/issue-lifecycle.status.json
| criterion | qc verdict | judged | evidence |
|---|---|---|---|
| issue-lifecycle#acceptance-ticket-skills | pass | judged 0310af8c | /home/exedev/.local/state/octo-feather/qc/0310af8c5494b5320e37274893ea4b824edf399c-20261122T214206Z-977fdc.json, scripts/octo-feather-qa --verdict ... && python3 tests/gate/kit/lane_skills.py demo |
Review verdict: https://github.com/0xTomDaniel/octo-feather/pull/1233#issuecomment-7085862927
Built: acceptance-ticket-skills
Failed: none

Spec calls: 0 calls (0 weakens, 0 adds, 0 clarifies; 0 denied).

