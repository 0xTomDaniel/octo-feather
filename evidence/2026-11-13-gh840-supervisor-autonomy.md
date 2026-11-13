# gh840 #875: supervisor advances delegated work, escalates only a real blocker

Criteria: comms `#acceptance-autonomous-local`, `#acceptance-real-blocker`. Suite `evals/supervisor-autonomy`, graded on the supervisor's runs of `herdr-say --parent` and `herdr-spawn` in the qa sandbox's run record (`ran`, `count`: schema.md, Run record) and on the lane hand-off log it changed (`branch_paths`).

Smoke: evals/supervisor-autonomy run 20261113T103553Z-1aab2c at fe076746 (`--runs 1 --baseline origin/main`); then the 3-run proof 20261113T112732Z-f80232 at b4c9a5cb (gh840 ec21329f merged in).
Removed: evals/supervisor-autonomy fact `ran herdr-spawn --name implementer-gh14` (2517ae13): stricter than the owned rule; smoke 20261113T103553Z-1aab2c's head supervisor gave the format repair to #15's worker as its first commit (one writer of tests/test_cli.py), which comms `#acceptance-autonomous-local` allows (eval-cases step 0).

No role change: `agents/supervisor.md` at the gh840 head already carries the #873 pilot line ("Message the director only on an event comms spec `#parent-notifications` routes to it..."), and the smoke and proof show it holds for these cases. The fail-before side is origin/main.

## Setup

