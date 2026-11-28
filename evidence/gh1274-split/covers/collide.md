# Overlap and conflicts before and after the split (#1334)

Two measures: overlap, where two PRs open at the same time changed the same file (whether or not git could merge
them), and conflict, where a real merge of main into a lane conflicted (git merge-tree). Commands: README.md.

## Overlap (director's addition)

A PR of the 60 overlaps when another PR whose open interval overlaps its own (createdAt to
mergedAt, else closedAt, else the fetch time) changed a file it changed too. Before: files as recorded. After: the
hub's hunks placed on the split modules, as (c') and (c'') in counts.md.

Caveats:
- PR #79 is left out: it has been open since 2026-10-22, and its diff from today's merge base (51 files) is not what
  it touched while the 60 were open. With it the numbers are: all files 53 overlapped, 310 pairs before and 300 after;
  scripts/ only 29 overlapped, 115 pairs before and 89 after.
- The open PRs' files are their diff from their merge base with origin/main as of the fetch.
- Bookkeeping files (qc.toml, the status, calls and spec files, .basedpyright/baseline.json) overlap in most PRs, so
  the share of PRs that overlap does not move. The scripts/ rows and the per-file tables show what the split changes:
  scripts/octo-feather-lane drops from 100 overlap pairs to 25 (dispatcher), and its hunks spread over the modules.

PRs measured: the 60 merged in prs.json; others: every PR whose interval overlaps theirs (71 with files, fetched 2026-11-28T09:46:20Z); left out: [79].

| files | view | PRs of the 60 that overlapped | median overlapping PRs per PR | overlap pairs (PR, other PR) |
|---|---|---|---|---|
| all | before | 52 | 4 | 275 |
| all | c' | 52 | 3 | 265 |
| all | c'' | 52 | 3 | 265 |
| scripts/ | before | 28 | 0 | 113 |
| scripts/ | c' | 28 | 0 | 87 |
| scripts/ | c'' | 28 | 0 | 87 |

Top overlapping files, before: | file | overlap pairs through it | PRs of the 60 overlapping through it |
|---|---|---|
| scripts/octo-feather-lane | 100 | 21 |
| qc.toml | 80 | 18 |
| docs/specs/issue-lifecycle.status.json | 61 | 18 |
| .basedpyright/baseline.json | 45 | 11 |
| docs/specs/issue-lifecycle.spec.html | 40 | 13 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 32 | 14 |
| justfile | 31 | 11 |
| docs/specs/issue-lifecycle.calls.jsonl | 26 | 9 |
| tests/gate/kit/testkit/herdr.py | 22 | 8 |
| pyproject.toml | 19 | 9 |
| tests/gate/kit/herdr_messaging.py | 19 | 10 |
| docs/specs/comms.calls.jsonl | 18 | 9 |
| docs/specs/comms.spec.html | 18 | 9 |
| docs/specs/comms.status.json | 17 | 9 |
| .agents/skills/verify-octo-feather/features/README.md | 15 | 7 |
| agents/director.md | 14 | 6 |
| tests/gate/kit/lane_archive_teardown.py | 14 | 5 |
| tests/gate/kit/lane_merge.py | 14 | 5 |
| tests/gate/kit/testkit/__init__.py | 13 | 7 |
| .agents/skills/herdr-comms/SKILL.md | 12 | 8 |

Top overlapping files, c': | file | overlap pairs through it | PRs of the 60 overlapping through it |
|---|---|---|
| qc.toml | 80 | 18 |
| docs/specs/issue-lifecycle.status.json | 61 | 18 |
| .basedpyright/baseline.json | 45 | 11 |
| docs/specs/issue-lifecycle.spec.html | 40 | 13 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 32 | 14 |
| justfile | 31 | 11 |
| scripts/lane_ticketing.py | 29 | 13 |
| docs/specs/issue-lifecycle.calls.jsonl | 26 | 9 |
| scripts/post_merge.py | 26 | 9 |
| scripts/octo-feather-lane | 25 | 10 |
| scripts/lane_reporting.py | 22 | 9 |
| tests/gate/kit/testkit/herdr.py | 22 | 8 |
| scripts/merge_ask.py | 20 | 9 |
| pyproject.toml | 19 | 9 |
| scripts/lane_review.py | 19 | 8 |
| tests/gate/kit/herdr_messaging.py | 19 | 10 |
| docs/specs/comms.calls.jsonl | 18 | 9 |
| docs/specs/comms.spec.html | 18 | 9 |
| docs/specs/comms.status.json | 17 | 9 |
| scripts/lane_reflection.py | 16 | 7 |

Top overlapping files, c'': | file | overlap pairs through it | PRs of the 60 overlapping through it |
|---|---|---|
| qc.toml | 80 | 18 |
| docs/specs/issue-lifecycle.status.json | 61 | 18 |
| .basedpyright/baseline.json | 45 | 11 |
| docs/specs/issue-lifecycle.spec.html | 40 | 13 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 32 | 14 |
| justfile | 31 | 11 |
| scripts/lane_ticketing.py | 29 | 13 |
| docs/specs/issue-lifecycle.calls.jsonl | 26 | 9 |
| scripts/post_merge.py | 26 | 9 |
| scripts/octo-feather-lane | 25 | 10 |
| scripts/lane_reflection.py | 22 | 8 |
| scripts/lane_reporting.py | 22 | 9 |
| tests/gate/kit/testkit/herdr.py | 22 | 8 |
| scripts/merge_ask.py | 20 | 9 |
| pyproject.toml | 19 | 9 |
| scripts/lane_review.py | 19 | 8 |
| tests/gate/kit/herdr_messaging.py | 19 | 10 |
| docs/specs/comms.calls.jsonl | 18 | 9 |
| docs/specs/comms.spec.html | 18 | 9 |
| docs/specs/comms.status.json | 17 | 9 |

