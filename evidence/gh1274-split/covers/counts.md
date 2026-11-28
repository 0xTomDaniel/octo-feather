# Stale counts (a), (b), (c), (c'), (c'') (#1334)

Made 2026-11-28 by the commands in README.md: main f7f16367 (its map: the post-merge build at f7f16367), split tree
e9e16e57 (its map: `just fast-map` at e9e16e57, 423 passed, 379 mapped, 0 not passed); measures
measure-main-f7f163676186.json and measure-e9e16e570896.json; PRs prs.json (fetched 2026-11-28). (b) and (c) are
coverage's Python files plus every declared path coverage cannot see (any non-Python file or directory).

Not measured, so covers kept as declared in (b) and (c): the 4 model-eval entries, which have no command and no test
(comms#acceptance-no-routine-traffic, roles#acceptance-supervisor-delegates-execution, roles#acceptance-delegated-pr,
comms#acceptance-autonomous-local), and quality#acceptance-qc-sandbox-maintained and quality#acceptance-one-execution,
whose tagged items (test_qc_sandbox_gone.py x3, test_qc_one_execution.py::test_two_specs) did not pass under the
coverage run on either tree. On main the result-file demo failed (exit 1), so comms#acceptance-result-file keeps its
declared covers in (b) only.

Lane-command files alone: a stale pair counts when every changed file that reaches the criterion's covers is a
lane-command file (the sets are printed below the table).

Built criteria with covers: (a) 95, (b) 95, (c) 95. PRs: 60 merged, #962..#1313, 2026-11-17..2026-11-28.

| covers set | PR #1246 (lane gh1234) | median | p90 | max | stale (PR, criterion) pairs | of them through lane-command files alone |
|---|---|---|---|---|---|---|
| (a) declared, main | 58 | 23.5 | 51 | 62 | 1539 | 564 (37%) |
| (b) coverage, main tree | 72 | 43.5 | 70 | 88 | 2379 | 427 (18%) |
| (c) coverage, split tree | 72 | 43.5 | 70 | 88 | 2340 | 453 (19%) |
| (c') split tree, hub hunks placed, unplaced to the dispatcher | 72 | 40.5 | 70 | 88 | 2148 | 261 (12%) |
| (c'') split tree, hub hunks placed, unplaced by nearest context or dropped | 72 | 38 | 70 | 88 | 2134 | 247 (12%) |

Lane-command files: before the split scripts/merge_ask.py, scripts/octo-feather-lane, scripts/post_merge.py, scripts/start_lane.py; after it the hub and scripts/ci_start.py, scripts/lane_cli.py, scripts/lane_reflection.py, scripts/lane_reporting.py, scripts/lane_review.py, scripts/lane_ticketing.py, scripts/merge_ask.py, scripts/pi_sessions.py, scripts/post_merge.py, scripts/start_lane.py. A pair counts when every changed file reaching its covers is one.

(a) declared, main: top triggers. | file | criteria listing it | PRs changing it (of 60) | stale pairs it reaches | pairs it alone reaches |
|---|---|---|---|---|
| scripts/octo-feather-lane | 33 | 23 | 759 | 523 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 16 | 15 | 240 | 151 |
| tests/gate/kit/testkit/herdr.py | 19 | 9 | 171 | 86 |
| justfile | 9 | 14 | 126 | 88 |
| tests/gate/kit/herdr_messaging.py | 8 | 10 | 80 | 26 |
| agents/supervisor.md | 14 | 5 | 70 | 31 |
| scripts/octo-feather-qc | 15 | 4 | 60 | 32 |
| scripts/merge_ask.py | 9 | 6 | 54 | 0 |
| scripts/octo-feather-qa | 12 | 4 | 48 | 33 |
| scripts/octo-feather-qc-sandbox | 11 | 4 | 44 | 23 |
| scripts/tracker_calls.py | 13 | 3 | 39 | 0 |
| tests/gate/kit/testkit/gh.py | 6 | 6 | 36 | 12 |
| scripts/octo-feather-gate | 11 | 3 | 33 | 8 |
| scripts/pi-role | 7 | 4 | 28 | 20 |
| .agents/skills/herdr-comms/assets/herdr-say | 12 | 2 | 24 | 4 |

(b) coverage, main tree: top triggers. | file | criteria listing it | PRs changing it (of 60) | stale pairs it reaches | pairs it alone reaches |
|---|---|---|---|---|
| scripts/octo-feather-lane | 43 | 23 | 989 | 322 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 35 | 15 | 525 | 266 |
| tests/gate/kit/testkit/__init__.py | 39 | 9 | 351 | 153 |
| scripts/merge_ask.py | 43 | 6 | 258 | 0 |
| scripts/pi-role | 59 | 4 | 236 | 131 |
| tests/gate/kit/testkit/herdr.py | 22 | 9 | 198 | 34 |
| scripts/eval_grading.py | 51 | 3 | 153 | 24 |
| scripts/slot_queue.py | 45 | 3 | 135 | 42 |
| scripts/post_merge.py | 43 | 3 | 129 | 0 |
| scripts/tracker_calls.py | 43 | 3 | 129 | 0 |
| justfile | 9 | 14 | 126 | 77 |
| tests/gate/kit/testkit/gh.py | 21 | 6 | 126 | 34 |
| .agents/skills/herdr-comms/assets/herdr_scope.py | 17 | 6 | 102 | 10 |
| tests/gate/kit/herdr_messaging.py | 8 | 10 | 80 | 10 |
| agents/supervisor.md | 14 | 5 | 70 | 30 |

(c) coverage, split tree: top triggers. | file | criteria listing it | PRs changing it (of 60) | stale pairs it reaches | pairs it alone reaches |
|---|---|---|---|---|
| scripts/octo-feather-lane | 43 | 23 | 989 | 365 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 35 | 15 | 525 | 266 |
| tests/gate/kit/testkit/__init__.py | 39 | 9 | 351 | 169 |
| scripts/pi-role | 59 | 4 | 236 | 131 |
| scripts/merge_ask.py | 37 | 6 | 222 | 0 |
| tests/gate/kit/testkit/herdr.py | 22 | 9 | 198 | 34 |
| scripts/tracker_calls.py | 43 | 3 | 129 | 0 |
| justfile | 9 | 14 | 126 | 77 |
| tests/gate/kit/testkit/gh.py | 21 | 6 | 126 | 34 |
| .agents/skills/herdr-comms/assets/herdr_scope.py | 17 | 6 | 102 | 10 |
| tests/gate/kit/herdr_messaging.py | 8 | 10 | 80 | 10 |
| scripts/eval_grading.py | 24 | 3 | 72 | 16 |
| agents/supervisor.md | 14 | 5 | 70 | 30 |
| scripts/octo-feather-qa | 17 | 4 | 68 | 17 |
| scripts/octo-feather-qc | 17 | 4 | 68 | 25 |

(c') split tree, hub hunks placed, unplaced to the dispatcher: top triggers. | file | criteria listing it | PRs changing it (of 60) | stale pairs it reaches | pairs it alone reaches |
|---|---|---|---|---|
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 35 | 15 | 525 | 280 |
| scripts/octo-feather-lane | 43 | 11 | 473 | 53 |
| scripts/merge_ask.py | 37 | 11 | 407 | 33 |
| scripts/lane_reporting.py | 36 | 11 | 396 | 23 |
| tests/gate/kit/testkit/__init__.py | 39 | 9 | 351 | 188 |
| scripts/lane_cli.py | 43 | 6 | 258 | 0 |
| scripts/pi-role | 59 | 4 | 236 | 142 |
| tests/gate/kit/testkit/herdr.py | 22 | 9 | 198 | 34 |
| scripts/tracker_calls.py | 43 | 3 | 129 | 37 |
| justfile | 9 | 14 | 126 | 77 |
| tests/gate/kit/testkit/gh.py | 21 | 6 | 126 | 34 |
| scripts/pi_sessions.py | 13 | 8 | 104 | 0 |
| .agents/skills/herdr-comms/assets/herdr_scope.py | 17 | 6 | 102 | 10 |
| scripts/lane_reflection.py | 10 | 8 | 80 | 0 |
| tests/gate/kit/herdr_messaging.py | 8 | 10 | 80 | 10 |

(c'') split tree, hub hunks placed, unplaced by nearest context or dropped: top triggers. | file | criteria listing it | PRs changing it (of 60) | stale pairs it reaches | pairs it alone reaches |
|---|---|---|---|---|
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 35 | 15 | 525 | 280 |
| scripts/octo-feather-lane | 43 | 10 | 430 | 39 |
| scripts/merge_ask.py | 37 | 11 | 407 | 33 |
| scripts/lane_reporting.py | 36 | 11 | 396 | 23 |
| tests/gate/kit/testkit/__init__.py | 39 | 9 | 351 | 188 |
| scripts/lane_cli.py | 43 | 7 | 301 | 0 |
| scripts/pi-role | 59 | 4 | 236 | 142 |
| tests/gate/kit/testkit/herdr.py | 22 | 9 | 198 | 34 |
| scripts/tracker_calls.py | 43 | 3 | 129 | 37 |
| justfile | 9 | 14 | 126 | 77 |
| tests/gate/kit/testkit/gh.py | 21 | 6 | 126 | 46 |
| scripts/pi_sessions.py | 13 | 8 | 104 | 0 |
| .agents/skills/herdr-comms/assets/herdr_scope.py | 17 | 6 | 102 | 10 |
| scripts/lane_reflection.py | 10 | 9 | 90 | 0 |
| tests/gate/kit/herdr_messaging.py | 8 | 10 | 80 | 10 |

Per PR: number, (a), (b), (c), (c'), (c'')
1246 58 72 72 72 72
1313 22 54 54 54 54
1324 25 79 79 79 79
1269 60 74 74 74 74
1268 19 33 33 33 33
1309 7 59 59 59 59
1301 20 26 26 26 26
1302 9 63 55 55 55
1281 9 9 9 9 9
1246 58 72 72 72 72
1282 0 0 0 0 0
1270 0 0 0 0 0
1265 38 48 48 48 48
1264 0 0 0 0 0
1242 44 49 49 43 43
1248 0 0 0 0 0
1245 28 43 43 43 43
1153 57 70 70 70 70
1238 35 45 45 5 5
1212 51 65 65 60 60
1223 43 58 58 52 52
1233 33 44 44 37 37
1216 33 43 43 0 0
1160 17 24 24 24 24
1209 7 9 9 9 9
1195 16 35 35 35 35
1166 50 72 72 72 72
1164 33 43 43 43 43
1145 48 56 56 27 27
1190 25 42 48 48 48
1123 53 66 66 58 58
1184 19 61 61 61 61
1173 0 4 4 4 4
1171 33 43 43 0 0
1165 0 0 0 0 0
1118 44 58 58 58 58
1010 28 55 55 55 55
1124 9 9 9 9 9
1126 11 52 15 15 15
1021 60 88 88 88 88
1100 51 65 65 65 65
1098 0 0 0 0 0
1086 62 81 81 81 81
1101 15 17 17 17 17
1003 11 11 11 11 11
1072 15 22 22 22 22
1008 45 56 56 56 56
1005 43 48 48 48 48
1073 5 19 19 19 19
1024 16 17 17 17 17
1023 26 47 47 47 47
1017 43 58 58 58 58
1006 15 25 25 25 25
1016 11 2 2 2 2
984 44 59 59 54 54
983 0 39 39 39 39
981 2 2 2 2 2
982 8 23 23 23 23
958 42 49 49 49 49
967 8 42 42 42 42
962 33 46 46 46 32

## Before and after #1335 (merge_ask.py's shared helpers moved to pr_git.py, pr_report.py, gate_time.py)

Made 2026-11-28 by README.md's counts command, the same main, (b) measure and PRs; before: split e9e16e57 with
measure-e9e16e570896.json (this file's table above, reproduced exactly); after: split 9e96c717 with
measure-a17be240e5d0.json (`just fast-map` at a17be240: 424 passed, 380 mapped; test_replace_none timed out under
coverage, run by regen as a tagged item). On the after tree covers.py's Split places each PR's merge_ask.py hunks
too, among merge_ask.py and the shared modules alone (its text went nowhere else), as it places the hub's. Full
output: counts-after-1335.md.

| covers set | | PR #1246 | median | p90 | max | stale pairs | through lane-command files alone |
|---|---|---|---|---|---|---|---|
| (c) coverage | before #1335 | 72 | 43.5 | 70 | 88 | 2340 | 453 |
| (c) coverage | after #1335 | 72 | 43.5 | 70 | 88 | 2340 | 454 |
| (c') hub hunks placed, unplaced to the dispatcher | before #1335 | 72 | 40.5 | 70 | 88 | 2148 | 261 |
| (c') + merge_ask.py hunks placed | after #1335 | 72 | 40.5 | 70 | 88 | 2127 | 241 |
| (c'') hub hunks placed, unplaced by nearest context or dropped | before #1335 | 72 | 38 | 70 | 88 | 2134 | 247 |
| (c'') + merge_ask.py hunks placed | after #1335 | 72 | 37 | 70 | 88 | 2113 | 227 |

(c'') triggers that moved: scripts/merge_ask.py listed by 37 criteria, 407 stale pairs, before; by 11, 99 pairs,
after. scripts/lane_reporting.py by 36, 396 pairs, before; by 25, 275 pairs, after (merge-ask no longer loads it).
scripts/gate_time.py, new, by 36, 324 pairs: merge_ask.py imports it, so every merge-ask criterion still covers it;
scripts/pr_git.py by 13, 104 pairs; scripts/pr_report.py below the top 15.

Collisions (collide.md's command, after: --split 9e96c717, merge_ask.py hunks placed the same way; full output
collide-after-1335.md): all files 265 pairs before #1335, 265 after (52 PRs, median 3, both); scripts/ 87 before,
85 after (28 PRs, median 0, both); merge_ask.py 20 pairs (9 PRs) before, 16 (8 PRs) after.
