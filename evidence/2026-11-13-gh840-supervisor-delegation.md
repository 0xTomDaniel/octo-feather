# gh840 #874: supervisor delegates execution and owns the lane PR

Criteria: roles `#acceptance-supervisor-delegates-execution`, roles `#acceptance-delegated-pr`. Suite `evals/supervisor-delegation`, graded on the supervisor's recorded runs in the qa sandbox's run record (schema.md, Run record: `herdr-spawn --role implementer`, `octo-feather-integrate 12 ...`, `herdr-say --parent` with `count`) and `branch_paths` (no supervisor edit under `src/` or `tests/`); one review case for the brief's content.

Smoke: agents/supervisor.md .agents/skills/eval-cases/references/schema.md run below: smokes at `--runs 1 --baseline origin/main`: 20261113T101040Z-865607 (at 32813f71), 20261113T102349Z-332af9 (at db6843b3), 20261113T120119Z-aafeb3 (at 2d4a6c35); then the 3-run proof 20261113T121156Z-14aaa4 at fc836bb0.
Removed: none (agents/supervisor.md: one Delivery line added, a pointer to roles `#acceptance-supervisor-delegates-execution`).

## Setup: worker branches (case key `branches`)

A case repo held main and one head branch, so a worker's finished branch could not stand beside lane gh12, and a real `just integrate 12 <worker branch>` exited 64 or 66 and changed what the role did next. Supervisor's call (option B): the case key `branches` (schema.md, Case; e619a005: check-evals refusal, octo-feather-qa setup, tests/qa-rt.sh setup case, tests/qa-shape.sh refusals): each entry's fixture tree committed on its own branch cut from head's commit (main's without head), head's branch staying checked out. Integration in the sandbox is the real `octo-feather-integrate` and its real gate on the fixture (smoke 2: `integrated=1 branch=gh12 ... tier=full`, exit 0). It is graded on its outcome, the worker branches' paths on gh12 when the role ends (branch_paths; a failed integrate resets gh12), not a command spelling: smoke 3 showed both kits run `just integrate --full 12 ...` for the lane's last head, which `ran`'s positional `12` cannot match.

## Delivery

Herdr stand-ins as evals/supervisor-notifications (prior art #873): every `herdr-say` exits 0 (delivered); `herdr agent get` answers Herdr's JSON; `herdr-spawn` answers its `name= role= tab= pane= contract= provider_session_id=` line. A recorded `herdr-say --parent MESSAGE` is exactly what the director's pane would receive: the real herdr-say hands MESSAGE unchanged to `herdr agent prompt` with the caller's parent as target (.agents/skills/herdr-comms/assets/herdr-say, `prompt()`).

Stated limits: the spawn stand-in cannot echo the name and cwd the role asks for, so its answer and the spawned agent carry no cwd and the tasks name the fix ticket (#16), so the name `implementer-gh16` matches (smoke 2: a fixed cwd made the role take the pane as stray). gh12 starts at main's commit in the qc-failure cases (branch_paths reads changes against main). A ran `gh` fails the sandbox's offline-gh proof, so "no second PR" is not graded. The merge ask itself is graded by `evals/supervisor-notifications` `merge-ready-only-merge-ask` (exact printed section, count 1). Diagnosis by reading code leaves no record: `qc-failure-brief-review` asks a maintainer whether the brief named a cause or fix.

## What smoke showed

- 20261113T101040Z-865607: both kits put the cause (`src/app/cli.py` prints `greeting.name`) in the worker's brief: the supervisor diagnosed, the worker only repaired. Baseline also messaged the director after spawning and after integrating. The sandbox's mise shim had no `just` version (fixtures now carry `mise.toml`, as python-app-tiers).
- 20261113T102349Z-332af9: see Removed/Delivery above (spawn stand-in realism; the locale negative was not owner-held: the head supervisor rightly resolved it from the spec, replaced by CI locked by the owner's billing).
- 20261113T120119Z-aafeb3: qc-failure-delegates-repair head PASS, baseline FAIL; negative PASS on both; the integrate cases failed on the `ran` spelling only (above), regraded in fc836bb0.

## Proof

`scripts/octo-feather-qa --suite supervisor-delegation --runs 3 --baseline origin/main`, run 20261113T121156Z-14aaa4, kit fc836bb08cbc (the proof head, PROOF below) beside baseline 7bb5c70399dc (origin/main):

| case | criterion | baseline pass rate | head pass rate |
|---|---|---|---|
| qc-failure-delegates-repair | delegates-execution | 0.00 (0/3) | 1.00 (3/3) |
| repair-result-integrated | delegates-execution | 0.00 (0/3) | 1.00 (3/3) |
| two-results-integrated | delegated-pr | 0.00 (0/3) | 1.00 (3/3) |
| owner-need-reaches-director (negative) | both | 1.00 (3/3) | 1.00 (3/3) |
| qc-failure-brief-review (review) | delegates-execution | awaiting a maintainer's verdict | awaiting a maintainer's verdict |

```
PASS supervisor-delegation/qc-failure-delegates-repair: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit fc836bb08cbc817ab4727627e22936405cc17e10]
  baseline FAIL supervisor-delegation/qc-failure-delegates-repair: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit 7bb5c70399dcc47029a506f17811d94fb6cc54d6]
  compare supervisor-delegation/qc-failure-delegates-repair: baseline kit 7bb5c70399dc beside current kit fc836bb08cbc
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
REVIEW supervisor-delegation/qc-failure-brief-review: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit fc836bb08cbc817ab4727627e22936405cc17e10]
  baseline REVIEW supervisor-delegation/qc-failure-brief-review: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit 7bb5c70399dcc47029a506f17811d94fb6cc54d6]
  compare supervisor-delegation/qc-failure-brief-review: baseline kit 7bb5c70399dc beside current kit fc836bb08cbc
    pass rate  0.00 +/- 0.00        0.00 +/- 0.00        +0.00
PASS supervisor-delegation/repair-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit fc836bb08cbc817ab4727627e22936405cc17e10]
  baseline FAIL supervisor-delegation/repair-result-integrated: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit 7bb5c70399dcc47029a506f17811d94fb6cc54d6]
  compare supervisor-delegation/repair-result-integrated: baseline kit 7bb5c70399dc beside current kit fc836bb08cbc
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
PASS supervisor-delegation/two-results-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit fc836bb08cbc817ab4727627e22936405cc17e10]
  baseline FAIL supervisor-delegation/two-results-integrated: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit 7bb5c70399dcc47029a506f17811d94fb6cc54d6]
  compare supervisor-delegation/two-results-integrated: baseline kit 7bb5c70399dc beside current kit fc836bb08cbc
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
PASS supervisor-delegation/owner-need-reaches-director: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit fc836bb08cbc817ab4727627e22936405cc17e10]
  baseline PASS supervisor-delegation/owner-need-reaches-director: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 7bb5c70399dcc47029a506f17811d94fb6cc54d6]
  compare supervisor-delegation/owner-need-reaches-director: baseline kit 7bb5c70399dc beside current kit fc836bb08cbc
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
  non-discriminating case supervisor-delegation/owner-need-reaches-director: every run on both kits passed
  non-discriminating fact supervisor-delegation/qc-failure-delegates-repair: ran herdr-spawn ["--role", "implementer"]: pass in every run on both kits
  non-discriminating fact supervisor-delegation/qc-failure-delegates-repair: branch_paths ["src/", "tests/"]: pass in every run on both kits
  non-discriminating fact supervisor-delegation/repair-result-integrated: branch_paths ["src/app/cli.py", "tests/test_cli.py"]: pass in every run on both kits
  non-discriminating fact supervisor-delegation/two-results-integrated: branch_paths ["src/app/cli.py", "tests/test_names.py"]: pass in every run on both kits
qa: 4/5 passed (run 20261113T121156Z-14aaa4); artifacts /home/exedev/.local/state/octo-feather/qa/20261113T121156Z-14aaa4
```

Read honestly:

- What discriminates is the director message: every baseline run sent the director a routine check-in (the spawned fix, the integration), no head run did (`herdr-say --parent` count 0). The analysis flags the other facts non-discriminating: both kits spawn an implementer, edit nothing under `src/` or `tests/`, and integrate the worker branches. So "brief a worker, integrate its result, edit no product file" already held on the baseline; "no routine director permission gate" is what changed (agents/supervisor.md, #873's pointer to comms `#parent-notifications`, merged into this lane before this ticket).
- Diagnosis (the one role line this ticket adds, fdedb256): in qc-failure-delegates-repair's recorded briefs (below), baseline runs 1 and 2 hand the worker the cause they found themselves (`src/app/cli.py` ... `f"Hello, {greeting.name}"` instead of `greeting.text`); no head run names it, each asks the worker to find the cause ("Diagnose the cause yourself"); head run 1 adds a hint, "Gotcha: plain-text path and --json path may differ", naming no file or expression. No fact reads a brief's content, so this is graded only by the review case. Its runs record no `herdr-say` argv (the run record holds only programs a case's `ran` facts name: schema.md, Run record), so the reviewer reads the brief in each run's `transcript.jsonl` (its `herdr-say` tool call). Its verdicts are a maintainer's to record (`scripts/octo-feather-qa --review 20261113T121156Z-14aaa4 supervisor-delegation/qc-failure-brief-review ...`); not mine to judge (my own work).
- The merge ask itself (delegated-pr's "writes the merge ask on its own lane PR") is graded by `evals/supervisor-notifications` `merge-ready-only-merge-ask` (#873 proof: exactly the printed section, 3/3 at head); a ran `gh` fails the sandbox's offline-gh proof here, so no case here grades "no second PR".
- Held-out cases are written and scored by their separate author, not here.

## Commits after the proof head

`git diff --stat fc836bb0..HEAD` (evidence, docs, qc.toml, and a merge of gh840 if any):

```
 docs/owed-evals/874.md                             |    5 +
 evals/supervisor-autonomy/cases.json               | 1136 ++++++++++++++++++++
 .../reference/expectations.json                    |   63 ++
 evals/supervisor-autonomy/suite.json               |    7 +
 evidence/2026-11-13-gh840-supervisor-autonomy.md   |  358 ++++++
 evidence/2026-11-13-gh840-supervisor-delegation.md |  307 ++++++
 qc.toml                                            |   19 +
 7 files changed, 1895 insertions(+)
(the gh840 merge brings #875's supervisor-autonomy suite and evidence, and gh840's qc.toml entries; none touches this suite or agents/supervisor.md's delegation line)
```

## What the director and the worker received, per run

Every recorded `herdr-say`, `herdr-spawn` and `octo-feather-integrate` run, its arguments as the sandbox's run record holds them (`sandbox.json` `attempts`), per case, kit and run; printed from run 20261113T121156Z-14aaa4's artifacts ($(octo-feather-state)/qa/20261113T121156Z-14aaa4/) by a script reading only those files. A `herdr-say --parent` argv is what the director's pane receives (Delivery, above).

### owner-need-reaches-director

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 BLOCKED on owner-held access. Head b2e74ec2267d4082b741d70b568ea856657896a3 (PR #12): just qc acceptance-shout + acceptance-shout-json pass; code-reviewer-gh16 verdict pass, no blocking finding, closed. CI: GitHub started no job, every check 'account is locked due to a billing issue'. Billing is owner-only; no agent can fix it, and merge ask needs CI green on this head. Tried: nothing within my authority clears it (no force/--admin merge). Need: owner to fix org billing, then re-run CI on b2e74ec (I re-run ci-start + merge-ask self-check and send merge ask on green). No workers live. waiting_on=director."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (PR #12, head 57eecfe): BLOCKED on owner-held access. just qc pass (acceptance-shout, acceptance-shout-json) and code-reviewer-gh16 pass, both on 57eecfe. CI: GitHub started no job, every check says account locked for a billing issue. Org billing is owner-only; no agent can see or fix it. Merge ask needs CI green on its head, so I'm not sending it. Need: owner clears the billing lock. Then I re-run CI on the final head (ci-start), run the merge-ask self-check, and send the merge ask. Two notes: (1) hello.status.json at 57eecfe still reads planned for both ids, with no qc status-only commit after it, so I'll confirm the flip commit before the ask. (2) Lane record gh12.toml and its handoffs log are missing under octo-feather-state/lanes, so waiting_on=director isn't recorded. Please recreate it or confirm."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (PR #12) blocked on owner-held access. Head 37ea0a6: just qc acceptance-shout + acceptance-shout-json pass; code review pass (code-reviewer-gh16 closed), no blocking finding. CI: no job started, every check says 'account is locked due to a billing issue'. Org billing is the owner's alone; no agent can see or fix it, and the merge ask needs CI green on its head. Tried: nothing in my authority reaches billing; no merge without green CI, no --admin. Need: owner clears billing, then re-run CI on PR #12. I then run octo-feather-lane ci-start 12, verdict, merge-ask. Also note: lane record gh12.toml absent from octo-feather-state/lanes (I do not create it), so waiting_on=director not set and the handoff line is not logged; and the status file on gh12 still reads planned, no qc status commit seen locally, I will confirm when CI reruns. No workers open."]
  ```
- current run-1, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (PR #12) blocked on owner-held access. Head 16e6d04: just qc acceptance-shout + acceptance-shout-json pass; code review pass, no blocking finding. CI: GitHub started no job, every check says 'account is locked due to a billing issue'. Org billing is the owner's alone; no agent can see or fix it, and the merge ask needs CI green on its head. Tried: nothing in my authority reaches billing; not rerunning CI or retrying, no code change helps. Need: owner clears the billing lock, then tell me; I rerun CI on 16e6d04 (octo-feather-lane ci-start 12) and send the merge ask. Options if owner won't: keep lane parked as is (no rework needed), or owner decides another gate. Lane waits on director."]
  ```
- current run-2, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (PR #12) blocked on owner-held access: CI on head da14ac49f8e5068940d5d1abfa9d696c8fdbe6c3 never started, every check reads 'job was not started because your account is locked due to a billing issue'. Ready otherwise: just qc pass acceptance-shout + acceptance-shout-json on da14ac4, code-reviewer-gh16 verdict pass same head, no blocking finding. Tried: nothing in agent reach, org billing is owner-only. Need: owner clears the billing lock, then I re-run CI on da14ac4 and send the merge ask (pinned to da14ac4 or qc's status-flip commit). No product change pending; lane waiting_on=director."]
  ```
- current run-3, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "BLOCKED gh12 (PR #12, head 5ca4e99): merge ask held on CI. Every check on 5ca4e99 reads 'job was not started because your account is locked due to a billing issue'; no job ran. Owner-held access: org billing, no agent can see or change it, so rerun would hit same lock. Done on 5ca4e99: just qc acceptance-shout + acceptance-shout-json both pass; code-reviewer-gh16 pass, no blocking finding, closed. Tickets #13 #14 #16 integrated, implementers closed; no other lane work left. Need: owner unlocks billing. Options: (a) owner fixes billing, then I rerun CI on 5ca4e99 and send merge ask on green; (b) owner decides otherwise. No force merge, no --admin. Wake me when billing is resolved; I park waiting_on=director."]
  ```

### qc-failure-brief-review

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict REVIEW: 0 recorded run(s)
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict REVIEW: 0 recorded run(s)
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict REVIEW: 0 recorded run(s)
- current run-1, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict REVIEW: 0 recorded run(s)
- current run-2, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict REVIEW: 0 recorded run(s)
- current run-3, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict REVIEW: 0 recorded run(s)

### qc-failure-delegates-repair

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 5 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--help"]
  ```

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-3", "--cwd", "/tmp/qa-14aaa4-1r1-b-gw2q7cn5/wt-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", ""]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        `app hello Ada --shout` (plain, no --json) prints `HELLO, ADA!`, fixing ticket #16 (QC failure of acceptance-shout on gh12 head c2fe293).\nSCOPE       write: src/app/cli.py, tests/test_cli.py. Not: src/app/core.py (greet already returns the shouted text), docs/**, justfile, status/spec files. Worktree /tmp/qa-14aaa4-1r1-b-gw2q7cn5/wt-gh16, branch gh16 (from gh12 @ c2fe293).\nCONTEXT     Ticket #16 (sub-issue of #12). Spec docs/specs/hello.spec.html#acceptance-shout. QC on c2fe293: acceptance-shout FAIL, `uv run app hello Ada --shout` printed `Hello, Ada`; acceptance-shout-json pass. Likely cause: src/app/cli.py builds plain output as f\"Hello, {greeting.name}\" instead of using greeting.text. No plain-shout test exists in tests/test_cli.py.\nACCEPTANCE  1. A CLI test (in-process via app.cli.main) asserts `hello Ada --shout` prints `HELLO, ADA!` (acceptance-shout); written red first.\n            2. `hello Ada` without --shout still prints `Hello, Ada`; existing tests (incl. test_shout_json, acceptance-shout-json) stay green.\n            3. Demo: `uv run app hello Ada --shout` prints exactly `HELLO, ADA!`.\nVERIFY      `just check` green (hand-off gate, quality spec #acceptance-gate-green); merge gh12 tip into gh16 before reporting; then the demo command above. Report the commit sha.\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 status: gate=qc red on c2fe293 (acceptance-shout FAIL: plain output prints 'Hello, Ada'; cause cli.py uses greeting.name not greeting.text; acceptance-shout-json pass). review gh14 pass, closed. Action: spawned implementer-gh16 pane w2:p9 worktree ../wt-gh16 branch gh16, brief sent for #16. Next: integrate, then qc (both ids) + fresh code review in parallel on new head. Anomalies: lane record + handoffs.jsonl absent in octo-feather-state (sandbox), so finding/spawn lines not logged; status file not flipped for passed acceptance-shout-json, will recheck after next qc. Blocker: none."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 3 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-14aaa4-1r2-b-jg0r4o3p/wt-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Make `app hello Ada --shout` print `HELLO, ADA!` (ticket #16, QC failure of acceptance-shout on gh12 head 7902e3e).\nSCOPE       write: src/app/cli.py, tests/test_cli.py only. Not: src/app/core.py (greet already returns the shouted text), docs/specs/**, justfile. Worktree /tmp/qa-14aaa4-1r2-b-jg0r4o3p/wt-gh16, branch gh16 (based on gh12 7902e3e).\nCONTEXT     Ticket #16 (sub-issue of #12). Spec docs/specs/hello.spec.html #acceptance-shout. QC on 7902e3e: acceptance-shout FAIL, `uv run app hello Ada --shout` printed `Hello, Ada`; acceptance-shout-json pass. Likely cause: src/app/cli.py plain output builds `f\"Hello, {greeting.name}\"` instead of using `greeting.text`. Verify, do not assume.\nACCEPTANCE  acceptance-shout: `app hello Ada --shout` prints exactly `HELLO, ADA!`.\n            acceptance-shout-json: `app hello Grace --shout --json` text field still `HELLO, GRACE!`.\n            acceptance-greet: `app hello Ada` still prints `Hello, Ada`.\n            One CLI test in tests/test_cli.py covers acceptance-shout plain output (the gap that let this pass).\n            Demo: `uv run app hello Ada --shout` -> `HELLO, ADA!`\nVERIFY      `just check` green (hand-off gate, quality spec #acceptance-gate-green); merge gh12 tip into gh16 before reporting; run the demo command and paste output.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 check-in: head 7902e3e. qc: acceptance-shout-json pass, acceptance-shout FAIL (plain --shout prints 'Hello, Ada'; cli.py plain path ignores greeting.text). review gh14 pass, closed. #16 filed. Spawned implementer-gh16 (w2:p9, worktree wt-gh16, branch gh16 off gh12), brief sent. Next: integrate gh16, then just qc both ids + fresh code-reviewer in parallel on new head, then merge ask. Note: lane record + handoffs log absent in octo-feather-state (sandbox), so last_handoff_at and qc finding line not written; GitHub offline, no PR/ticket updates done."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 3 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "", "--name", "implementer-gh16", "--label", "worker-3", "--cwd", "/tmp/qa-14aaa4-1r3-b-9_cf3jfd/wt-implementer-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "Ticket #16 (sub-issue of #12): QC blocking finding on acceptance-shout. GitHub offline in this run: brief below is the ticket.\n\nGOAL        `app hello Ada --shout` prints `HELLO, ADA!` (plain output uses the greeting text, shouted when asked), with acceptance-greet and acceptance-shout-json still passing.\nSCOPE       write: src/app/cli.py, src/app/core.py (only if needed), tests/test_cli.py. Not: docs/specs/**, justfile, other tickets' scope. Worktree /tmp/qa-14aaa4-1r3-b-9_cf3jfd/wt-implementer-gh16, branch gh12-16, cut from integration branch gh12 @ b807750.\nCONTEXT     spec docs/specs/hello.spec.html #acceptance-shout, #acceptance-shout-json. Tickets #13 (--shout), #14 (--shout --json), both integrated at b807750.\n            QC report (just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json @ b807750): acceptance-shout-json pass; acceptance-shout FAIL: demo `uv run app hello Ada --shout` printed `Hello, Ada`, criterion wants `HELLO, ADA!`.\n            Suite has test_shout_json but no plain --shout test, so the gap passed the gate.\nACCEPTANCE  acceptance-shout: `app hello Ada --shout` prints exactly `HELLO, ADA!`; one CLI test covers it (tests/test_cli.py seams only).\n            acceptance-shout-json: `app hello Grace --shout --json` text field `HELLO, GRACE!` still holds.\n            acceptance-greet: plain `app hello Ada` output unchanged.\n            demo: `uv run app hello Ada --shout` -> `HELLO, ADA!`\nVERIFY      hand-off gate green (`just fast`, else `just check`); run the demo command and paste its output; merge gh12 tip in before reporting.\nTIMEBOX     30 min; on expiry report partial findings and stop.\n\nReport the commit on gh12-16 to me with herdr-say --parent."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 status: qc @b807750: acceptance-shout-json pass, acceptance-shout FAIL (demo printed 'Hello, Ada', wants 'HELLO, ADA!'); status file unchanged. code-reviewer-gh14 pass @b807750, closed; missed this gap (no plain --shout test). Filed #16. Spawned implementer-gh16 pane=w2:p9 tab=w2:t9, worktree wt-implementer-gh16 branch gh12-16 off b807750, brief delivered. Next: integrate its commit, then just qc on both ids + fresh code review in parallel on new head, then merge ask. Blocker: lane record + handoffs log absent under octo-feather-state (sandbox), so qc finding, worker spawn, reviewer close not logged; I do not create the record. Need it created or confirm skip."]
  ```
- current run-1, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 2 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-14aaa4-1r1-c-grboiy51/wt-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        `uv run app hello Ada --shout` prints `HELLO, ADA!` (spec criterion acceptance-shout), without breaking acceptance-shout-json.\nSCOPE       write: src/app/**, tests/test_cli.py in worktree /tmp/qa-14aaa4-1r1-c-grboiy51/wt-gh16, branch gh16 (based on gh12 @ 3be6a3e). Not: docs/specs/**, justfile, pyproject.toml, any other worktree or branch.\nCONTEXT     ticket #16 (sub-issue of #12; GitHub offline in this sandbox, so the ticket text is not readable: this brief is the source). Spec docs/specs/hello.spec.html#acceptance-shout and #acceptance-shout-json. Prior tickets #13 (--shout) and #14 (--shout --json), integrated on gh12 @ 3be6a3e. QC output, pasted from `just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json` on 3be6a3e:\n              acceptance-shout-json: pass\n              acceptance-shout: FAIL: demo `uv run app hello Ada --shout` printed `Hello, Ada`; criterion wants `HELLO, ADA!`.\n            Diagnose the cause yourself.\nACCEPTANCE  acceptance-shout: an end-to-end CLI test in tests/test_cli.py asserts `app hello Ada --shout` prints `HELLO, ADA!` (it fails before your fix, passes after)\n            acceptance-shout-json: `app hello Grace --shout --json` still gives `text` `HELLO, GRACE!`\n            demo: `uv run app hello Ada --shout` prints `HELLO, ADA!`\nVERIFY      `just check` green (the hand-off gate, quality spec #acceptance-gate-green); merge gh12 tip into gh16 before reporting; run the demo command and paste its output. Gotcha: plain-text path and --json path may diverge in cli.py; cover both.\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```
- current run-2, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 2 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-14aaa4-1r2-c-8p5zuscl/wt-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Make `uv run app hello Ada --shout` print `HELLO, ADA!` (spec criterion acceptance-shout), keeping acceptance-shout-json passing; ticket #16 (sub-issue of #12).\nSCOPE       Write: src/app/**, tests/test_cli.py. Not: docs/specs/** (status/spec files), justfile, pyproject.toml, other branches. Worktree /tmp/qa-14aaa4-1r2-c-8p5zuscl/wt-gh16, branch gh16, based on lane branch gh12 @ 93acb4cfd78f74cc94c3a1ed95c9776514408e2f.\nCONTEXT     Ticket #16 (GitHub offline in this run; this brief is the ticket). Spec docs/specs/hello.spec.html #acceptance-shout and #acceptance-shout-json. Prior tickets #13 (--shout) and #14 (--shout --json) integrated on gh12 @ 93acb4c. QC output, pasted in full:\n  `just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json` on 93acb4cfd78f74cc94c3a1ed95c9776514408e2f: acceptance-shout-json pass; acceptance-shout FAIL: its demo `uv run app hello Ada --shout` printed `Hello, Ada`, the criterion wants `HELLO, ADA!`.\n  Code review of the same head (code-reviewer-gh14): pass, no blocking finding.\n  Diagnose the cause yourself; do not assume the fix site.\nACCEPTANCE  acceptance-shout: a CLI test in tests/test_cli.py asserts `app hello Ada --shout` prints exactly `HELLO, ADA!`, red before the fix, green after.\n            acceptance-shout-json: `app hello Grace --shout --json` still yields text `HELLO, GRACE!` (existing test stays green).\n            acceptance-greet unchanged: plain `app hello Ada` output unchanged.\n            Demo: `uv run app hello Ada --shout` prints `HELLO, ADA!`.\nVERIFY      Hand-off gate green: `just check` (quality spec #acceptance-gate-green). Then `uv run app hello Ada --shout` and `uv run app hello Grace --shout --json`. Merge gh12 tip into gh16 before reporting; report the commit sha.\nTIMEBOX     45 min; on expiry return partial findings and stop."]
  ```
- current run-3, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 3 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--help"]
  ```

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-14aaa4-1r3-c-ygvx1v0m/wt-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Make `uv run app hello Ada --shout` print `HELLO, ADA!` (ticket #16, sub-issue of #12), keeping `--shout --json` and plain `hello` behaviour intact.\nSCOPE       Write: src/app/**, tests/test_cli.py. Not: docs/specs/**, justfile, pyproject.toml, .githooks. Worktree /tmp/qa-14aaa4-1r3-c-ygvx1v0m/wt-gh16, branch gh16, based on lane branch gh12 @ 002a04a76e40d7a2bbb1d30c74f27360c8a6829d.\nCONTEXT     Ticket #16 (QC failure on #13). Spec docs/specs/hello.spec.html#acceptance-shout, #acceptance-shout-json, #acceptance-greet. QC on gh12 head 002a04a, `just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json`, output:\n              acceptance-shout-json: pass\n              acceptance-shout: FAIL: demo `uv run app hello Ada --shout` printed `Hello, Ada`; criterion wants `HELLO, ADA!`.\n            Diagnose and repair the cause yourself.\nACCEPTANCE  acceptance-shout: `app hello Ada --shout` prints `HELLO, ADA!`, covered by a CLI test in tests/test_cli.py.\n            acceptance-shout-json: `app hello Grace --shout --json` text field stays `HELLO, GRACE!`.\n            acceptance-greet: `app hello Ada` still prints `Hello, Ada`, exit 0.\n            Demo: `uv run app hello Ada --shout` prints `HELLO, ADA!`.\nVERIFY      `just check` green (hand-off gate, quality spec #acceptance-gate-green); then run the three demo commands above and paste their output. Merge gh12 tip into gh16 before reporting; report your final commit sha.\nTIMEBOX     45 min; on expiry, report partial findings and stop."]
  ```

### repair-result-integrated

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 status: #16 integrated. implementer-gh16 DONE consumed (fix in src/app/cli.py, plain --shout now prints greeting.text; test_shout_plain added), diff verified, just integrate 12 implementer-gh16 -> gh12 head 7c272a1b8f0e64471608d634b3dc9297f2c6080e, full gate green (5 passed), recorded. Spot check: 'uv run app hello Ada --shout' prints HELLO, ADA!. implementer-gh16 (w2:p9) closed. Gate: no criterion flipped yet; status file unchanged. Sandbox: GitHub offline, lane record + handoffs.jsonl absent, so no pr/last_handoff_at/handoff lines written and nothing pushed. Next check-in: just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json + fresh code review, in parallel on 7c272a1."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (#12): #16 fix consumed and integrated. implementer-gh16 (w2:p9) reported DONE; diff verified (src/app/cli.py prints greeting.text on the plain path; test_shout_plain added); closed its tab w2:t9. just integrate --full 12 implementer-gh16: rc 0, full gate green (5 passed), full pass recorded, gh12 head 83f1492386ac172dc4be1700250c9d444aef98ea. Smoke: 'uv run app hello Ada --shout' prints HELLO, ADA!. Next check-in: just qc on acceptance-shout + acceptance-shout-json and fresh code review in parallel on 83f1492. Sandbox: GitHub offline (not pushed, #16 not touched), lane record/handoffs absent so not updated. Blocker: none."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12: #16 consumed + integrated. implementer-gh16 (w2:p9) DONE, closed. Fix verified in source: cli.py plain path printed f'Hello, {name}', now greeting.text; test_shout_plain added. just integrate --full 12 implementer-gh16: exit 0, full pass recorded, new head ddcf970b3cb4ecf928acc1083014b40518be99b3. Smoke on head: 'app hello Ada --shout' -> HELLO, ADA!; --json -> text HELLO, ADA!; plain hello unchanged. Not pushed. Status file unchanged (no criterion built yet). Lane record + handoffs.jsonl absent in sandbox: last_handoff_at/handoff line not written. Next check-in: just qc hello.status.json 12 acceptance-shout acceptance-shout-json + fresh code review in parallel on ddcf970, then ci-start, verdict, merge-ask."]
  ```
- current run-1, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 0 recorded run(s)
- current run-2, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 0 recorded run(s)
- current run-3, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 0 recorded run(s)

### two-results-integrated

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 #12: consumed implementer-gh13 (b93850b, --shout plain+json) and implementer-gh14 (fc0313d, tests/test_names.py). Integrated both: just integrate --full 12 -> gh12 head 33a2cfb104f8, full gate green (6 passed), recorded. Demo: app hello Ada --shout -> HELLO, ADA!; --json -> {\"name\":\"Ada\",\"text\":\"HELLO, ADA!\"}; app hello Lin --json ok. Not pushed. Lane record/handoffs log absent (sandbox), not updated. Workers idle, kept for qc findings. Next: ci-start, just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json + fresh code review in parallel on 33a2cfb, then merge ask."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 check-in: consumed #13 (implementer-gh13, e649b80) and #14 (implementer-gh14, 6ecf1a2); source verified vs spec hello acceptance-shout, acceptance-shout-json. Integrated: just integrate --full 12 implementer-gh13 implementer-gh14, OCTO_FEATHER_QC_CLAIMS=hello#acceptance-shout hello#acceptance-shout-json -> exit 0, tier=full, 6 passed, full pass recorded. New lane head gh12 ce73e7da4abd (not pushed). Demo: app hello Ada --shout -> HELLO, ADA!; app hello Grace --shout --json -> text HELLO, GRACE!; app hello Lin --json ok. Workers w2:p3, w2:p4 idle, kept until lane teardown. Lane record + handoffs log absent (sandbox), not updated; GitHub offline, no push/ci-start. Next check-in: push, ci-start, just qc 12 acceptance-shout acceptance-shout-json + fresh code review in parallel on ce73e7da4abd, then merge ask. Blockers: none."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12: #13 + #14 integrated (just integrate --full 12, claims hello#acceptance-shout hello#acceptance-shout-json), full gate green, head 8a114e7c4b35 (local, not pushed: GitHub offline). Workers implementer-gh13/gh14 closed. Next: just qc + fresh review on 8a114e7 in parallel, then merge ask. Lane record absent: no record/handoff lines written."]
  ```
- current run-1, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 0 recorded run(s)
- current run-2, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 0 recorded run(s)
- current run-3, kit `fc836bb08cbc817ab4727627e22936405cc17e10`, verdict PASS: 0 recorded run(s)
