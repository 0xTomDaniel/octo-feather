# Stale counts (a), (b), (c) (#1334)

Made 2026-11-28 by the commands in README.md: main f7f16367 (its map: the post-merge build at f7f16367), split tree
e9e16e57 (its map: `just fast-map` at e9e16e57, 423 passed, 379 mapped, 0 not passed); measures
measure-main-f7f163676186.json and measure-e9e16e570896.json; PRs prs.json (fetched 2026-11-28). Command:

    uv run --locked --offline --no-sync python3 evidence/gh1274-split/covers/covers.py counts \
      --main f7f1636761867209bdc1a0d90d586a65188a6bab --b evidence/gh1274-split/covers/measure-main-f7f163676186.json \
      --split e9e16e570896c680abe3ceb76bcd177eb1f5d432 --c evidence/gh1274-split/covers/measure-e9e16e570896.json \
      --prs evidence/gh1274-split/covers/prs.json --pr 1246

Not measured, covers kept as declared in (b) and (c): the 4 model-eval entries (no command, no test:
comms#acceptance-no-routine-traffic, roles#acceptance-supervisor-delegates-execution, roles#acceptance-delegated-pr,
comms#acceptance-autonomous-local), and quality#acceptance-qc-sandbox-maintained, quality#acceptance-one-execution,
whose tagged items (test_qc_sandbox_gone.py x3, test_qc_one_execution.py::test_two_specs) did not pass under the
coverage run, on both trees. On main, the result-file demo failed (exit 1), so comms#acceptance-result-file kept its
declared covers in (b) only.

Built criteria with covers: (a) 95, (b) 95, (c) 95. PRs: 60 merged, #962..#1313, 2026-11-17..2026-11-28.

| covers set | PR #1246 (lane gh1234) | median | p90 | max |
|---|---|---|---|---|
| (a) declared, main | 58 | 23.5 | 51 | 62 |
| (b) coverage, main tree | 71 | 43 | 66 | 88 |
| (c) coverage, split tree | 71 | 43 | 66 | 88 |
| (c') coverage, split tree, hub hunks placed | 71 | 37.5 | 65 | 87 |

Paths in the most built criteria's covers, (a): scripts/octo-feather-lane 33, tests/gate/kit/testkit/herdr.py 19, .agents/skills/verify-octo-feather/scripts/verify-octo-feather 16, scripts/octo-feather-qc 15, agents/supervisor.md 14, scripts/tracker_calls.py 13, .agents/skills/herdr-comms/assets/herdr-say 12, scripts/octo-feather-qa 12, scripts/correction_lanes.py 11, scripts/octo-feather-gate 11, scripts/octo-feather-qc-sandbox 11, scripts/octo-feather-start 10

Paths in the most built criteria's covers, (b): scripts/pi-role 59, scripts/handoff_log.py 52, scripts/eval_grading.py 51, scripts/slot_queue.py 45, scripts/correction_lanes.py 43, scripts/merge_ask.py 43, scripts/octo-feather-lane 43, scripts/post_merge.py 43, scripts/tracker_calls.py 43, tests/gate/kit/testkit/__init__.py 39, scripts/octo-feather-contract 37, scripts/octo-feather-evidence 37

Paths in the most built criteria's covers, (c): scripts/pi-role 59, scripts/handoff_log.py 53, scripts/correction_lanes.py 43, scripts/lane_cli.py 43, scripts/octo-feather-lane 43, scripts/tracker_calls.py 43, tests/gate/kit/testkit/__init__.py 39, scripts/octo-feather-contract 38, scripts/octo-feather-evidence 38, scripts/merge_ask.py 37, scripts/lane_reporting.py 36, .agents/skills/verify-octo-feather/scripts/verify-octo-feather 35

Per PR: number, (a), (b), (c), (c')
1246 58 71 71 71
1313 22 54 54 54
1324 25 79 79 79
1269 60 72 72 72
1268 19 29 29 29
1309 7 59 59 59
1301 20 24 24 24
1302 9 63 55 55
1281 9 0 0 0
1246 58 71 71 71
1282 0 0 0 0
1270 0 0 0 0
1265 38 48 48 48
1264 0 0 0 0
1242 44 49 49 43
1248 0 0 0 0
1245 28 35 35 35
1153 57 65 65 65
1238 35 43 43 0
1212 51 61 61 56
1223 43 58 58 52
1233 33 43 43 36
1216 33 43 43 0
1160 17 23 23 23
1209 7 9 9 9
1195 16 35 35 35
1166 50 70 70 70
1164 33 43 43 43
1145 48 55 55 26
1190 25 40 46 46
1123 53 66 66 58
1184 19 60 60 60
1173 0 4 4 4
1171 33 43 43 0
1165 0 0 0 0
1118 44 51 50 50
1010 28 50 50 50
1124 9 1 1 1
1126 11 48 11 11
1021 60 88 88 87
1100 51 58 58 58
1098 0 0 0 0
1086 62 81 81 81
1101 15 17 17 17
1003 11 0 0 0
1072 15 13 13 13
1008 45 48 47 47
1005 43 48 48 48
1073 5 17 17 17
1024 16 13 13 13
1023 26 46 46 46
1017 43 58 58 58
1006 15 23 23 23
1016 11 2 2 2
984 44 59 59 54
983 0 39 39 39
981 2 0 0 0
982 8 23 23 23
958 42 44 44 44
967 8 42 42 42
962 33 46 46 46