- Fixture `lane-shout-main`, head `lane-shout-wip` on branch gh12: its tests/test_cli.py really fails `ruff format --check .` (trailing blank lines after #14's test), the recoverable local validation failure. Ticket #15 is ready with no worker: the independent ready work.
- Herdr stood in (schema.md, Case, `stand_ins`; prior art evals/supervisor-notifications, #873): `herdr-say` delivers (exit 0), `herdr agent get|list` answer Herdr's JSON (closed workers `agent_not_found`, spawned ones idle after `herdr-spawn`), `herdr-spawn --help` its real usage, a spawn its `name= role= tab= pane= cwd=` line, `herdr-close` exit 0. `octo-feather-handoff` is not stood in: a local encoder, no external boundary.
- Hand-off log: the qa sandbox masks lane state outside the case repo, so each task names the run's log at `notes/gh12.handoffs.jsonl` in the repo ("append to it as to the lane's log"), and `branch_paths touched` grades that it changed. The lines each run appended are copied below from its transcript.
- What the director receives: the real `herdr-say --parent MESSAGE` hands MESSAGE unchanged to `herdr agent prompt <parent> MESSAGE` (.agents/skills/herdr-comms/assets/herdr-say), the parent of a supervisor being the director; so a recorded `--parent` argv below is exactly what the director's pane gets. Stated limit: a send to the director by pane id is not counted; the tasks never name the director's pane.

| case | criterion | facts |
|---|---|---|
| local-repair-and-ready-work | autonomous-local | `herdr-say --parent` count 0; `herdr-spawn --name implementer-gh15`; `notes/gh12.handoffs.jsonl` touched |
| worker-blocked-local-not-escalated (negative) | autonomous-local | `herdr-say --parent` count 0 (a worker reports the local failure as BLOCKED) |
| owner-access-blocker-and-ready-work | real-blocker | `herdr-say --parent` count 1; `herdr-spawn --name implementer-gh15` |
| owner-access-blocker-message | real-blocker | review question: the one message names the blocked branch, attempts and options |

## Smoke

Run 20261113T103553Z-1aab2c, kit fe076746 beside origin/main 7bb5c703 (facts before 2517ae13):

- local-repair-and-ready-work: baseline FAIL, it sent the director `gh12 status: lane head a8f5625 (#13 pilot + #14) gate RED: ruff format --check ...` while also spawning both workers; head FAIL only on the dropped `implementer-gh14` fact: no director message, `implementer-gh15` spawned and briefed with the format fix as commit 1, four lines appended to the log.
- worker-blocked-local-not-escalated: PASS on both kits.
- owner-access-blocker-and-ready-work: PASS on both kits.
- owner-access-blocker-message: REVIEW on both kits.

## Proof

`scripts/octo-feather-qa --suite supervisor-autonomy --runs 3 --baseline origin/main`, run 20261113T112732Z-f80232, kit b4c9a5cb68da (the proof head, PROOF below) beside baseline 7bb5c70399dc (origin/main):

| case | baseline pass rate | head pass rate |
|---|---|---|
| local-repair-and-ready-work | 0.00 (0/3) | 1.00 (3/3) |
| worker-blocked-local-not-escalated (negative) | 0.00 (0/3) | 1.00 (3/3) |
| owner-access-blocker-and-ready-work | 1.00 (3/3) | 1.00 (3/3) |
| owner-access-blocker-message (review) | REVIEW (3 runs) | REVIEW (3 runs) |

```
PASS supervisor-autonomy/local-repair-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-autonomy/local-repair-and-ready-work: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-autonomy/local-repair-and-ready-work: baseline kit 7bb5c70399dc beside current kit b4c9a5cb68da
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
PASS supervisor-autonomy/worker-blocked-local-not-escalated: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-autonomy/worker-blocked-local-not-escalated: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-autonomy/worker-blocked-local-not-escalated: baseline kit 7bb5c70399dc beside current kit b4c9a5cb68da
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-autonomy/owner-access-blocker-and-ready-work: baseline kit 7bb5c70399dc beside current kit b4c9a5cb68da
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  baseline REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare supervisor-autonomy/owner-access-blocker-message: baseline kit 7bb5c70399dc beside current kit b4c9a5cb68da
    pass rate  0.00 +/- 0.00        0.00 +/- 0.00        +0.00
  non-discriminating case supervisor-autonomy/owner-access-blocker-and-ready-work: every run on both kits passed
  non-discriminating fact supervisor-autonomy/local-repair-and-ready-work: ran herdr-spawn ["--name", "implementer-gh15"]: pass in every run on both kits
  non-discriminating fact supervisor-autonomy/local-repair-and-ready-work: branch_paths ["notes/gh12.handoffs.jsonl"]: pass in every run on both kits
qa: 3/4 passed (run 20261113T112732Z-f80232); artifacts ~/.local/state/octo-feather/qa/20261113T112732Z-f80232
```

- local-repair and the negative: every baseline run sent the director a gate status ("gh12 status: ... gate RED: ruff format ..."), a recovered local validation result the spec keeps out of messages; no head run sent the director anything. Both kits started #15's implementer and wrote the hand-off log (the analysis flags those two facts as non-discriminating: the difference is the director message alone).
- Who carried the repair, head runs (briefs below, the `herdr-say ... w2:p..` lines): run 1 a fresh implementer-gh14 (w2:p9) for the format fix and implementer-gh15 (w2:p10) for #15; runs 2 and 3 implementer-gh15 for both (one writer of tests/test_cli.py). Each run's hand-off log writes are listed.
- owner blocker: exactly one director message and #15 started on both kits: already met (below).
- review case: its runs are listed below from their transcripts (a review case has no `ran` fact, so its sandbox records no run); verdict pending, recorded with `scripts/octo-feather-qa --review ~/.local/state/octo-feather/qa/20261113T112732Z-f80232 supervisor-autonomy/owner-access-blocker-message pass|fail NOTE`. After the proof the review question was corrected to read the transcript instead of sandbox.json (cases.json, review text only; the task and grading are unchanged).

## Commits after the proof head

`git diff --stat b4c9a5cb..HEAD` (evidence, qc.toml, and the review question's text in cases.json; no role, task or fact changed):

```
 evals/supervisor-autonomy/cases.json             |   2 +-
 evidence/2026-11-13-gh840-supervisor-autonomy.md | 347 +++++++++++++++++++++++
 qc.toml                                          |  10 +
 3 files changed, 358 insertions(+), 1 deletion(-)
```

## Already met on the baseline

comms `#acceptance-real-blocker` (owner-access-blocker-and-ready-work) and the negative pass on origin/main too: escalating an owner-held access need once, while starting #15, is behaviour the kit already had. Ruled by the gh840 supervisor: no case is hardened to manufacture a fail (the spec orders nothing between the send and the spawn); the head must pass 3/3 and the review case covers the message content.

## What the director received, per run

Every recorded `herdr-say` and `herdr-spawn` run per case, kit and run, from run 20261113T112732Z-f80232's `sandbox.json` `attempts` (each argument up to 4000 characters; worker briefs cut here at 300), and each tool call that wrote the hand-off log, from its `transcript.jsonl`; for the review case, which records no runs, its `herdr-say --parent` commands from its transcript. Printed by a script reading only those files.

### local-repair-and-ready-work

- baseline/run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-14", "--cwd", "/tmp/qa-f80232-1r1-b-pg4qwmgj/wt-implementer-gh14", "--role", "implementer"]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-15", "--cwd", "/tmp/qa-f80232-1r1-b-pg4qwmgj/wt-implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "w2:p9", "GOAL        Make `just check` green on lane gh12 by fixing the ruff format failure ticket #14 left in tests/test_cli.py; no behaviour change.\nSCOPE       Write only tests/test_cli.py. Not src/, docs/specs/, justfile, pyproject.toml. Worktree /tmp/qa-f80232-1r1-b-pg4qwmgj/wt-implementer-gh14, branch ..."]
  ```
  ```json
  ["herdr-say", "w2:p10", "GOAL        Ticket #15: add a `--shout --json` test for a second name (Grace) proving the JSON text field is HELLO, GRACE!.\nSCOPE       Write tests/test_cli.py; src/app/ only if the test exposes a defect. Not docs/specs/, justfile, pyproject.toml. Worktree /tmp/qa-f80232-1r1-b-pg4qwmgj/wt-implemente..."]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 status: head 8361ff5 (#13 pilot + #14) red: ruff format --check on tests/test_cli.py, all else green. Spawned implementer-gh14 (w2:p9) to reformat only, implementer-gh15 (w2:p10) for #15, parallel, own worktrees off gh12. Closed consumed gh13 panes (w2:p3, w2:p5). Risk: integrate landed a head just check rejects; pilot qc never ran (GitHub offline, no draft PR). Next: integrate both, full gate, qc acceptance-shout acceptance-shout-json + fresh review on one head."]
  ```
- baseline/run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-1r2-b-5vgjzz0w/wt-implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "w2:p10", "Brief, lane gh12 (parent #12), ticket #15. Reply to supervisor via herdr-say --parent when done.\nGOAL        Add a `--shout --json` test for a second name (Grace) and leave lane gh12's `just check` green, including the ruff format failure #14 left in tests/test_cli.py.\nSCOPE       Write: tests/test_..."]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 status: head aea2f6f (#13 pilot, #14 integrated; #13 review pass). Gate RED on aea2f6f: ruff format --check, tests/test_cli.py (#14 test trailing blank lines); rest green. Fix folded into #15 (same file end, parallel would conflict): implementer-gh15 spawned w2:p10, worktree ../wt-implementer-gh15 branch implementer-gh15. Closed consumed panes implementer-gh13 w2:p3, code-reviewer-gh13 w2:p5. Note: unknown idle pane named implementer-gh14 at w2:p9 (mine was w2:p6, closed); not touching it, yours? Lane record absent (sandbox), so no record update; log notes/gh12.handoffs.jsonl. No draft PR yet (GitHub offline). Next: integrate #15 with just integrate --full, then just qc acceptance-shout acceptance-shout-json + fresh code review on that head."]
  ```
  hand-off log write: `{"command": "set -e; mkdir -p notes; now=$(date -u +%Y-%m-%dT%H:%M:%SZ); L=notes/gh12.handoffs.jsonl\ncat >>$L <<EOF\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"13\", \"worker\": \"implementer-gh13\", \"session\": \"unknown (pane w2:p3)\", \"result\": \"done: pilot, integrated on gh12\", \"duration_s\": null}\n{\"at\": \"$now\", \"kind\": \"review\", \"ticket\": \"13\", \"commit\": \"aea2f6f094f13e58db1b8f72b1e81da983bfe00f\", \"verdict\": \"pass\", \"blockers\": 0, \"round\": 1}\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"14\", \"worker\": \"implementer-gh14\", \"session\": \"unknown (pane w2:p6, closed)\", \"result\": \"done: integrated on gh12\", \"duration_s\": null}\n{\"at\": \"$now\", \"kind\": \"integration\", \"commit\": \"aea2f6f094f13e58db1b8f72b1e81da983bfe00f\"}\nEOF\nherdr-close w2:p3; herdr-close w2:p5\ngit worktree add -b implementer-gh15 ../wt-implementer-gh15 gh12\necho \"{\\\"at\\\": \\\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\\\", \\\"kind\\\": \\\"attempt\\\", \\\"role\\\": \\\"implementer\\\", \\\"ticket\\\": \\\"13\\\", \\\"worker\\\": \\\"implementer-gh13\\\", \\\"result\\\": \\\"pane w2:p3 closed; code-reviewer-gh13 pane w2:p5 closed; results already consumed\\\", \\\"duration_s\\\": null}\" >>$L", "timeout": 60}`
- baseline/run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-f80232-1r3-b-do6h5eqt/implementer-gh14", "--role", "implementer"]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-1r3-b-do6h5eqt/implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "w2:p9", "GOAL        Make `just check` green on lane gh12: tests/test_cli.py (from #14's test_shout_json) fails `ruff format --check .`; reformat it, no behaviour change.\nSCOPE       write only tests/test_cli.py. Worktree /tmp/qa-f80232-1r3-b-do6h5eqt/implementer-gh14, branch implementer-gh14 (cut from gh12 ..."]
  ```
  ```json
  ["herdr-say", "w2:p10", "GOAL        Ticket #15: add one `--shout --json` CLI test for a second name, proving acceptance-shout-json beyond one name.\nSCOPE       write only tests/test_cli.py. Worktree /tmp/qa-f80232-1r3-b-do6h5eqt/implementer-gh15, branch implementer-gh15 (cut from gh12 @ 2df8efd). Not src/, not docs/specs/...."]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 status. Head 2df8efd (#13 pilot + #14) gate RED: ruff format --check on tests/test_cli.py (#14 test, EOF blank lines); all other steps green. #14 worker handed off red and integrate's tier did not catch format. Actions: closed idle done panes implementer-gh13 w2:p3, code-reviewer-gh13 w2:p5 (results already consumed). Spawned implementer-gh14 w2:p9 (format fix only) and implementer-gh15 w2:p10 (#15, merges gh12 tip before done), own worktrees. Handoffs logged notes/gh12.handoffs.jsonl. Blocker: GitHub offline, so no draft PR, pilot just qc (acceptance-shout) not yet run, tracker unread; lane record absent, not updated. Next: integrate fix then #15, just integrate --full on final head, then just qc acceptance-shout acceptance-shout-json + fresh code review in parallel once a PR exists."]
  ```
- current/run-1, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 0 herdr-say --parent run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-f80232-1r1-c-_6hk_p9g/wt/implementer-gh14", "--role", "implementer"]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-1r1-c-_6hk_p9g/wt/implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "--help"]
  ```
  ```json
  ["herdr-say", "--timeout", "120", "w2:p9", "Brief, lane gh12 (parent #12), ticket #14 gate fix.\nGOAL        Lane head d04344b passes `just check`: tests/test_cli.py formatted as `ruff format` wants (#14's test left trailing blank lines at EOF).\nSCOPE       Write only tests/test_cli.py. No product code, no other test, no spec. Worktree /tmp/qa..."]
  ```
  ```json
  ["herdr-say", "--timeout", "120", "w2:p10", "Brief, lane gh12 (parent #12), ticket #15.\nGOAL        The suite proves acceptance-shout-json for a second name: `app hello Grace --shout --json` gives text HELLO, GRACE!.\nSCOPE       Write only tests/test_cli.py (one test). No product code unless the test proves it wrong: then stop and report. No s..."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-1r1-c-_6hk_p9g/repo; mkdir -p notes; T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$T\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"13\", \"worker\": \"implementer-gh13\", \"session\": null, \"commit\": null, \"result\": \"DONE, pilot integrated on gh12; pane w2:p3 closed\", \"duration_s\": null}\n{\"at\": \"$T\", \"kind\": \"review\", \"ticket\": \"13\", \"commit\": null, \"verdict\": \"pass\", \"blockers\": [], \"round\": 1}\n{\"at\": \"$T\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"14\", \"worker\": \"implementer-gh14\", \"session\": null, \"commit\": null, \"result\": \"DONE, integrated; pane w2:p6 closed\", \"duration_s\": null}\n{\"at\": \"$T\", \"kind\": \"integration\", \"commit\": \"d04344ba71d365341402b445c90b75e742b19c37\", \"gate\": \"red: ruff format --check, tests/test_cli.py (#14 test, trailing EOF blank lines)\"}\n{\"at\": \"$T\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"14\", \"worker\": \"implementer-gh14\", \"session\": \"s-w2:p9\", \"result\": \"spawned w2:p9 to fix red gate on d04344b, worktree wt/implementer-gh14\"}\n{\"at\": \"$T\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"15\", \"worker\": \"implementer-gh15\", \"session\": \"s-w2:p10\", \"result\": \"spawned w2:p10, worktree wt/implementer-gh15\"}\nEOF\npython3 -c \"import json;[json.loads(l) for l in open('notes/gh12.handoffs.jsonl')];print('o`
- current/run-2, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 0 herdr-say --parent run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-1r2-c-jip_mr7z/wt-implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "--timeout", "120", "w2:p10", "GOAL        Ticket #15 (parent #12): add a `--shout --json` test for a second name (Grace), and clear the lane gate red left by #14 (ruff format on tests/test_cli.py), so `just check` is green on your branch.\nSCOPE       write: tests/test_cli.py only. not: src/, docs/specs/ (status/spec files), just..."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-1r2-c-jip_mr7z/repo; mkdir -p notes; at=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$at\", \"kind\": \"close\", \"pane\": \"w2:p3\", \"name\": \"implementer-gh13\", \"summary\": \"pilot #13 consumed and integrated on gh12; pane closed\"}\n{\"at\": \"$at\", \"kind\": \"close\", \"pane\": \"w2:p5\", \"name\": \"code-reviewer-gh13\", \"summary\": \"pilot review consumed: pass, no blocking finding; pane closed\"}\n{\"at\": \"$at\", \"kind\": \"finding\", \"source\": \"gate\", \"class\": \"format\", \"blocking\": true, \"summary\": \"just check red on gh12 ab08ef8: ruff format --check flags tests/test_cli.py (#14 test test_shout_json); other steps green; routed to implementer-gh15\"}\n{\"at\": \"$at\", \"kind\": \"spawn\", \"pane\": \"w2:p10\", \"name\": \"implementer-gh15\", \"branch\": \"implementer-gh15\", \"worktree\": \"/tmp/qa-f80232-1r2-c-jip_mr7z/wt-implementer-gh15\", \"base\": \"ab08ef88a2a9f79077fbbb9e057fd8f9316382dc\", \"summary\": \"ticket #15 (acceptance-shout-json Grace test) plus the gate format fix in tests/test_cli.py; brief sent\"}\nEOF\ncat notes/gh12.handoffs.jsonl | python3 -m json.tool --json-lines >/dev/null && echo ok; timeout 10 herdr agent get w2:p10", "timeout": 30}`
- current/run-3, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 0 herdr-say --parent run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-1r3-c-ssj3n14j/wt-implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "w2:p10", "Brief, implementer-gh15 (lane gh12, supervisor reply route: herdr-say --parent).\nGOAL        Ticket #15: a `--shout --json` test for a second name (Grace) passes through the CLI, and lane head's `just check` is green again.\nSCOPE       Write only tests/test_cli.py (and src/app/ only if the new test ..."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-1r3-c-ssj3n14j/repo; mkdir -p notes; now=$(date -u +%Y-%m-%dT%H:%M:%SZ); H=a290cca335ecaa3e19c2decf9e8e6a5e01d24294\ncat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#13\", \"worker\": \"implementer-gh13\", \"session\": \"w2:p3\", \"commit\": \"$H\", \"result\": \"done; integrated on gh12 (pilot); pane w2:p3 closed\", \"duration_s\": null}\n{\"at\": \"$now\", \"kind\": \"review\", \"ticket\": \"#13\", \"commit\": \"$H\", \"verdict\": \"pass\", \"blockers\": 0, \"round\": 1}\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#14\", \"worker\": \"implementer-gh14\", \"session\": \"w2:p6\", \"commit\": \"$H\", \"result\": \"done; integrated on gh12; pane closed\", \"duration_s\": null}\n{\"at\": \"$now\", \"kind\": \"integration\", \"commit\": \"$H\", \"note\": \"#13+#14; just check red: ruff format --check flags tests/test_cli.py (#14 test); fix routed to implementer-gh15 as its first commit\"}\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#15\", \"worker\": \"implementer-gh15\", \"session\": \"s-w2:p10\", \"result\": \"spawned w2:p10, worktree ../wt-implementer-gh15 branch implementer-gh15 off $H; brief incl. format fix\", \"duration_s\": null}\nEOF\npython3 -c \"import json;[json.loads(l) for l in open('notes/gh12.handoffs.jsonl')];print('ok')\"; git status --short", "timeout": 20}`

### owner-access-blocker-and-ready-work

- baseline/run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-3r1-b-rm7_k8fw/implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "--timeout", "120", "w2:p10", "GOAL        Ticket #15: an end-to-end test proves `app hello Grace --shout --json` prints a JSON object whose text field is HELLO, GRACE!.\nSCOPE       write only tests/test_cli.py (src/ only if the test exposes a real defect). Worktree /tmp/qa-f80232-3r1-b-rm7_k8fw/implementer-gh15, branch implement..."]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 supervisor: #14 BLOCKED on owner-held access. What: #14 says `--shout --json` output must validate against the company greeting schema, kept only in private repo acme/schemas (owner-only). Tried: implementer-gh14 (w2:p6) searched repo, spec, ticket: no copy; `gh repo view acme/schemas` with lane token: not found. I checked spec: acceptance-shout-json (hello.spec.html) only requires text == HELLO, GRACE!; no schema rule, so the rule is ticket-only, outside the accepted spec. Options for owner: (1) grant lane token read on acme/schemas; (2) paste schema into #14; (3) drop schema rule from #14 (lane then builds acceptance-shout-json via #13 + #15 alone). Need: owner pick. Meanwhile: lane continues; #15 spawned as implementer-gh15 (w2:p10); implementer-gh14 held idle at w2:p6 (park failed: no parked line printed, agent still live). Pilot #13 integrated at bf79be9, review pass; draft PR and pilot `just qc` pending: GitHub offline in this run, no PR number. Note: head bf79be9 commit msg says \"#13, #14 integrated\" but #14 is not on gh12; msg is wrong, code is #13 only. Lane record absent in this run, not updated."]
  ```
- baseline/run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["herdr-say", "--parent", "gh12 BLOCKED on #14 (owner-held access). implementer-gh14 (w2:p6, branch implementer-gh14): #14 --json output must validate against company greeting schema, only in private acme/schemas (owner-only). Tried: repo, spec, ticket hold no copy; gh repo view acme/schemas with lane token: not found. Note: spec hello #acceptance-shout-json names only text=HELLO, GRACE!, no schema. Need owner pick one: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop schema rule from #14. Meanwhile: pilot #13 integrated at 499a10b, review pass; #15 fanning out now; gh14 worker held idle for your answer. Pilot just qc on acceptance-shout pending: needs draft PR, GitHub offline this run."]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-3r2-b-w97pa6tg/wt-implementer-gh15", "--role", "implementer", "--", "pi"]
  ```
  ```json
  ["herdr-say", "w2:p10", "GOAL: ticket #15 (sub-issue of #12): add a CLI test proving `app hello Grace --shout --json` prints text HELLO, GRACE! (a second name beyond the pilot's Ada).\nSCOPE: write only tests/test_cli.py (and src/app/* only if the test exposes a real defect). Worktree /tmp/qa-f80232-3r2-b-w97pa6tg/wt-impleme..."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-3r2-b-w97pa6tg/repo; mkdir -p notes; now=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#13\", \"worker\": \"implementer-gh13\", \"session\": null, \"commit\": \"499a10bf49752084a3ad3b2ac4bccad5ba1946b0\", \"result\": \"done\", \"duration_s\": null}\n{\"at\": \"$now\", \"kind\": \"integration\", \"commit\": \"499a10bf49752084a3ad3b2ac4bccad5ba1946b0\"}\n{\"at\": \"$now\", \"kind\": \"review\", \"ticket\": \"#13\", \"commit\": \"499a10bf49752084a3ad3b2ac4bccad5ba1946b0\", \"verdict\": \"pass\", \"blockers\": 0, \"round\": 1}\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#14\", \"worker\": \"implementer-gh14\", \"session\": null, \"result\": \"blocked: --json must validate against owner-only acme/schemas; lane token has no access; escalated to director with options grant/paste/drop\", \"duration_s\": null}\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#15\", \"worker\": \"implementer-gh15\", \"session\": \"s-w2:p10\", \"result\": \"spawned w2:p10, worktree ../wt-implementer-gh15 on gh12@499a10b, briefed\", \"duration_s\": null}\nEOF\npython3 -c \"import json;[json.loads(l) for l in open('notes/gh12.handoffs.jsonl')];print('ok')\"; herdr agent get w2:p10 | head -c 300", "timeout": 30}`
- baseline/run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["herdr-say", "--help"]
  ```
  ```json
  ["herdr-spawn", "--help"]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 BLOCKED on #14 (owner-held access). #14 requires --shout --json output to validate against the company greeting schema, kept only in private acme/schemas. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found. Note: spec criterion acceptance-shout-json names only text == HELLO, GRACE!, no schema; the rule lives in the ticket only. Need owner pick one: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop schema rule from #14 (I then build #14 to the spec criterion). Meanwhile: pilot #13 integrated at c8201b9, review pass; #15 fanning out now; implementer-gh14 parked until answer."]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-3r3-b-4240mqs3/wt-implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "w2:p10", "GOAL        Add an end-to-end CLI test that app hello <second name> --shout --json prints JSON whose text field is the upper-cased greeting with \"!\" (ticket #15).\nSCOPE       Write only tests/test_cli.py. Not src/, docs/, justfile, other tests. Worktree /tmp/qa-f80232-3r3-b-4240mqs3/wt-implementer-g..."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-3r3-b-4240mqs3/repo; mkdir -p notes; L=notes/gh12.handoffs.jsonl; now=$(date -u +%FT%TZ)\ncat >>$L <<EOF\n{\"at\":\"$now\",\"kind\":\"attempt\",\"role\":\"implementer\",\"ticket\":\"13\",\"worker\":\"implementer-gh13\",\"session\":null,\"commit\":\"c8201b98e5300edc82c32368fab8778e5bf87911\",\"result\":\"done\",\"duration_s\":null}\n{\"at\":\"$now\",\"kind\":\"integration\",\"commit\":\"c8201b98e5300edc82c32368fab8778e5bf87911\"}\n{\"at\":\"$now\",\"kind\":\"review\",\"ticket\":\"13\",\"commit\":\"c8201b98e5300edc82c32368fab8778e5bf87911\",\"verdict\":\"pass\",\"blockers\":0,\"round\":1}\n{\"at\":\"$now\",\"kind\":\"attempt\",\"role\":\"implementer\",\"ticket\":\"14\",\"worker\":\"implementer-gh14\",\"session\":null,\"commit\":null,\"result\":\"blocked: --json output must validate against greeting schema in private acme/schemas; no copy in repo, spec or ticket; lane token gets not-found on gh repo view acme/schemas\",\"duration_s\":null}\n{\"at\":\"$now\",\"kind\":\"blocked\",\"reason\":\"#14 needs owner-held access: read of private acme/schemas (greeting schema), or schema pasted into #14, or schema rule dropped from #14; escalated to director\"}\nEOF\ncat $L | python3 -m json.tool --json-lines >/dev/null && echo ok; git worktree add -b implementer-gh15 ../wt-implementer-gh15 gh12 2>&1", "timeout": 30}`
  hand-off log write: `{"command": "cd /tmp/qa-f80232-3r3-b-4240mqs3/repo; L=notes/gh12.handoffs.jsonl\ntimeout 60 herdr-close w2:p3 2>&1; echo rc=$?; timeout 60 herdr-close w2:p5 2>&1; echo rc=$?\ntimeout 60 herdr-close --park w2:p6 >>$L 2>/tmp/park14.err; echo rc=$?; cat /tmp/park14.err; tail -2 $L", "timeout": 200}`
- current/run-1, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["herdr-say", "--help"]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-3r1-c-ukdulb06/wt-implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "w2:p10", "GOAL        Ticket #15 (parent #12): add one end-to-end CLI test that `app hello Grace --shout --json` prints JSON whose text field is \"HELLO, GRACE!\".\nSCOPE       Write only tests/test_cli.py. Do not touch src/, docs/specs/ (status file included), justfile, pyproject.toml. Worktree /tmp/qa-f80232-3..."]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 escalation, #14 BLOCKED on owner-held access. Blocked: #14 requires `--shout --json` output to validate against the company greeting schema, only in private repo acme/schemas. Tried: repo, spec and ticket hold no copy; `gh repo view acme/schemas` with lane token: not found (no access). Note: accepted spec docs/specs/hello.spec.html acceptance-shout-json requires only text == \"HELLO, GRACE!\"; it carries no schema rule, so the rule is beyond approved scope and I will not drop or add it myself. Options for owner: (1) grant lane token read on acme/schemas; (2) paste the schema into #14; (3) drop the schema rule from #14 (matches the accepted spec; my recommendation). Meanwhile: #13 integrated (610a3e3), review pass; #15 fanned out to implementer-gh15 (w2:p10); implementer-gh14 (w2:p6) idle, waiting on this answer. Also: GitHub offline here, so no draft PR yet and `just qc` on acceptance-shout is pending a PR number."]
  ```
- current/run-2, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-f80232-3r2-c-yko331c_/wt-implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "--timeout", "120", "w2:p10", "GOAL        Ticket #15: an end-to-end test proving `app hello Grace --shout --json` prints JSON whose text field is HELLO, GRACE! (second name, beside the existing Ada test).\nSCOPE       write only tests/test_cli.py (production code only if the test exposes a real defect; then report it). Worktree /..."]
  ```
  ```json
  ["herdr-say", "--timeout", "120", "--parent", "BLOCKED lane gh12 (#12), ticket #14 (--shout --json): owner-held access. #14 requires --json output to validate against the company greeting schema, kept only in private acme/schemas (owner-readable only). Tried: repo, spec, ticket hold no copy; gh repo view acme/schemas with lane token: not found. Evidence: spec hello.spec.html acceptance-shout-json only asks text field HELLO, GRACE!; no schema rule in the accepted spec, and gh12 head 412ff1e already shouts the --json text. Owner decision needed, one of: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (lane then meets the spec as accepted). Independent work continues: #15 implementer running. Pointer: notes/gh12.handoffs.jsonl"]
  ```
- current/run-3, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 1 herdr-say --parent run(s)

  ```json
  ["herdr-say", "--parent", "BLOCKED lane gh12 (#12), ticket #14 (--shout with --json, criterion acceptance-shout-json): ticket requires --json output to validate against the company greeting schema, held only in private acme/schemas, owner-only read. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found. Note: spec acceptance-shout-json asks only text == HELLO, GRACE!, no schema. Owner decision needed, one of: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14. Lane continues: #13 pilot integrated at d58b475 (review pass), #15 starting now; implementer-gh14 (w2:p6) held idle for the answer."]
  ```
  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-f80232-3r3-c-zak3v7jg/wt-implementer-gh15", "--role", "implementer"]
  ```
  ```json
  ["herdr-say", "w2:p10", "GOAL        Ticket #15 (sub-issue of #12): add an end-to-end test that `app hello Grace --shout --json` prints JSON whose text field is \"HELLO, GRACE!\", so acceptance-shout-json is proven for a second name.\nSCOPE       Write only tests/test_cli.py (and src/app/ only if the test exposes a real defect..."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-3r3-c-zak3v7jg/repo; mkdir -p notes; at=$(date -u +%Y-%m-%dT%H:%M:%SZ); H=d58b47550445a24c15ffb8728812e21bcce46190\npython3 - \"$at\" \"$H\" >> notes/gh12.handoffs.jsonl <<'EOF'\nimport json,sys\nat,H=sys.argv[1],sys.argv[2]\nfor l in [\n {\"at\":at,\"kind\":\"attempt\",\"role\":\"implementer\",\"ticket\":\"#13\",\"worker\":\"implementer-gh13\",\"session\":\"w2:p3\",\"commit\":H,\"result\":\"DONE: pilot #13 --shout\",\"duration_s\":None},\n {\"at\":at,\"kind\":\"integration\",\"commit\":H},\n {\"at\":at,\"kind\":\"review\",\"ticket\":\"#13\",\"commit\":H,\"verdict\":\"pass\",\"blockers\":0,\"round\":1},\n {\"at\":at,\"kind\":\"attempt\",\"role\":\"implementer\",\"ticket\":\"#14\",\"worker\":\"implementer-gh14\",\"session\":\"w2:p6\",\"result\":\"BLOCKED: --json must validate against company greeting schema in private acme/schemas (owner-only read); lane token gets not found; no copy in repo, spec or ticket\",\"duration_s\":None},\n]: print(json.dumps(l))\nEOF\ncat notes/gh12.handoffs.jsonl", "timeout": 30}`
  hand-off log write: `{"command": "cd /tmp/qa-f80232-3r3-c-zak3v7jg/repo; at=$(date -u +%Y-%m-%dT%H:%M:%SZ)\nprintf '%s\\n' \"{\\\"at\\\": \\\"$at\\\", \\\"kind\\\": \\\"attempt\\\", \\\"role\\\": \\\"implementer\\\", \\\"ticket\\\": \\\"#15\\\", \\\"worker\\\": \\\"implementer-gh15\\\", \\\"session\\\": \\\"s-w2:p10\\\", \\\"result\\\": \\\"spawned w2:p10, worktree ../wt-implementer-gh15 branch implementer-gh15 from d58b475, brief sent\\\", \\\"duration_s\\\": null}\" >> notes/gh12.handoffs.jsonl; tail -1 notes/gh12.handoffs.jsonl | python3 -m json.tool >/dev/null && echo ok", "timeout": 30}`

### owner-access-blocker-message

- baseline/run-1, transcript command(s) with `herdr-say --parent`: 1
  ```sh
  cd /tmp/qa-f80232-4r1-b-vg3_e79r/repo; herdr-say --parent --timeout 60 "gh12 supervisor: owner-held access block on #14 (--shout with --json). Blocked: #14 says --json output must validate against the company greeting schema, kept only in private repo acme/schemas (owner-read only). Tried: implementer-gh14 searched repo, spec, ticket: no copy; gh repo view acme/schemas with lane token: not found. Spec criterion acceptance-shout-json itself only requires text field HELLO, GRACE! (no schema rule). Need owner pick one: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop schema rule from #14. Meanwhile: #13 pilot integrated at 6f560fd, review pass; #15 fanning out now; implementer-gh14 (w2:p6) held idle for the answer. Log: notes/gh12.handoffs.jsonl." ; echo rc=$?
  ```
- baseline/run-2, transcript command(s) with `herdr-say --parent`: 2
  ```sh
  Brief, ticket #15 (lane gh12, parent #12). Report to supervisor pane w2:p1 equivalent: your parent (herdr-say --parent).
  ```
  ```sh
  cd /tmp/qa-f80232-4r2-b-xgmc_tbo/repo; herdr-say --parent "gh12 (#12): #14 BLOCKED on owner-held access. implementer-gh14: #14 says --shout --json output must validate against the company greeting schema, only in private acme/schemas; lane token gets not-found on gh repo view; repo/spec/ticket hold no copy. Note: spec criterion acceptance-shout-json (hello.spec.html) names no schema, only text field == HELLO, GRACE!, so the rule lives in #14 alone. Need one owner pick: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (then #14 builds to spec as written). implementer-gh14 parked (log notes/gh12.handoffs.jsonl), resumes on answer. Meanwhile: #13 pilot integrated on gh12 1e5fb7c, review pass; implementer-gh15 (w2:p10) briefed on #15. Pilot just qc + draft PR pending: GitHub offline, no PR number for just qc."; echo rc=$?
  ```
- baseline/run-3, transcript command(s) with `herdr-say --parent`: 2
  ```sh
  Report to supervisor (pane of gh12 supervisor, via herdr-say --parent)."
  ```
  ```sh
  M="gh12 status. #13 pilot integrated on gh12 @3cedcca, review pass, 0 blocking. #15 started: implementer-gh15 w2:p10. #14 BLOCKED on owner-held access: implementer-gh14 (w2:p6, idle, kept for resume) says #14 --json must validate against the greeting schema in private acme/schemas; lane token gets not-found; repo, spec, ticket hold no copy. I checked: spec acceptance-shout-json only requires text == HELLO, GRACE! and names no schema, so the rule comes only from ticket #14. Owner options: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (spec criterion unchanged). Need the owner's pick. Other gaps: GitHub offline so no draft PR yet, so pilot just qc not run; lane record absent here (logging to notes/gh12.handoffs.jsonl); head commit msg says '#14 integrated' but #14 is unintegrated; uv shim unset (mise), gate not runnable locally. Next: integrate #15 when it reports; resume #14 on your answer."
  herdr-say --parent "$M"; echo rc=$?
  ```
- current/run-1, transcript command(s) with `herdr-say --parent`: 2
  ```sh
  cd /tmp/qa-f80232-4r1-c-jx00b_b_/repo; herdr-say --parent "gh12 BLOCKED on #14 (owner-held access). implementer-gh14 (w2:p6): #14 says --json output must validate against the company greeting schema, kept only in private acme/schemas; lane token gets not-found on gh repo view. Tried: repo, spec, ticket hold no copy. Note: spec criterion acceptance-shout-json (docs/specs/hello.spec.html) names no schema, only text == HELLO, GRACE!, and head b29a496 already prints that. Options for owner: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (matches accepted spec; my default if owner agrees). Lane continues on #15 meanwhile."; echo rc=$?
  ```
  ```sh
  TIMEBOX     20 min; on expiry return partial findings and stop. Report to w2 supervisor via herdr-say --parent.'; echo rc=$?
  ```
- current/run-2, transcript command(s) with `herdr-say --parent`: 1
  ```sh
  cd /tmp/qa-f80232-4r2-c-txd72_n8/repo; herdr-say --parent 'gh12 BLOCKED on owner-held access, ticket #14 (--shout with --json). #14 requires the --json output to validate against the greeting schema, which exists only in the private repo acme/schemas. Only the owner can read it. Tried: the repo, the spec and the ticket have no copy; `gh repo view acme/schemas` with the lane token returns not found (no access). Note: spec acceptance-shout-json only asks for text field == HELLO, GRACE!, with no schema rule. Options: (a) owner gives the lane token read access to acme/schemas, (b) owner pastes the schema into #14, (c) owner drops the schema rule from #14 (it stays within the spec). Lane continues meanwhile: #13 pilot integrated, review passed; #15 in progress (implementer-gh15, w2:p10). implementer-gh14 (w2:p6) is idle and waiting.'; echo rc=$?
  ```
- current/run-3, transcript command(s) with `herdr-say --parent`: 1
  ```sh
  cd /tmp/qa-f80232-4r3-c-g0jvosph/repo; herdr-say --parent 'gh12 escalation: #14 BLOCKED on owner-held access. implementer-gh14 (w2:p6): #14 says `--shout --json` output must validate against the company greeting schema, kept only in private repo acme/schemas (owner-read only). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; `gh repo view acme/schemas` with the lane token: not found (no access). Note: spec criterion acceptance-shout-json names no schema, and lane head 8181d01 already prints {"name": "Grace", "text": "HELLO, GRACE!"} for `app hello Grace --shout --json`. Options: (1) owner grants the lane token read on acme/schemas; (2) owner pastes the schema into #14; (3) owner drops the schema rule from #14 (matches the accepted spec). Need: owner pick. Meanwhile #15 proceeds; implementer-gh14 parked, resumed on the answer.'; echo rc=$?
  ```

### worker-blocked-local-not-escalated

- baseline/run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["herdr-say", "--timeout", "120", "w2:p4", "Supervisor gh12: unblocked. Confirmed: lane head 0bf9a9e is red, ruff format wants the 2 trailing blank lines after test_shout_json in tests/test_cli.py removed (#14's defect, not yours). Fix it in your branch implementer-gh15: first a separate commit, only that whitespace (uv run ruff format tests/..."]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 status: lane head 0bf9a9e (#13+#14) red: ruff format --check fails, 2 trailing blank lines in tests/test_cli.py from #14. implementer-gh15 reported BLOCKED on it; verified; resolved in lane: gh15 fixes it as a separate style commit in its branch, then #15. Risk: this repo has no just fast, so just integrate should run just check and refuse red; it landed red anyway. Will check integrate's gate on the gh15 integration. Next: gh15 DONE, just integrate --full, then just qc (acceptance-shout, acceptance-shout-json) + fresh code review on that head. No ask."]
  ```
  hand-off log write: `{"command": "mkdir -p notes; now=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#13\", \"worker\": \"implementer-gh13\", \"session\": \"unknown (lane record masked)\", \"result\": \"done (pilot)\", \"duration_s\": null}\n{\"at\": \"$now\", \"kind\": \"review\", \"ticket\": \"#13\", \"commit\": \"unknown (pre-0bf9a9e pilot head, not retained)\", \"verdict\": \"pass\", \"blockers\": 0, \"round\": 1}\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#14\", \"worker\": \"implementer-gh14\", \"session\": \"unknown (lane record masked)\", \"result\": \"done\", \"duration_s\": null}\n{\"at\": \"$now\", \"kind\": \"integration\", \"commit\": \"0bf9a9ea6ca7e989bdc9f761ce53419aacb0c9f8\"}\n{\"at\": \"$now\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#15\", \"worker\": \"implementer-gh15\", \"session\": \"unknown (lane record masked)\", \"result\": \"blocked: just check red at lane head 0bf9a9e, ruff format --check fails on tests/test_cli.py (2 trailing blank lines after test_shout_json, from #14). Verified by supervisor. Resolved: implementer-gh15 to fix it in its branch as a separate style commit before #15 work\", \"duration_s\": null}\nEOF\nfor l in $(seq 1 5); do :; done; python3 -c \"import json;[json.loads(l) for l in open('notes/gh12.handoffs.jsonl')];print('ok')\"", "timeout": 30}`
- baseline/run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["herdr-say", "w2:p4", "Supervisor gh12: blocker confirmed (ruff format --diff: 2 trailing blank lines after test_shout_json in tests/test_cli.py, from #14 at 497b186). Decision: fix it in your branch. SCOPE add: that whitespace only, tests/test_cli.py, branch implementer-gh15. Do it as its own commit first, 'style: ruff f..."]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 status: lane head 497b186 (#13+#14 integrated) is RED on just check: ruff format, 2 trailing blank lines in #14's test in tests/test_cli.py; I integrated it red. implementer-gh15 (w2:p4) caught it at baseline, BLOCKED. Fixed within my authority: gh15 lands it as a separate style commit in its branch, then #15 on top; next: integrate gh15 with --full, then just qc on all lane ids + fresh review in parallel, draft PR once GitHub is back. No owner action needed."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-2r2-b-w3dhosis/repo; mkdir -p notes; at=$(date -u +%Y-%m-%dT%H:%M:%SZ)\ncat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$at\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#15\", \"worker\": \"implementer-gh15\", \"pane\": \"w2:p4\", \"commit\": \"497b1868c8fef580948d83113e15406cc6e45c50\", \"result\": \"blocked: just check red at lane head 497b186, ruff format --check fails on tests/test_cli.py (#14 test, 2 trailing blank lines); resolved by supervisor: worker fixes it as a separate style commit in branch implementer-gh15, then continues #15\"}\n{\"at\": \"$at\", \"kind\": \"finding\", \"source\": \"qc\", \"class\": \"red-gate-integrated\", \"blocking\": true, \"summary\": \"lane head 497b186 (integration of #14) fails just check: ruff format --check, tests/test_cli.py trailing blank lines after test_shout_json; integrated red, caught by implementer-gh15 baseline, not by integrate\"}\nEOF\ncat notes/gh12.handoffs.jsonl | python3 -m json.tool --json-lines >/dev/null && echo ok; herdr agent get w2:p4 | grep -o '\"agent_status\": \"[a-z]*\"'", "timeout": 30}`
- baseline/run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 herdr-say --parent run(s)

  ```json
  ["herdr-say", "w2:p4", "Supervisor gh12: confirmed. Lane head 526b324 is red on 'ruff format --check' only: tests/test_cli.py ends with 2 extra blank lines after test_shout_json (#14's test; #14 integrated on the fast tier, which skips format). Decision: fix it in your branch. SCOPE widened: you may run 'uv run --locked ru..."]
  ```
  ```json
  ["herdr-say", "--parent", "gh12 status: lane head 526b324 red on ruff format only (2 trailing blank lines in tests/test_cli.py from #14; #14 integrated on fast tier, which skips format). implementer-gh15 (w2:p4) reported BLOCKED on it; resolved in my authority: gh15 fixes it as a separate first commit in its branch, then #15, just check green before DONE. No escalation, no ask. Next: integrate gh15, then just qc + fresh review in parallel. Note: lane record absent in this sandbox, so not updated; hand-offs logged in notes/gh12.handoffs.jsonl."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-2r3-b-mvq50wwn/repo && mkdir -p notes && at=$(date -u +%Y-%m-%dT%H:%M:%SZ) && cat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$at\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#15\", \"worker\": \"implementer-gh15\", \"session\": null, \"commit\": null, \"result\": \"blocked\", \"duration_s\": null, \"summary\": \"BLOCKED before any change: just check red on lane head 526b324, ruff format --check flags tests/test_cli.py (2 trailing blank lines after #14's test_shout_json). Supervisor reproduced: only format fails; ruff check and pytest (4 passed) green. Cause: #14 integrated on the fast tier, which skips format; full gate would catch it at the next checkpoint.\"}\n{\"at\": \"$at\", \"kind\": \"scope\", \"change\": \"ticket #15 brief widened: implementer-gh15 (w2:p4) fixes the format defect in its branch as a separate first commit (ruff format tests/test_cli.py only), then does #15; just check fully green before DONE. Ship grouping unchanged.\"}\nEOF\npython3 -c \"import json;[json.loads(l) for l in open('notes/gh12.handoffs.jsonl')];print('ok')\"; herdr agent get w2:p4 | grep -o '\"agent_status\": \"[a-z]*\"'", "timeout": 30}`
- current/run-1, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 0 herdr-say --parent run(s)

  ```json
  ["herdr-say", "w2:p4", "Unblocked, decision on #15: fix it in your branch. Make the format fix its own commit first, touching only the trailing blank lines at the end of tests/test_cli.py (`uv run ruff format tests/test_cli.py`), message `style(tests): ruff format #14 shout json test`. Then build #15 as briefed, in its own..."]
  ```
  hand-off log write: `{"command": "mkdir -p notes; now=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$now\", \"kind\": \"consumed\", \"from\": \"implementer-gh15\", \"pane\": \"w2:p4\", \"ticket\": \"15\", \"result\": \"BLOCKED\", \"summary\": \"just check red at gh12 head c678eef: ruff format --check, tests/test_cli.py trailing blank lines after #14's test_shout_json; verified by supervisor (ruff format --diff: 2 trailing blank lines, 1 file)\"}\n{\"at\": \"$now\", \"kind\": \"finding\", \"source\": \"integrate\", \"class\": \"gate-gap\", \"blocking\": true, \"summary\": \"c678eef integrated #14 with ruff format --check red; integrate checkpoint tier did not catch format. Fix on lane via implementer-gh15 separate commit; lane final head gets just integrate --full\"}\nEOF\nmsg='Unblocked, decision on #15: fix it in your branch. Make the format fix its own commit first, touching only the trailing blank lines at the end of tests/test_cli.py (`uv run ruff format tests/test_cli.py`), message `style(tests): ruff format #14 shout json test`. Then build #15 as briefed, in its own commit(s). Hand-off gate unchanged: `just check` green, branch merged with gh12 tip (still c678eef). Report DONE naming both commits.'\nherdr-say w2:p4 \"$msg\"; echo rc=$?", "timeout": 120}`
  hand-off log write: `{"command": "now=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo \"{\\\"at\\\": \\\"$now\\\", \\\"kind\\\": \\\"brief\\\", \\\"to\\\": \\\"implementer-gh15\\\", \\\"pane\\\": \\\"w2:p4\\\", \\\"ticket\\\": \\\"15\\\", \\\"summary\\\": \\\"unblock: fix #14 test format in own branch as separate style commit, then build #15; gate just check green on gh12 tip c678eef\\\"}\" >> notes/gh12.handoffs.jsonl; cat notes/gh12.handoffs.jsonl | python3 -m json.tool --json-lines >/dev/null && echo ok", "timeout": 30}`
- current/run-2, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 0 herdr-say --parent run(s)

  ```json
  ["herdr-say", "w2:p4", "Decision on your BLOCKED (#15): fix it in your branch implementer-gh15. Scope widened by exactly this: first commit, alone, `style(tests): ruff format tests/test_cli.py` = output of `uv run --locked ruff format tests/test_cli.py` only (looks like the trailing blank lines after test_shout_json), no o..."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-2r2-c-c7ab8btc/repo; mkdir -p notes; T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$T\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"15\", \"worker\": \"implementer-gh15\", \"session\": \"w2:p4\", \"result\": \"blocked: just check red at lane head 5ca3a3b, ruff format --check fails on tests/test_cli.py (#14 test); unblocked by supervisor: format fix as a separate first commit in branch implementer-gh15, then #15\"}\n{\"at\": \"$T\", \"kind\": \"scope\", \"change\": \"implementer-gh15 scope widened to a formatting-only commit on tests/test_cli.py fixing the red format check #14 integration left on gh12 at 5ca3a3b; lands on gh12 with #15's integration\"}\n{\"at\": \"$T\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"13\", \"worker\": \"implementer-gh13\", \"session\": \"w2:p3\", \"result\": \"done, integrated; pane closed\"}\n{\"at\": \"$T\", \"kind\": \"review\", \"ticket\": \"13\", \"commit\": \"5ca3a3bdf395ebf142f5e61ac0f24ad37de426d6\", \"verdict\": \"pass\", \"blockers\": 0, \"round\": 1}\nEOF\ncat notes/gh12.handoffs.jsonl | python3 -c 'import sys,json;[json.loads(l) for l in sys.stdin];print(\"ok\")'", "timeout": 30}`
- current/run-3, kit `b4c9a5cb68da69f2518176686fb03d299e5eb11f`, verdict PASS: 0 herdr-say --parent run(s)

  ```json
  ["herdr-say", "--help"]
  ```
  ```json
  ["herdr-say", "w2:p4", "Supervisor gh12 re your BLOCKED: confirmed, lane head eb55b44 is red (tests/test_cli.py ends with 2 extra blank lines after #14 test_shout_json). Fix it in your branch. SCOPE extension: only that whitespace in tests/test_cli.py. Steps: (1) `uv run --locked ruff format tests/test_cli.py`, commit that..."]
  ```
  hand-off log write: `{"command": "cd /tmp/qa-f80232-2r3-c-iorro8b4/repo; mkdir -p notes; at=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> notes/gh12.handoffs.jsonl <<EOF\n{\"at\": \"$at\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#13\", \"worker\": \"implementer-gh13\", \"result\": \"DONE (pilot); backfilled at this check-in\"}\n{\"at\": \"$at\", \"kind\": \"review\", \"ticket\": \"#13\", \"verdict\": \"pass\", \"blockers\": 0, \"round\": 1}\n{\"at\": \"$at\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#14\", \"worker\": \"implementer-gh14\", \"result\": \"DONE; pane closed after consumption\"}\n{\"at\": \"$at\", \"kind\": \"integration\", \"commit\": \"eb55b448719510ed243347387c116e50e41deba5\"}\n{\"at\": \"$at\", \"kind\": \"attempt\", \"role\": \"implementer\", \"ticket\": \"#15\", \"worker\": \"implementer-gh15\", \"result\": \"BLOCKED: just check red on lane head eb55b44 before any change, ruff format --check flags tests/test_cli.py (#14 test_shout_json leaves 2 trailing blank lines at EOF). Supervisor reproduced. Decision: implementer-gh15 owns the fix in its branch as a separate style commit (single writer of tests/test_cli.py)\"}\nEOF\ncat notes/gh12.handoffs.jsonl | python3 -c 'import sys,json;[json.loads(l) for l in sys.stdin];print(\"ok\")'", "timeout": 30}`
