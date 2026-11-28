# Why (b) makes more criteria stale than (a) (#1334, director's addition)

Commands: README.md. (b) here is covers from coverage on main's tree f7f16367, plus each declared path coverage cannot
see, against (a), the covers as declared at f7f16367, over the 60 PRs in prs.json. Probe: for each file (b) adds, up
to 3 criteria that gained it had their proof run again on main's tree with line data (probe-main-f7f163676186.json).
Called means a line of work in that file ran: a function or method body, or a script's top-level code (why.py
work_lines). Loaded only means that only its imports, defs, classes, assignments, import guards or docstring ran.

Summary:
- Stale pairs over the 60 PRs: (a) 1539, (b) 2379.
- Extra pairs by the added file's verdict, where a pair counts once for each added file reaching it: real
  dependency 1432, incidental load 62. The declared covers missed the real dependencies: the verify driver
  (31 criteria, 350 extra pairs), the hub for 15 criteria not declaring it (282), testkit/__init__.py (39, 215),
  pi-role (52, 119: tracker_calls loads it by path and calls tracker_skill), merge_ask.py (34, 66),
  eval_grading.py (47, 65), slot_queue.py (41, 65), tracker_calls.py (33, 37).
- Incidental loads: post_merge.py (40 criteria, 37 pairs) and correction_lanes.py (35, 11). The pre-split hub imports
  them and no function in them runs in the proof. Fixture stubs (tests/fixtures/*/pi, herdr) and the template
  packages' __init__.py are loaded the same way and bring few pairs.
- Dropped (declared Python paths the proof does not run): the hub from 5 criteria (82 pairs) and the verify driver
  from 12 (71 pairs). Those criteria are proven by tagged tests that do not drive them.

Caveats: a probe runs one proof per criterion (its first tagged item, or its demo), while (b) is the union over all
its tagged items, so "1 not run" can appear. The probe ran on main's tree only.

Stale (PR, criterion) pairs over the 60 PRs: (a) 1539, (b) 2379.

Files (b) adds, by the extra stale pairs they bring (pairs stale in (b), not in (a), that file among the changed files reaching the covers; a pair with two such files counts for each).

| file | criteria (b) adds it to | extra stale pairs | probe verdict |
|---|---|---|---|
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 31 | 350 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/octo-feather-lane | 15 | 282 | real dependency (3 called, 0 loaded only, of 3 probes) |
| tests/gate/kit/testkit/__init__.py | 39 | 215 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/pi-role | 52 | 119 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/merge_ask.py | 34 | 66 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/eval_grading.py | 47 | 65 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/slot_queue.py | 41 | 65 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/post_merge.py | 40 | 37 | incidental load (0 called, 3 loaded only, of 3 probes) |
| scripts/tracker_calls.py | 33 | 37 | real dependency (3 called, 0 loaded only, of 3 probes) |
| .agents/skills/herdr-comms/assets/herdr_scope.py | 14 | 31 | real dependency (3 called, 0 loaded only, of 3 probes) |
| tests/gate/kit/testkit/gh.py | 16 | 28 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/octo-feather-gate | 14 | 27 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/octo-feather-qa | 10 | 20 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/octo-feather-spec-status | 13 | 19 | real dependency (3 called, 0 loaded only, of 3 probes) |
| tests/gate/kit/testkit/herdr.py | 5 | 15 | real dependency (2 called, 0 loaded only, 1 not run, of 3 probes) |
| scripts/octo-feather-reflect | 10 | 14 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/check-gate-free | 20 | 13 | real dependency (3 called, 0 loaded only, of 3 probes) |
| tests/gate/kit/testkit/systemd.py | 13 | 12 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/correction_lanes.py | 35 | 11 | incidental load (0 called, 3 loaded only, of 3 probes) |
| scripts/octo-feather-handoff | 10 | 10 | real dependency (3 called, 0 loaded only, of 3 probes) |
| tests/fixtures/install-check/pi | 8 | 8 | incidental load (0 called, 3 loaded only, of 3 probes) |
| templates/python/tests/conftest.py | 5 | 6 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/octo-feather-qc | 2 | 6 | real dependency (2 called, 0 loaded only, of 2 probes) |
| scripts/octo-feather-slot | 2 | 6 | real dependency (2 called, 0 loaded only, of 2 probes) |
| tests/gate/kit/testkit/realcase.py | 8 | 5 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/check-vendored | 4 | 4 | real dependency (3 called, 0 loaded only, of 3 probes) |
| tests/gate/kit/herdr_messaging.py | 1 | 4 | real dependency (1 called, 0 loaded only, of 1 probes) |
| tests/fixtures/herdr-say/herdr | 3 | 3 | incidental load (0 called, 3 loaded only, of 3 probes) |
| tests/fixtures/herdr-spawn/herdr | 3 | 3 | incidental load (0 called, 3 loaded only, of 3 probes) |
| tests/gate/conftest.py | 2 | 3 | real dependency (2 called, 0 loaded only, of 2 probes) |
| .agents/skills/github-pr/scripts/gh | 2 | 2 | real dependency (2 called, 0 loaded only, of 2 probes) |
| tests/gate/kit/testkit/install_check.py | 2 | 2 | real dependency (2 called, 0 loaded only, of 2 probes) |
| tests/gate/kit/testkit/jsonwalk.py | 2 | 2 | real dependency (2 called, 0 loaded only, of 2 probes) |
| tests/gate/kit/testkit/qc_box.py | 2 | 2 | real dependency (2 called, 0 loaded only, of 2 probes) |
| tests/gate/kit/qc_eval_verdict.py | 1 | 1 | real dependency (1 called, 0 loaded only, of 1 probes) |
| tests/gate/kit/testkit/qc.py | 1 | 1 | real dependency (1 called, 0 loaded only, of 1 probes) |
| scripts/handoff_log.py | 48 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/octo-feather-contract | 35 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/octo-feather-evidence | 29 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| templates/python/src/app/__init__.py | 15 | 0 | incidental load (0 called, 3 loaded only, of 3 probes) |
| evals/fixtures/quote-app-inline/src/app/__init__.py | 14 | 0 | incidental load (0 called, 3 loaded only, of 3 probes) |
| .agents/skills/herdr-comms/assets/herdr_ready.py | 11 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/check-evals | 8 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| tests/fixtures/classify-stub/pi | 8 | 0 | incidental load (0 called, 3 loaded only, of 3 probes) |
| tests/fixtures/qc-judge/pi | 8 | 0 | incidental load (0 called, 3 loaded only, of 3 probes) |
| tests/fixtures/lane-report/gh | 7 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| templates/python/src/app/cli.py | 6 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| templates/python/src/app/core.py | 6 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| tests/gate/kit/lane_start.py | 6 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| scripts/check-behavior-smoke | 5 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| templates/python/scripts/check-languages | 5 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| templates/python/scripts/own-tool-paths | 5 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| templates/python/tests/e2e/conftest.py | 5 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |
| templates/python/tests/test_gate.py | 5 | 0 | real dependency (3 called, 0 loaded only, of 3 probes) |

Declared Python paths (b) drops (coverage does not run them in the proof), by the stale pairs they no longer bring:

| file | criteria | stale pairs only (a) had |
|---|---|---|
| scripts/octo-feather-lane | 5 | 82 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 12 | 71 |
| scripts/octo-feather-qc-sandbox | 9 | 17 |
| scripts/octo-feather-qa | 5 | 10 |
| scripts/octo-feather-reflect | 3 | 9 |
| scripts/tracker_calls.py | 3 | 6 |
| tests/gate/kit/lane_correction.py | 2 | 6 |
| tests/gate/kit/herdr_messaging.py | 1 | 6 |
| tests/gate/kit/testkit/herdr.py | 2 | 5 |
| tests/gate/conftest.py | 3 | 4 |
| scripts/correction_lanes.py | 3 | 3 |
| scripts/octo-feather-handoff | 1 | 2 |
| tests/fixtures/tracker-gh/gh | 1 | 1 |
| tests/gate/kit/lane_skills.py | 1 | 1 |
| tests/gate/kit/testkit/gh.py | 1 | 1 |
| tests/gate/kit/test_start_relaunch.py | 6 | 0 |
| scripts/octo-feather-gate | 4 | 0 |
| scripts/check-templates | 1 | 0 |
| scripts/octo-feather-parent-gone | 1 | 0 |
| scripts/octo-feather-shape | 1 | 0 |
| tests/fixtures/classify-stub/pi | 1 | 0 |
| tests/gate/kit/qc_sandbox_cost.py | 1 | 0 |
| tests/gate/kit/test_qc_sandbox_cost.py | 1 | 0 |

Full list, per criterion: + added, - dropped; per added file probed, its verdict for this criterion.

- comms#acceptance-correction-intake
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather (called)
  + scripts/eval_grading.py (called)
  + scripts/handoff_log.py (called)
  + scripts/merge_ask.py (called)
  + scripts/octo-feather-contract (called)
  + scripts/octo-feather-evidence (called)
  + scripts/pi-role (called)
  + scripts/post_merge.py (loaded only)
  + scripts/slot_queue.py (called)
  + tests/fixtures/classify-stub/pi (loaded only)
  + tests/fixtures/herdr-say/herdr (loaded only)
  + tests/fixtures/herdr-spawn/herdr (loaded only)
  + tests/fixtures/install-check/pi (loaded only)
  + tests/fixtures/qc-judge/pi (loaded only)
  + tests/fixtures/reflection-director (called)
  + tests/fixtures/tracker-gh/gh (called)
- comms#acceptance-director-relaunch
  + .agents/skills/herdr-comms/assets/herdr_ready.py (called)
  + .agents/skills/herdr-comms/assets/herdr_scope.py (called)
  + scripts/correction_lanes.py (loaded only)
  + scripts/eval_grading.py (called)
  + scripts/handoff_log.py (called)
  + scripts/merge_ask.py (called)
  + scripts/octo-feather-lane (called)
  + scripts/octo-feather-reflect (called)
  + scripts/pi-role (called)
  + scripts/post_merge.py (loaded only)
  + scripts/slot_queue.py (called)
  + scripts/tracker_calls.py (called)
  + tests/gate/kit/testkit/__init__.py (called)
  + tests/gate/kit/testkit/systemd.py (called)
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  - tests/gate/kit/test_start_relaunch.py
- comms#acceptance-director-relaunch-busy
  + .agents/skills/herdr-comms/assets/herdr_scope.py (called)
  + scripts/pi-role (called)
  + tests/gate/kit/testkit/__init__.py (called)
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  - tests/gate/kit/test_start_relaunch.py
- comms#acceptance-director-relaunch-own-scope
  + .agents/skills/herdr-comms/assets/herdr_scope.py (called)
  + scripts/pi-role
  + tests/gate/kit/testkit/__init__.py (called)
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  - tests/gate/kit/test_start_relaunch.py
- comms#acceptance-director-relaunch-same-session
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/pi-role
  + tests/gate/kit/testkit/__init__.py
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  - tests/gate/kit/test_start_relaunch.py
- comms#acceptance-director-replace
  + .agents/skills/herdr-comms/assets/herdr_ready.py (called)
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/correction_lanes.py (loaded only)
  + scripts/eval_grading.py (called)
  + scripts/handoff_log.py (called)
  + scripts/merge_ask.py (called)
  + scripts/octo-feather-lane (called)
  + scripts/octo-feather-reflect (called)
  + scripts/pi-role
  + scripts/post_merge.py (loaded only)
  + scripts/slot_queue.py (called)
  + scripts/tracker_calls.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/systemd.py (called)
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  - tests/gate/kit/test_start_relaunch.py
- comms#acceptance-director-replace-outgoing
  + .agents/skills/herdr-comms/assets/herdr_ready.py (called)
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/correction_lanes.py (loaded only)
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-handoff (called)
  + scripts/octo-feather-lane (called)
  + scripts/octo-feather-reflect (called)
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/systemd.py (called)
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  - tests/gate/kit/test_start_relaunch.py
- comms#acceptance-director-worker-resume
  + .agents/skills/herdr-comms/assets/herdr_ready.py
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/handoff_log.py
  + scripts/pi-role
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/realcase.py (called)
  + tests/gate/kit/testkit/systemd.py
- comms#acceptance-parent-gone
  + scripts/handoff_log.py
  + scripts/octo-feather-handoff (called)
  + scripts/octo-feather-queued (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/realcase.py (called)
- comms#acceptance-parent-resumed
  + .agents/skills/herdr-comms/assets/herdr_ready.py
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract (called)
  + scripts/octo-feather-evidence (called)
  + scripts/octo-feather-lane
  + scripts/octo-feather-reflect
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + tests/gate/kit/testkit/systemd.py
- comms#acceptance-queued-completion
  + scripts/handoff_log.py
  + scripts/octo-feather-handoff (called)
  + tests/gate/kit/herdr_messaging.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/realcase.py (called)
- comms#acceptance-real-blocker
  + scripts/check-evals (called)
  + scripts/eval_grading.py
  + scripts/pi-role
  - tests/gate/kit/herdr_messaging.py
- comms#acceptance-reflect-files-correction
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather (called)
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract (called)
  + scripts/octo-feather-evidence (called)
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + tests/fixtures/classify-stub/pi (loaded only)
  + tests/fixtures/herdr-say/herdr (loaded only)
  + tests/fixtures/herdr-spawn/herdr (loaded only)
  + tests/fixtures/install-check/pi (loaded only)
  + tests/fixtures/qc-judge/pi (loaded only)
  + tests/fixtures/reflection-director (called)
- comms#acceptance-reflect-files-route-owner
  + tests/gate/kit/testkit/gh.py (called)
  - scripts/correction_lanes.py
  - scripts/octo-feather-lane
  - scripts/octo-feather-reflect
  - scripts/tracker_calls.py
  - tests/fixtures/tracker-gh/gh
- comms#acceptance-reflect-recurrence-comments
  + tests/gate/kit/testkit/gh.py (called)
  - scripts/correction_lanes.py
  - scripts/octo-feather-lane
  - scripts/octo-feather-reflect
  - scripts/tracker_calls.py
  - tests/gate/kit/lane_correction.py
- comms#acceptance-report-gate-budget
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather (called)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-reflect
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + tests/fixtures/lane-report/gh (called)
  - tests/gate/conftest.py
- comms#acceptance-report-owner-caught-headline
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-reflect
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + tests/fixtures/lane-report/gh (called)
- comms#acceptance-report-skill-reach
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-reflect
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + tests/fixtures/lane-report/gh (called)
- comms#acceptance-result-missing
  + scripts/handoff_log.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
- comms#acceptance-worker-ended
  + .agents/skills/herdr-comms/assets/herdr_ready.py
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/pi-role
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/herdr.py (called)
  + tests/gate/kit/testkit/systemd.py
- issue-lifecycle#acceptance-brownfield-full
  + scripts/pi-role
- issue-lifecycle#acceptance-ci-alongside
  + evals/fixtures/quote-app-inline/src/app/__init__.py (loaded only)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-gate (called)
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py (loaded only)
  + tests/gate/kit/lane_ci_start.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py (called)
- issue-lifecycle#acceptance-ci-status-only
  + evals/fixtures/quote-app-inline/src/app/__init__.py (loaded only)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-gate (called)
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py (loaded only)
  + tests/gate/kit/lane_merge_ask.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
- issue-lifecycle#acceptance-correction-replay-missing
  + evals/fixtures/quote-app-inline/src/app/__init__.py (loaded only)
  + scripts/check-behavior-smoke (called)
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/octo-feather-gate (called)
  + scripts/octo-feather-spec-status (called)
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py (loaded only)
  + tests/gate/kit/lane_correction_replay.py (called)
  + tests/gate/kit/lane_verdict_rounds.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
  + tests/gate/kit/testkit/install_check.py (called)
  + tests/gate/kit/testkit/jsonwalk.py (called)
  + tests/gate/kit/testkit/qc_box.py (called)
  - scripts/octo-feather-qc-sandbox
- issue-lifecycle#acceptance-correction-replay-shown
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/check-behavior-smoke (called)
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/octo-feather-gate
  + scripts/octo-feather-spec-status (called)
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py
  + tests/gate/kit/lane_correction_replay.py (called)
  + tests/gate/kit/lane_verdict_rounds.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
  + tests/gate/kit/testkit/install_check.py (called)
  + tests/gate/kit/testkit/jsonwalk.py (called)
  + tests/gate/kit/testkit/qc_box.py (called)
  - scripts/octo-feather-qc-sandbox
- issue-lifecycle#acceptance-declaration-check-shown
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/octo-feather-gate
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py
  + tests/gate/kit/lane_verdict_rounds.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
- issue-lifecycle#acceptance-integrate-checkpoint
  + scripts/pi-role
- issue-lifecycle#acceptance-integrate-fast
  + scripts/pi-role
- issue-lifecycle#acceptance-lane-start
  + .agents/skills/herdr-comms/assets/herdr_ready.py
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-handoff
  + scripts/octo-feather-reflect
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + tests/gate/kit/lane_start.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/systemd.py
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
- issue-lifecycle#acceptance-lane-start-current-kit
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + tests/gate/kit/lane_start.py (called)
  + tests/gate/kit/testkit/__init__.py
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  - tests/gate/kit/testkit/gh.py
  - tests/gate/kit/testkit/herdr.py
- issue-lifecycle#acceptance-lane-start-exists
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + tests/gate/kit/lane_start.py (called)
  + tests/gate/kit/testkit/__init__.py
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
- issue-lifecycle#acceptance-lane-start-files
  + .agents/skills/herdr-comms/assets/herdr_ready.py
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-handoff
  + scripts/octo-feather-reflect
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + tests/gate/kit/lane_start.py
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/herdr.py (called)
  + tests/gate/kit/testkit/systemd.py
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
- issue-lifecycle#acceptance-lane-start-rerun
  + .agents/skills/herdr-comms/assets/herdr_ready.py
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-handoff
  + scripts/octo-feather-queued (not measured)
  + scripts/octo-feather-reflect
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + tests/gate/kit/lane_start.py
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/systemd.py
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
- issue-lifecycle#acceptance-lane-start-sub-issue
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + tests/gate/kit/lane_start.py
  + tests/gate/kit/testkit/__init__.py
  - .agents/skills/verify-octo-feather/scripts/verify-octo-feather
- issue-lifecycle#acceptance-merge-ask-full-proof
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py
  + tests/gate/kit/lane_merge_ask.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
- issue-lifecycle#acceptance-merge-ask-gate-budget
  + .agents/skills/github-pr/scripts/gh (called)
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-behavior-smoke (called)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-gate
  + scripts/octo-feather-spec-status (called)
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  - tests/gate/conftest.py
- issue-lifecycle#acceptance-merge-ask-siblings
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/check-behavior-smoke
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-gate
  + scripts/octo-feather-qa (called)
  + scripts/octo-feather-spec-status
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py
  + tests/gate/kit/lane_merge_ask.py (called)
  + tests/gate/kit/lane_merge_order.py (called)
  + tests/gate/kit/qc_eval_verdict.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
  + tests/gate/kit/testkit/qc.py (called)
- issue-lifecycle#acceptance-one-head-hunks
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/octo-feather-gate
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py
  + tests/gate/kit/lane_merge_ask.py
  + tests/gate/kit/lane_merge_ask_hunks.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
- issue-lifecycle#acceptance-pilot-full
  + scripts/pi-role
- issue-lifecycle#acceptance-pilot-pr
  + scripts/check-gate-free (called)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-gate
  + scripts/octo-feather-qa (called)
  + scripts/octo-feather-spec-status
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
- issue-lifecycle#acceptance-reflection-missed-lane
  + tests/gate/kit/testkit/gh.py
  - scripts/correction_lanes.py
  - scripts/octo-feather-lane
  - scripts/octo-feather-reflect
  - scripts/tracker_calls.py
  - tests/gate/kit/lane_correction.py
- issue-lifecycle#acceptance-review-resolution
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-gate
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + tests/gate/kit/lane_ci_start.py (called)
  + tests/gate/kit/lane_review_resolution.py (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
- issue-lifecycle#acceptance-revision-invalid
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/pi-role
- issue-lifecycle#acceptance-revision-preserve
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/pi-role
- issue-lifecycle#acceptance-revision-remove
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/pi-role
- issue-lifecycle#acceptance-revision-repeat
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/pi-role
- issue-lifecycle#acceptance-ticket-skills
  + scripts/check-evals (called)
  + scripts/eval_grading.py
  + scripts/pi-role
  - scripts/octo-feather-handoff
  - scripts/octo-feather-lane
  - tests/gate/kit/lane_skills.py
  - tests/gate/kit/testkit/herdr.py
- issue-lifecycle#acceptance-tier-three-waits
  + scripts/check-evals (called)
  + scripts/pi-role
- issue-lifecycle#acceptance-verdict-covers-lane
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/octo-feather-gate
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/src/app/__init__.py
  + tests/gate/kit/lane_verdict_rounds.py
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
- issue-lifecycle#acceptance-writer-route-lane
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + tests/fixtures/classify-stub/pi (loaded only)
  + tests/fixtures/herdr-say/herdr (loaded only)
  + tests/fixtures/herdr-spawn/herdr (loaded only)
  + tests/fixtures/install-check/pi (loaded only)
  + tests/fixtures/qc-judge/pi (loaded only)
  + tests/fixtures/reflection-director (called)
  + tests/fixtures/tracker-gh/gh (called)
- quality#acceptance-built-links
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free (called)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-lane
  + scripts/octo-feather-qa (called)
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
- quality#acceptance-evidence-stale
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free (called)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-lane
  + scripts/octo-feather-qa
  + scripts/octo-feather-qc (called)
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
- quality#acceptance-fast-affected
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-dashes (called)
  + scripts/check-gate-free
  + scripts/check_rules.py (called)
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/pi-role
  + tests/gate/conftest.py (called)
  + tests/gate/heavy_slot.py (called)
  + tests/gate/kit/conftest.py (loaded only)
  + tests/gate/test_gate.py (called)
- quality#acceptance-fast-diff-base
  + tests/gate/kit/testkit/__init__.py
  - scripts/octo-feather-gate
- quality#acceptance-fast-map-behind
  + tests/gate/kit/testkit/__init__.py
  - scripts/octo-feather-gate
- quality#acceptance-fast-map-slot-free
  + scripts/handoff_log.py
  + scripts/octo-feather-handoff
  + tests/gate/kit/testkit/__init__.py
  - scripts/octo-feather-gate
- quality#acceptance-map-after-merge
  + scripts/octo-feather-slot (called)
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
  + tests/gate/kit/testkit/herdr.py (not measured)
  + tests/gate/kit/testkit/realcase.py
  + tests/gate/kit/testkit/systemd.py
  + tests/lib/no-packages.py (called)
  - scripts/octo-feather-gate
- quality#acceptance-map-build-failed
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
  + tests/gate/kit/testkit/herdr.py
  + tests/gate/kit/testkit/realcase.py
  + tests/gate/kit/testkit/systemd.py
- quality#acceptance-map-full-daily
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/gh.py
  + tests/gate/kit/testkit/herdr.py
  + tests/gate/kit/testkit/realcase.py
  + tests/gate/kit/testkit/systemd.py
- quality#acceptance-one-execution-incomplete
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free
  + scripts/eval_grading.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-gate
  + scripts/octo-feather-spec-status
  - scripts/octo-feather-qc-sandbox
- quality#acceptance-qa-analyst
  + scripts/check-evals
  + scripts/pi-role
  + tests/fixtures/classify-stub/pi
  + tests/fixtures/install-check/pi
  + tests/fixtures/qc-judge/pi
  - scripts/octo-feather-qa
- quality#acceptance-qa-baseline
  + scripts/check-evals
  + scripts/pi-role
  + tests/fixtures/classify-stub/pi
  + tests/fixtures/install-check/pi
  + tests/fixtures/qc-judge/pi
  - scripts/octo-feather-qa
- quality#acceptance-qa-cost
  + scripts/check-evals
  + scripts/pi-role
  + tests/fixtures/classify-stub/pi
  + tests/fixtures/install-check/pi
  + tests/fixtures/qc-judge/pi
  - scripts/octo-feather-qa
- quality#acceptance-qa-history
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free
  + scripts/eval_grading.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-qc (called)
  + scripts/octo-feather-slot (called)
  + scripts/pi-role
  + scripts/slot_queue.py
- quality#acceptance-qa-repeats
  + scripts/check-evals
  + scripts/pi-role
  + tests/fixtures/classify-stub/pi
  + tests/fixtures/install-check/pi
  + tests/fixtures/qc-judge/pi
  - scripts/octo-feather-qa
- quality#acceptance-qa-review
  + scripts/pi-role
  + tests/fixtures/classify-stub/pi
  + tests/fixtures/install-check/pi
  + tests/fixtures/qc-judge/pi
  - scripts/octo-feather-qa
- quality#acceptance-qc-advisory
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-lane
  + scripts/octo-feather-spec-status
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  - tests/fixtures/classify-stub/pi
- quality#acceptance-qc-capture
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-lane
  + scripts/octo-feather-qa
  + scripts/octo-feather-spec-status
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  - scripts/octo-feather-qc-sandbox
- quality#acceptance-qc-capture-browser
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-lane
  + scripts/octo-feather-qa
  + scripts/octo-feather-spec-status
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  - scripts/octo-feather-qc-sandbox
- quality#acceptance-qc-carry
  + scripts/check-gate-free
  + scripts/eval_grading.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-qa
  + scripts/pi-role
  + tests/gate/conftest.py (called)
  + tests/gate/test_gate.py (called)
- quality#acceptance-qc-fallback
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free
  + scripts/eval_grading.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-qa
  + scripts/octo-feather-spec-status
  - scripts/octo-feather-lane
  - scripts/octo-feather-qc-sandbox
- quality#acceptance-qc-insufficient
  + .agents/skills/github-pr/scripts/gh (called)
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-behavior-smoke
  + scripts/check-gate-free
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-gate
  + scripts/octo-feather-spec-status
  + scripts/pi-role
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  - scripts/octo-feather-qc-sandbox
- quality#acceptance-qc-same-verdict
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-lane
  + scripts/octo-feather-qa
  + scripts/octo-feather-spec-status
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  - scripts/octo-feather-qc-sandbox
- quality#acceptance-qc-sandbox-cost
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  - scripts/octo-feather-qc-sandbox
  - tests/gate/kit/qc_sandbox_cost.py
  - tests/gate/kit/test_qc_sandbox_cost.py
- roles#acceptance-codemode-every-role
  + .agents/skills/herdr-comms/assets/herdr_ready.py
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/check-roles (called)
  + scripts/handoff_log.py
  + scripts/octo-feather-handoff
- roles#acceptance-fresh-independent-worker
  + .agents/skills/herdr-comms/assets/herdr_ready.py
  + .agents/skills/herdr-comms/assets/herdr_scope.py
  + scripts/handoff_log.py
  + scripts/octo-feather-handoff
  + scripts/pi-role
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/realcase.py
  + tests/gate/kit/testkit/systemd.py
- roles#acceptance-general-worker-no-implementation
  + scripts/check-evals
  + scripts/eval_grading.py
  + scripts/pi-role
- roles#acceptance-shaper-launch
  + scripts/check-gate-free
  - scripts/octo-feather-shape
- roles#acceptance-task-worker-route
  + scripts/handoff_log.py
  + scripts/octo-feather-handoff
  + tests/gate/kit/testkit/__init__.py
  + tests/gate/kit/testkit/realcase.py
  - scripts/octo-feather-parent-gone
- skills#acceptance-launch-refuses-unloaded
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-skills (called)
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
- skills#acceptance-only-listed
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
- skills#acceptance-skill-frontmatter
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/pi-role
- templates#acceptance-edge-rejects
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + scripts/check-gate-free
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + templates/python/src/app/__init__.py
  + templates/python/src/app/cli.py (called)
  + templates/python/src/app/core.py (called)
- templates#acceptance-fresh-fast
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/check-gate-free
  + scripts/check-vendored (called)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-lane
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/scripts/check-languages (called)
  + templates/python/scripts/own-tool-paths (called)
  + templates/python/src/app/__init__.py
  + templates/python/src/app/cli.py (called)
  + templates/python/src/app/core.py (called)
  + templates/python/tests/conftest.py (called)
  + templates/python/tests/e2e/conftest.py (called)
  + templates/python/tests/integration/conftest.py (loaded only)
  + templates/python/tests/test_gate.py (called)
  + tests/fixtures/lane-report/gh
  + tests/gate/kit/testkit/__init__.py
- templates#acceptance-same-gate
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/check-gate-free
  + scripts/check-vendored (called)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-lane
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/scripts/check-languages (called)
  + templates/python/scripts/own-tool-paths (called)
  + templates/python/src/app/__init__.py
  + templates/python/src/app/cli.py (called)
  + templates/python/src/app/core.py (called)
  + templates/python/tests/conftest.py (called)
  + templates/python/tests/e2e/conftest.py (called)
  + templates/python/tests/integration/conftest.py (loaded only)
  + templates/python/tests/test_gate.py (called)
  + tests/fixtures/lane-report/gh
  + tests/gate/kit/testkit/__init__.py
  - scripts/check-templates
- templates#acceptance-shared-fixture
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/check-gate-free
  + scripts/check-vendored (called)
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-lane
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/scripts/check-languages (called)
  + templates/python/scripts/own-tool-paths (called)
  + templates/python/src/app/__init__.py
  + templates/python/src/app/cli.py
  + templates/python/src/app/core.py
  + templates/python/tests/conftest.py (called)
  + templates/python/tests/e2e/conftest.py (called)
  + templates/python/tests/test_gate.py (called)
  + tests/fixtures/lane-report/gh
  + tests/gate/kit/testkit/__init__.py
- templates#acceptance-starter-acceptance-test
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/check-gate-free
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-gate
  + scripts/octo-feather-lane
  + scripts/octo-feather-qa
  + scripts/octo-feather-spec-status
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/scripts/check-languages
  + templates/python/scripts/own-tool-paths
  + templates/python/src/app/__init__.py
  + templates/python/src/app/cli.py
  + templates/python/src/app/core.py
  + templates/python/tests/conftest.py
  + templates/python/tests/e2e/conftest.py
  + templates/python/tests/e2e/test_cli_e2e.py (loaded only)
  + templates/python/tests/integration/conftest.py (loaded only)
  + templates/python/tests/integration/test_cli.py (loaded only)
  + templates/python/tests/test_gate.py
  + tests/gate/kit/testkit/__init__.py
  - tests/gate/conftest.py
- templates#acceptance-test-kinds
  + .agents/skills/verify-octo-feather/scripts/verify-octo-feather
  + evals/fixtures/quote-app-inline/src/app/__init__.py
  + scripts/check-gate-free
  + scripts/check-vendored
  + scripts/correction_lanes.py
  + scripts/eval_grading.py
  + scripts/handoff_log.py
  + scripts/merge_ask.py
  + scripts/octo-feather-contract
  + scripts/octo-feather-evidence
  + scripts/octo-feather-lane
  + scripts/post_merge.py
  + scripts/slot_queue.py
  + scripts/tracker_calls.py
  + templates/python/scripts/check-languages
  + templates/python/scripts/own-tool-paths
  + templates/python/src/app/__init__.py
  + templates/python/src/app/cli.py
  + templates/python/src/app/core.py
  + templates/python/tests/conftest.py
  + templates/python/tests/e2e/conftest.py
  + templates/python/tests/integration/conftest.py
  + templates/python/tests/test_gate.py
  + tests/fixtures/lane-report/gh
  + tests/gate/kit/testkit/__init__.py