## Conflicts (architecture shaper's addition)

conflicts.py, which reuses the shaper's conflicts2.py and reproduces its 225 merges, 59 conflicted and 117 files.
"other" covers the files outside the shaper's buckets.

How the split replay works and its caveats:
- Hunks are mapped to split modules by function (covers.py Split.hunks). The codemod is not run on old trees: it
  checks its tables against main 95353ff3 and refuses defs it does not know.
- A pair of touching hunks still conflicts after the split when both sides land in a common split file. A hunk that
  spans an import block places on every module holding one of its lines, so a "no" can overstate what is left.
- What the 5 hub conflicts were, read from merge-tree's markers:
  - 4 of 5 sit in the hub's top-level import block, where each side added an import for a different command group
    (8aeeadc0 also hits the shared bindings and a regex constant).
  - 20e1025c also conflicts inside ticket_notes' caller (lane_ticketing on both sides).
  - None is in the help text.
- After the split, imports live with the module that uses them. That is why 3 of the 5 come apart under (c').
  20e1025c and 8aeeadc0 keep a conflict in a function both sides edited (lane_ticketing, post_merge).
- The other 4 scripts/ conflicts (merge_ask.py 2, octo-feather-gate 1, octo-feather-qa 1) are in files the split
  leaves as they are, so they stand.


Merges since 2026-11-12 in origin/main's history off its first-parent line, replayed from their parents.

| kind | merges | with a real conflict | conflicted files |
|---|---|---|---|
| main | 225 | 59 (26%) | 117 |
| integrate | 436 | 33 (8%) | 61 |

Conflicted files, main merges, by kind: tests/ 38, *.calls.jsonl 25, other 18, verify skill 12, scripts/ 9, specs 7, status 5, qc.toml 2, .basedpyright/baseline.json 1

Conflicted files, integrate merges, by kind: scripts/ 22, tests/ 16, verify skill 8, qc.toml 6, other 6, specs 1, status 1, .basedpyright/baseline.json 1

scripts/ conflicts in merges of main into a lane, replayed against the split (e9e16e570896; hunks placed by function, as the docstring says):

| merge | file | conflicting hunk pairs | split files ours / theirs, (c') | avoided, (c') | avoided, (c'') |
|---|---|---|---|---|---|
| 984866f05c89 | scripts/octo-feather-gate | - | file unchanged by the split | no | no |
| f14ae1cceef1 | scripts/merge_ask.py | - | file unchanged by the split | no | no |
| dfbedf126b37 | scripts/merge_ask.py | - | file unchanged by the split | no | no |
| 8aeeadc0ba8e | scripts/octo-feather-lane | 7 | octo-feather-lane / lane_review.py; lane_cli.py / ci_start.py lane_review.py; octo-feather-lane / merge_ask.py; ci_start.py lane_cli.py lane_reflection.py lane_reporting.py lane_review.py lane_ticketing.py merge_ask.py octo-feather-lane pi_sessions.py post_merge.py start_lane.py / ci_start.py lane_cli.py lane_reflection.py lane_reporting.py lane_review.py lane_ticketing.py merge_ask.py octo-feather-lane pi_sessions.py post_merge.py start_lane.py; octo-feather-lane / ci_start.py lane_cli.py lane_reflection.py lane_reporting.py lane_review.py lane_ticketing.py merge_ask.py octo-feather-lane pi_sessions.py post_merge.py start_lane.py; post_merge.py / post_merge.py; post_merge.py / post_merge.py | no: ci_start.py, lane_cli.py, lane_reflection.py, lane_reporting.py, lane_review.py, lane_ticketing.py, merge_ask.py, octo-feather-lane, pi_sessions.py, post_merge.py, start_lane.py; octo-feather-lane; post_merge.py | no: ci_start.py, lane_cli.py, lane_reflection.py, lane_reporting.py, lane_review.py, lane_ticketing.py, merge_ask.py, octo-feather-lane, pi_sessions.py, post_merge.py, start_lane.py; merge_ask.py; post_merge.py |
| b14248dca94f | scripts/octo-feather-lane | 1 | octo-feather-lane / lane_reflection.py lane_reporting.py lane_ticketing.py post_merge.py | yes | no: lane_reflection.py |
| c2af5955c656 | scripts/octo-feather-lane | 1 | lane_review.py / lane_reflection.py lane_reporting.py lane_ticketing.py post_merge.py | yes | yes |
| 20e1025cd804 | scripts/octo-feather-lane | 3 | lane_reflection.py lane_reporting.py lane_ticketing.py post_merge.py / lane_cli.py lane_reflection.py lane_ticketing.py octo-feather-lane post_merge.py; lane_reflection.py lane_reporting.py lane_ticketing.py post_merge.py / octo-feather-lane; lane_ticketing.py / lane_ticketing.py | no: lane_reflection.py, lane_ticketing.py, post_merge.py; lane_ticketing.py | no: lane_reflection.py, lane_ticketing.py, post_merge.py; lane_ticketing.py |
| fce3781bcaa8 | scripts/octo-feather-lane | 1 | lane_review.py / octo-feather-lane | yes | yes |
| 1d90581ab59b | scripts/octo-feather-qa | - | file unchanged by the split | no | no |

Of 9 scripts/ conflicts, 5 in the hub; the split would have avoided 3 with (c') placement, 2 with (c'').

## Before and after #1335

Overlap pairs, c'': all files 265 before #1335, 265 after; scripts/: 87 before, 85 after; through
scripts/merge_ask.py 20 before, 16 after. The table, its command and its full output: counts.md (Before and after #1335),
collide-after-1335.md.
