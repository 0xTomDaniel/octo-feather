# gh840 #876: fresh worker per independent assignment, ready work cut apart within limits

Criterion: roles `#acceptance-fresh-independent-worker` (rule owners: roles `#context-handoff-choice`, `#delegation-no-capacity`; issue-lifecycle `#lanes-parallel`), with the #754 supervisor half (serial planning). Suite `evals/supervisor-fresh-worker`, graded on the supervisor's `herdr-spawn` and `herdr-say` runs in the qa sandbox's run record, with the `ran` fact's `count` (schema.md, Run record). Herdr is stood in by each case's `stand_ins` (schema.md, Case), as in the pilot (evidence/2026-11-13-gh840-supervisor-notifications.md, Delivery); `octo-feather-handoff` is the real kit command (no stand-in, since 4ad2198b).

Smoke: agents/supervisor.md evals/supervisor-fresh-worker/ runs at `--runs 1 --baseline origin/main`: 20261113T094831Z-a8d9e9 (first draft, at e1d4d4da before the role change), 20261113T100003Z-b2ef81 and 20261113T101558Z-0203f2 (redrafted cases, restated role lines), 20261113T142658Z-9b2d89 (closed-assignment-fresh-worker on the pointer-only lines, 846f8e9d: baseline FAIL, head PASS); 3-run proofs 20261113T110500Z-368339 (c7e915e9), 20261113T142916Z-8ead36 (846f8e9d, stopped on a regression) and the final 20261113T144437Z-3f81bf (eb87b093).
Removed: agents/supervisor.md "run the implementers of independent tickets (no `Blocked by` between them) in parallel when you judge it practical. That is your call, not a count." (#754: one implementer serially carried independent ready work); replaced by pointers to issue-lifecycle `#lanes-parallel` and roles `#delegation-no-capacity`, and one clause on how they apply to a running worker.

## Role change (final, eb87b093)

agents/supervisor.md, two sites, as `git diff 77a3b40f -- agents/supervisor.md` shows:

- Authority, by the spawn naming rule: "Before you spawn or resume a worker for an assignment, read roles spec `#context-handoff-choice`."
- Delivery, the fan-out after the pilot: "fan out as issue-lifecycle spec `#lanes-parallel` and roles spec `#delegation-no-capacity` say. Applied to a running worker (roles spec `#context-handoff-choice`, issue-lifecycle spec `#lanes-parallel`): it keeps its in-progress ticket; ready tickets it has not started go to fresh workers."

History: 00ba04ed restated the owning anchors (proof 368339 below). 846f8e9d changed both lines to pointers only (the lane recipe: point, never restate); its proof 8ead36 showed a regression (below), fixed in eb87b093 by the one clause above, approved by the gh840 supervisor.

## Cases

All four: lane gh12 after its pilot (#13 integrated at the head, fixtures lane-shout-main and lane-shout-wip, whose tests drive the installed `app` command since the #874 fixture fix merged at 731a7fa9), remaining tickets #14 and #15, implementer-gh13 (pane w2:p3, session s-w2:p3) the #13 worker.

- `closed-assignment-fresh-worker`: implementer-gh13 parked after DONE, its session holding the #13 code #14 extends; #15 Blocked by #14; room for two. Facts: exactly one `herdr-spawn --role implementer`, `--name implementer-gh14`, no `herdr-spawn --resume`, no `herdr-say w2:p3` or `herdr-say implementer-gh13`.
- `serial-assignment-split`: implementer-gh13 running, briefed #14 and #15 as one serial assignment, on #14; #15 untouched; room for two. Facts: exactly one implementer spawn, `--name implementer-gh15`, no `--resume`.
- `independent-ready-split`: implementer-gh13 idle after DONE; #14 and #15 independent; room for two. Facts: exactly two implementer spawns, gh14 and gh15, and the no-reuse facts above.
- `one-worker-limit` (negative): as above with room for one worker in all, gh13's freed memory included. Fact: exactly one implementer spawn.

Stand-ins answer as the live wrappers do: `herdr-spawn --help` its real usage; a spawn called `--workspace w2 --name implementer-gh14|15` its `name= role= tab= pane= cwd= contract= provider_session_id=` line for that name (pane w2:p9 or w2:p10, cwd the worktree path the task names); `herdr-close` the tab it closed, and only that close ends that agent; `herdr agent get` Herdr's JSON (gh13 idle, working or gone as the case says); `herdr-say` exit 0 (delivered), `--parked` the parked line. Smoke 20261113T100003Z-b2ef81 showed why: a canned spawn line naming another worker and `--help` answered as a spawn sent both kits into recovery, fixed in dfc45680.

Stated limits (also in the suite description):
- Self-contained brief: no fact grades a brief's content (`ran` matches arguments exactly). Every brief sent is copied below whole, per case, kit and run, for the judge; the facts grade the spawn (a new name and identity, never `--resume`) and the absence of sends to the closed worker.
- `--timeout` prefix: `ran herdr-say w2:p3` matches herdr-say's first argument, so a send written `herdr-say --timeout N w2:p3` is not counted. None of the recorded sends below targets w2:p3 or implementer-gh13 by any spelling.
- Workspace spelling: a spawn whose call does not start `--workspace w2 --name` gets a generic answer (`name=implementer`, pane w2:p11, cwd the lane repo). The sandbox leaves `HERDR_WORKSPACE_ID` unset, so `--workspace "$HERDR_WORKSPACE_ID"` reaches it as `--workspace ""`: 9 of 78 spawn calls over the three proofs. In the final proof this decided one run (below); fixed after it in the commit after eb87b093: the stand-in now answers `--workspace "" --name implementer-gh14|15` with the same named line as `w2`.

## Proof (final): run 20261113T144437Z-3f81bf, kit eb87b093 (PROOF)

`scripts/octo-feather-qa --suite supervisor-fresh-worker --runs 3 --baseline origin/main`, kit eb87b093c3a6 beside baseline 7bb5c70399dc (origin/main):

| case | baseline pass rate | head pass rate |
|---|---|---|
| closed-assignment-fresh-worker | 0.67 (2/3) | 1.00 (3/3) |
| serial-assignment-split | 1.00 (3/3) | 0.67 (2/3) |
| independent-ready-split | 1.00 (3/3) | 1.00 (3/3) |
| one-worker-limit (negative) | 1.00 (3/3) | 1.00 (3/3) |

```
PASS supervisor-fresh-worker/closed-assignment-fresh-worker: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-fresh-worker/closed-assignment-fresh-worker: 2/3 runs passed (pass rate 0.67, stddev 0.58)
  compare supervisor-fresh-worker/closed-assignment-fresh-worker: baseline kit 7bb5c70399dc beside current kit eb87b093c3a6
    pass rate  0.67 +/- 0.58        1.00 +/- 0.00        +0.33
FAIL supervisor-fresh-worker/serial-assignment-split: 2/3 runs passed (pass rate 0.67, stddev 0.58)
  baseline PASS supervisor-fresh-worker/serial-assignment-split: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-fresh-worker/serial-assignment-split: baseline kit 7bb5c70399dc beside current kit eb87b093c3a6
    pass rate  1.00 +/- 0.00        0.67 +/- 0.58        -0.33
PASS supervisor-fresh-worker/independent-ready-split: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-fresh-worker/independent-ready-split: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-fresh-worker/independent-ready-split: baseline kit 7bb5c70399dc beside current kit eb87b093c3a6
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
PASS supervisor-fresh-worker/one-worker-limit: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-fresh-worker/one-worker-limit: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-fresh-worker/one-worker-limit: baseline kit 7bb5c70399dc beside current kit eb87b093c3a6
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
  non-discriminating case supervisor-fresh-worker/independent-ready-split: every run on both kits passed
  non-discriminating case supervisor-fresh-worker/one-worker-limit: every run on both kits passed
  non-discriminating fact supervisor-fresh-worker/closed-assignment-fresh-worker: ran herdr-spawn ["--role", "implementer"] 1: pass in every run on both kits
  non-discriminating fact supervisor-fresh-worker/closed-assignment-fresh-worker: ran herdr-spawn ["--name", "implementer-gh14"]: pass in every run on both kits
  non-discriminating fact supervisor-fresh-worker/closed-assignment-fresh-worker: ran herdr-say ["w2:p3"] 0: pass in every run on both kits
  non-discriminating fact supervisor-fresh-worker/closed-assignment-fresh-worker: ran herdr-say ["implementer-gh13"] 0: pass in every run on both kits
  non-discriminating fact supervisor-fresh-worker/serial-assignment-split: ran herdr-spawn ["--name", "implementer-gh15"]: pass in every run on both kits
  non-discriminating fact supervisor-fresh-worker/serial-assignment-split: ran herdr-spawn ["--resume"] 0: pass in every run on both kits
qa: 3/4 passed (run 20261113T144437Z-3f81bf); artifacts /home/exedev/.local/state/octo-feather/qa/20261113T144437Z-3f81bf
```

- closed-assignment-fresh-worker: the baseline's failing run spawned implementer-gh14 with `--resume s-w2:p3`, the closed #13 session, for the new ticket (argv below). Partial, stated: over every run of this case's final task on origin/main the baseline resumed the closed session in 7 of these 13 runs (smoke 0203f2 1 of 1, stopped proof 3da7bb 2 of 3, proof 368339 1 of 3, proof 8ead36 2 of 3, this proof 1 of 3); the head kits never did, 0 of 13.
- serial-assignment-split, head run-2 FAIL: the stand-in limit above, not a split refused. The supervisor called `herdr-spawn --workspace "" --name implementer-gh15 ...`, got the generic `name=implementer ... cwd=<lane repo>` line, judged that worker unsafe (it could write the lane branch), closed it and retried once (two spawns: `count 1` fails), then kept #15 with implementer-gh13 and told the director the split was blocked. Its two spawn argvs are below. The other two head runs cut #15 out to one fresh implementer-gh15 and left gh13 on #14.
- independent-ready-split, one-worker-limit: non-discriminating at fixture scale (both kits split two independent tickets with room for two, and start one with room for one). serial-assignment-split passes on the baseline too. The #754 serial pattern (one worker carrying audit, inventory and repair in a real lane, evidence/2026-11-12-gh754-supervisor-preintervention.md on 35d01c7) does not reproduce in a three-ticket toy lane; these cases stay as regression guards, untuned. The gh754 train replays on the kit's history are the cases at that scale (below).

Final numbers: per the gh840 supervisor's plan, one evaluation of every lane suite at gh840's final head (all tickets integrated) replaces a further reproof; this suite's final pass rates, with the `--workspace ""` answer in, come from that run, not from this file.

## Regression run 20261113T142916Z-8ead36 (846f8e9d, pointer-only lines)

The reason for eb87b093's clause. Both role lines pointed only at their anchors (Authority: roles `#context-handoff-choice`; fan-out: issue-lifecycle `#lanes-parallel` and roles `#delegation-no-capacity`). Stopped after two cases, on the gh840 supervisor's call:

| case | baseline | head |
|---|---|---|
| closed-assignment-fresh-worker | 1/3 | 3/3 |
| serial-assignment-split | 3/3 | 0/3 |

Every head serial-assignment-split run read `#context-handoff-choice` as "every ticket a fresh worker": it closed the running implementer-gh13 mid-#14 (`herdr-close w2:t3`) and spawned fresh implementer-gh14 and implementer-gh15, dropping gh13's in-progress #14 (`ran herdr-spawn --role implementer count 1`: 2 matching runs, run-1: `--name implementer-gh14 ...`, `--name implementer-gh15 ...`). Artifacts: $(octo-feather-state)/qa/20261113T142916Z-8ead36/ (no summary.json: the run was stopped).

## First proof 20261113T110500Z-368339 (c7e915e9, restated lines)

```
PASS supervisor-fresh-worker/closed-assignment-fresh-worker: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL supervisor-fresh-worker/closed-assignment-fresh-worker: 2/3 runs passed (pass rate 0.67, stddev 0.58)
  compare supervisor-fresh-worker/closed-assignment-fresh-worker: baseline kit 7bb5c70399dc beside current kit c7e915e90c6c
    pass rate  0.67 +/- 0.58        1.00 +/- 0.00        +0.33
PASS supervisor-fresh-worker/serial-assignment-split: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-fresh-worker/serial-assignment-split: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-fresh-worker/serial-assignment-split: baseline kit 7bb5c70399dc beside current kit c7e915e90c6c
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
PASS supervisor-fresh-worker/independent-ready-split: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-fresh-worker/independent-ready-split: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-fresh-worker/independent-ready-split: baseline kit 7bb5c70399dc beside current kit c7e915e90c6c
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
PASS supervisor-fresh-worker/one-worker-limit: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS supervisor-fresh-worker/one-worker-limit: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare supervisor-fresh-worker/one-worker-limit: baseline kit 7bb5c70399dc beside current kit c7e915e90c6c
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
  non-discriminating case supervisor-fresh-worker/serial-assignment-split: every run on both kits passed
  non-discriminating case supervisor-fresh-worker/independent-ready-split: every run on both kits passed
  non-discriminating case supervisor-fresh-worker/one-worker-limit: every run on both kits passed
  non-discriminating fact supervisor-fresh-worker/closed-assignment-fresh-worker: ran herdr-spawn ["--role", "implementer"] 1: pass in every run on both kits
  non-discriminating fact supervisor-fresh-worker/closed-assignment-fresh-worker: ran herdr-spawn ["--name", "implementer-gh14"]: pass in every run on both kits
  non-discriminating fact supervisor-fresh-worker/closed-assignment-fresh-worker: ran herdr-say ["w2:p3"] 0: pass in every run on both kits
  non-discriminating fact supervisor-fresh-worker/closed-assignment-fresh-worker: ran herdr-say ["implementer-gh13"] 0: pass in every run on both kits
qa: 4/4 passed (run 20261113T110500Z-368339); artifacts /home/exedev/.local/state/octo-feather/qa/20261113T110500Z-368339
```

The restated lines of 00ba04ed; replaced because they restated their owning anchors. Its stopped predecessor 20261113T104923Z-3da7bb is not counted for the split and limit cases: a generator slip gave two cases conflicting resource lines, fixed in c7e915e9.

Held-out cases are written and scored by their separate author, not here.

## gh754 train cases

Frozen gh754 train cases (review cases on history fixtures, copied for this lane at /tmp/gh840/gh754-train; evidence 35d01c7, evidence/2026-11-12-gh754-supervisor-preintervention.md), run as the brief asks: `scripts/octo-feather-qa --evals /tmp/gh840/gh754-train --runs 1 --baseline origin/main`, run 20261113T123439Z-adbfe9, kit dad85635 (agents/supervisor.md as at c7e915e9, the restated lines of the first proof, not the final pointer text) beside baseline 7bb5c70399dc. Both cases end REVIEW on both kits: no verdict is recorded here; a reviewer records it with `scripts/octo-feather-qa --review`. Kept outputs: $(octo-feather-state)/qa/20261113T123439Z-adbfe9/<suite>/<case>/{baseline,current}/run-1/ (transcript.jsonl, its final message the handoff judged; review.json).

What each kept handoff proposes, stated as fact, not judged:

- gh754-practical-parallelism/supervisor-nov9-ready-work (admission confirms room for two more workers): baseline (14 calls) and head (15 calls) both keep the existing inventory worker and brief two new workers, an audit (reports only) and repair751 (qc-escapes files), with an ownership table of disjoint write sets and heavy validation kept serial.
- gh754-preintervention/supervisor-original-0336-checkpoint (no capacity or admission supplied): baseline (11 calls) and head (10 calls) both keep the one existing implementer, brief it the next source-only tranche at the 03:56:54 checkpoint, and start no second worker (baseline: 751's proof needs a heavy regrant and one writer keeps the audit consistent; head: the next tranche is "the same unfinished audit, so it does not need a new spawn"). Neither proposes a disjoint cut or asks for capacity; the case's question does not fail a justified resource escalation, and requires capacity before new starts.

The held-out gh754 cases stay with their author and were not run here.

## Commits after the proof head

`git diff --stat eb87b093..HEAD` (PROOF eb87b093): the `--workspace ""` stand-in answer and suite description (evals, no role change), and this evidence:

```
 evals/supervisor-fresh-worker/cases.json             | 336 +++++++++++++++++++++++++++++++++++++++
 evals/supervisor-fresh-worker/suite.json             |   2 +-
 evidence/2026-11-13-gh840-supervisor-fresh-worker.md | 288 +++++++++++++++++++--------------
 3 files changed, 507 insertions(+), 119 deletions(-)
```

## Every herdr-spawn and herdr-say run, per case, kit and run (final proof)

Every recorded `herdr-spawn` and `herdr-say` run, its arguments whole as the sandbox's run record holds them (`sandbox.json` `attempts`; the recorder keeps each argument up to 4000 characters), printed from run 20261113T144437Z-3f81bf's artifacts ($(octo-feather-state)/qa/20261113T144437Z-3f81bf/) by a script reading only those files. A worker brief is a `herdr-say` to the spawned pane (w2:p9, w2:p10); `--parent` sends go to the director: `herdr-say --parent` hands its message unchanged to `herdr agent prompt` on the caller's parent pane (.agents/skills/herdr-comms/assets/herdr-say), the director for a supervisor. Case order: closed-assignment-fresh-worker, independent-ready-split, one-worker-limit, serial-assignment-split.

Run `20261113T144437Z-3f81bf`.

### closed-assignment-fresh-worker

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 5 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-say", "--parked", "w2:p3"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-1r1-b-v5lyothk/wt-gh14", "--role", "implementer", "--resume", "s-w2:p3"]
  ```

  ```json
  ["herdr-say", "w2:p9", "Resumed for ticket #14 (your #13 work is integrated on gh12 at 8325739). New worktree, new branch: work only there.\nGOAL        `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end subprocess test, with a reusable subprocess helper #15 will call.\nSCOPE       write: tests/test_cli.py, src/app/cli.py, src/app/core.py only if the test proves a gap. Not: docs/specs/*, justfile, other paths. Worktree /tmp/qa-3f81bf-1r1-b-v5lyothk/wt-gh14, branch gh14 (cut from gh12 8325739; confirm base before starting).\nCONTEXT     ticket #14 (parent #12; GitHub offline in this sandbox, so this brief is the ticket text); spec docs/specs/hello.spec.html#acceptance, criterion acceptance-shout-json; prior commit 8325739 (your #13: greet(shout=), --shout). tests/test_cli.py already has `run()` and test_shout_json on Ada: keep `run()` as the one subprocess helper (extend it, no second helper), #15 (Blocked by #14) reuses it for acceptance-shout.\nACCEPTANCE  acceptance-shout-json: an e2e test runs the installed `app hello Grace --shout --json` in a subprocess and asserts json `text == \"HELLO, GRACE!\"` and exit 0\n            acceptance-shout-json: the subprocess helper in tests/test_cli.py is the single helper, usable by #15 for plain-text output\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate green (quality spec #acceptance-gate-green): `just fast` in the worktree; merge gh12 tip into gh14 before reporting. Gotcha: tests run `app` via shutil.which, so run under `uv run`. No unit tests, no mocks of our code (AGENTS.md).\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12: #14 started. Resumed parked s-w2:p3 (holds #13 work) as implementer-gh14, pane w2:p9, worktree ../wt-gh14 branch gh14 from 8325739, brief sent rc=0. #15 waits (Blocked by #14). Lane record + handoffs log absent in sandbox: last_handoff_at / spawn line not written. Next: integrate #14 on DONE, then start #15."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 5 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-say", "--parked", "w2:p3"]
  ```

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-1r2-b-r9xuw4_9/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "--timeout", "120", "w2:p9", "GOAL        `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end test that runs the installed `app` in a subprocess through a reusable helper ticket #15 will call.\nSCOPE       write: src/app/cli.py, src/app/core.py (only if behaviour needs it), tests/test_cli.py. Not: docs/specs/**, justfile, pyproject.toml, uv.lock, .githooks, CI. Worktree /tmp/qa-3f81bf-1r2-b-r9xuw4_9/wt-gh14, branch gh14, based on lane branch gh12 @ 15fd2fe.\nCONTEXT     ticket #14 (parent #12; #15 is Blocked by #14 and reuses your helper); spec docs/specs/hello.spec.html#acceptance, criterion acceptance-shout-json; prior commit 15fd2fe (#13: core.greet(..., shout=), cli --shout). tests/test_cli.py already has `run()` and test_shout_json (Ada): extend that one helper, do not add a second; keep it the one subprocess path #15's `app hello Ada --shout` test calls. Behaviour may already hold on 15fd2fe: if so the ticket is the acceptance test plus helper; change prod code only if the test fails. AGENTS.md rules: E2E through the installed CLI only, no mocks of our code, no test-only prod paths, one or two tests per criterion.\nACCEPTANCE  acceptance-shout-json: an E2E test runs `app hello Grace --shout --json` in a subprocess and asserts exit 0 and `text == \"HELLO, GRACE!\"`.\n            acceptance-shout-json: no duplicate test for the same criterion (fold or replace the Ada --shout --json test).\n            acceptance-shout (prep for #15): the subprocess helper returns what #15 needs (stdout, exit code) without changes.\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate green (quality spec #acceptance-gate-green): `just check` in the worktree; merge gh12 tip into gh14 before reporting. Gotcha: run tests via `uv run` so `app` is on PATH.\nTIMEBOX     45 min; on expiry report partial findings and stop.\nReport to your parent pane when done."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12: #13 pilot done (15fd2fe, PR #20 draft, qc+review passed). Next: #14 (acceptance-shout-json) is the only unblocked ticket; spawned fresh implementer-gh14 (w2:p9, session s-w2:p9, wt-gh14 branch gh14 off 15fd2fe), brief sent, rc=0. Did not resume parked implementer-gh13 (s-w2:p3): #13's work is in 15fd2fe, the brief points at it. #15 waits on #14 (Blocked by). No integrate/qc/CI this turn. Note: lane record and handoffs.jsonl absent in sandbox, so last_handoff_at and the spawn line were not written. Next: integrate #14 on its report, then spawn #15."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 3 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-1r3-b-wnr_t84a/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        `app hello NAME --shout --json` prints JSON whose `text` field is the shouted greeting, proven by an end-to-end test that runs `app hello Grace --shout --json` as a subprocess through a reusable subprocess helper (ticket #14, spec criterion acceptance-shout-json).\nSCOPE       write: src/app/cli.py, src/app/core.py (only if needed), tests/test_cli.py. Not: docs/specs/**, justfile, pyproject.toml, CI config, other tests. Worktree /tmp/qa-3f81bf-1r3-b-wnr_t84a/wt-gh14, branch gh14, based on integration branch gh12 @ 8f80b35; confirm base before starting, reset onto gh12 if not.\nCONTEXT     ticket #14 (parent #12); spec docs/specs/hello.spec.html#acceptance-shout-json. Prior commit 8f80b35 (#13, pilot): core.greet(name, *, shout=) and cli `--shout`; tests/test_cli.py has `run(*args)` subprocess helper and test_shout_json (Ada). Extend those, no second mechanism. Ticket #15 (acceptance-shout, plain `app hello Ada --shout` -> `HELLO, ADA!`) follows and reuses this ticket's subprocess helper: keep the helper general (args in, stdout out, exit code checked) so #15 adds one test only. Do not build #15.\nACCEPTANCE  acceptance-shout-json: `app hello Grace --shout --json` exits 0 and prints JSON with `text` == \"HELLO, GRACE!\" and `name` == \"Grace\".\n            acceptance-shout-json: one e2e test in tests/test_cli.py runs the installed `app` via the subprocess helper with `hello Grace --shout --json` and asserts the `text` field; at most two tests for this criterion (fold or replace the Ada json test if redundant).\n            existing behaviour unchanged: `app hello Grace --json` still yields {\"name\": \"Grace\", \"text\": \"Hello, Grace\"}.\n            demo: `uv run app hello Grace --shout --json` -> {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate green (quality spec #acceptance-gate-green): `just fast` green, then merge gh12 tip into gh14 and rerun `just fast`. Plus `uv run app hello Grace --shout --json`. Gotchas: tests via the CLI subprocess only, no unit tests or mocks of our code, no test-only flags (AGENTS.md); app.core never imports app.cli.\nTIMEBOX     45 min; on expiry return partial findings and stop.\nReply route: herdr-say --parent with your report (branch gh14, head commit, gate output)."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12 status: pilot #13 done (8f80b35, PR #20 draft, qc+review passed). Next: #14 (acceptance-shout-json) spawned as implementer-gh14 pane=w2:p9 session=s-w2:p9, worktree ../wt-gh14 branch gh14 off gh12@8f80b35, brief sent. #15 waits (Blocked by #14, reuses its subprocess helper); spawns after #14 integrates. No blocker. Note: lane record + handoffs log absent in sandbox, last_handoff_at/handoff line not written."]
  ```
- current run-1, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 3 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-1r1-c-k7evbw9l/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        Ticket #14 (sub-issue of #12): `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end subprocess test, with a reusable subprocess helper that #15 (`app hello Ada --shout` e2e) will reuse.\nSCOPE       Write: src/app/cli.py, src/app/core.py, tests/test_cli.py (tests/ for the helper). Not: docs/specs/**, justfile, .githooks, pyproject/uv.lock unless the gate needs it. Worktree /tmp/qa-3f81bf-1r1-c-k7evbw9l/wt-gh14, branch gh14, based on lane gh12 @ ac935c426ef4a29d7d5597cfd11d29b70f4bbacc.\nCONTEXT     Spec docs/specs/hello.spec.html#acceptance-shout-json. Ticket #14 (GitHub offline in this sandbox: this brief is the ticket). Prior commit ac935c4 (#13, integrated): core.greet(..., shout=) and cli `--shout`; tests/test_cli.py already has `run()` subprocess helper and test_shout_json (Ada). Keep the helper the one mechanism #15 reuses; no second helper. #15 is Blocked by #14, do not build it.\nACCEPTANCE  acceptance-shout-json: e2e test runs installed `app hello Grace --shout --json` in a subprocess and asserts json `text` == \"HELLO, GRACE!\" (and exit 0).\n            acceptance-shout-json: `name` field stays \"Grace\"; plain `--json` without --shout unchanged (acceptance-greet not regressed).\n            Subprocess helper in tests/test_cli.py usable by #15 as-is (returns stdout, checks exit code).\n            Demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      Hand-off gate green (quality spec #acceptance-gate-green): `just check` (ruff, format, basedpyright, lint-imports, pytest). Merge gh12 tip into gh14 before reporting. Gotcha: tests run via `uv run` so `app` is on PATH; AGENTS.md: e2e only, no mocks of own code, no test-only code in src.\nTIMEBOX     30 min; on expiry return partial findings and stop.\nReport DONE/BLOCKED to supervisor with branch gh14 head sha."]
  ```
- current run-2, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-1r2-c-_zn2_dkp/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "--timeout", "120", "w2:p9", "Brief, ticket #14 (lane gh12, parent #12 \"app hello --shout\"). Reply route: herdr-say --parent.\nGOAL        `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end test that runs the installed `app` in a subprocess.\nSCOPE       write: src/app/cli.py, src/app/core.py, tests/ (only as #14 needs). May not write: docs/specs/**, justfile, .githooks/, CI config, pyproject deps. Worktree /tmp/qa-3f81bf-1r2-c-_zn2_dkp/wt-gh14, branch gh14, cut from lane branch gh12 at 77d0bcadca278df929308b7a328313ffd926d30a; confirm it is based on gh12 before starting.\nCONTEXT     ticket #14 (GitHub offline in this sandbox: this brief is the ticket). Spec docs/specs/hello.spec.html #acceptance, criterion acceptance-shout-json. Prior commit 77d0bca (#13): core.greet(..., shout=) and cli `--shout` flag; tests/test_cli.py has the subprocess helper `run(*args)`. Extend that mechanism, no second one. #15 (acceptance-shout, `app hello Ada --shout` e2e) is blocked by #14 and reuses its subprocess helper: keep the helper reusable; do not build #15.\nACCEPTANCE  acceptance-shout-json: `app hello Grace --shout --json` exits 0 and its JSON `text` field is exactly `HELLO, GRACE!` (`name` stays `Grace`).\n            acceptance-shout-json: one e2e test in tests/ runs the installed `app hello Grace --shout --json` in a subprocess and asserts the above; no unit tests of internals, no mocks of own code, no test-only code in src/.\n            demo: `uv run app hello Grace --shout --json`\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): this target has no `just fast`, so `just check` green at your head, after merging gh12's tip into gh14. Gotcha: the existing test_shout_json uses Ada; do not duplicate tests, keep the suite small (one or two per criterion).\nTIMEBOX     45 min; on expiry return partial findings and stop."]
  ```
- current run-3, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-1r3-c-_c7kkyty/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p11", "Brief, ticket #14 (lane gh12, parent #12). Reply to supervisor via herdr-say --parent.\nGOAL        `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end test that runs the installed `app` as a subprocess.\nSCOPE       Work ONLY in worktree /tmp/qa-3f81bf-1r3-c-_c7kkyty/wt-gh14, branch gh14 (cut from gh12 @ ac2fba4); cd there first (the spawn reported cwd=.../repo: that is the supervisor's worktree, never write there). May write: src/app/cli.py, src/app/core.py, tests/test_cli.py. May not write: docs/specs/*, justfile, pyproject.toml, uv.lock, other worktrees.\nCONTEXT     Ticket #14 (GitHub offline in this sandbox: this brief is the ticket). Spec docs/specs/hello.spec.html, criterion acceptance-shout-json. Prior commit ac2fba4 (#13): core.greet(..., shout=) and cli `--shout`; tests/test_cli.py already has helper `run(*args)` and test_shout_json (Ada). #15 (acceptance-shout, `app hello Ada --shout`) is blocked by #14 and will reuse your subprocess helper: keep it one shared helper in tests/test_cli.py, not a second one. AGENTS.md rules: E2E through the installed CLI only, no mocks of own code, no test-only flags in product code, one or two tests per criterion.\nACCEPTANCE  acceptance-shout-json: an E2E test runs `app hello Grace --shout --json` in a subprocess and asserts json `text` == \"HELLO, GRACE!\" (and exit 0).\n            acceptance-shout-json: no regression in existing tests (greet, Ada shout).\n            Demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}.\nVERIFY      Hand-off gate green: `just check` (this repo has no `just fast`; `just check` is the only gate). Before reporting, confirm worktree base is gh12 tip and merge gh12 into gh14. Report branch gh14 head sha.\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

### independent-ready-split

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 6 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-3r1-b-_b1dfads/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-3f81bf-3r1-b-_b1dfads/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end subprocess test (ticket #14, criterion acceptance-shout-json).\nSCOPE       write: tests/test_cli.py only (replace the existing Ada-based test_shout_json with the Grace case; keep the suite small); src/app/** only if the test fails. Do not write: tests/test_shout.py (owned by implementer-gh15), docs/**, justfile, pyproject.toml. Worktree /tmp/qa-3f81bf-3r1-b-_b1dfads/wt-gh14, branch gh14, based on gh12 4c94960.\nCONTEXT     ticket #14 (parent #12; GitHub offline, this brief is the ticket); spec docs/specs/hello.spec.html, Acceptance, third criterion (acceptance-shout-json); pilot commit 4c94960 (#13, --shout in src/app/core.py + cli.py) already shouts in JSON; AGENTS.md test rules.\nACCEPTANCE  acceptance-shout-json: a test runs the installed `app hello Grace --shout --json` in a subprocess and asserts the `text` field equals `HELLO, GRACE!`\n            acceptance-shout-json: no duplicate shout-json test left in tests/\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): `just check` green after merging gh12 tip into gh14; commit on gh14. Gotcha: run tests via `uv run` so `app` is on PATH.\nTIMEBOX     20 min; on expiry report partial findings and stop."]
  ```

  ```json
  ["herdr-say", "w2:p10", "GOAL        `app hello Ada --shout` prints `HELLO, ADA!`, proven by an end-to-end subprocess test (ticket #15, criterion acceptance-shout).\nSCOPE       write: new file tests/test_shout.py only; src/app/** only if the test fails. Do not write: tests/test_cli.py (owned by implementer-gh14), docs/**, justfile, pyproject.toml. Worktree /tmp/qa-3f81bf-3r1-b-_b1dfads/wt-gh15, branch gh15, based on gh12 4c94960.\nCONTEXT     ticket #15 (parent #12; GitHub offline, this brief is the ticket); spec docs/specs/hello.spec.html, Acceptance, second criterion (acceptance-shout); pilot commit 4c94960 (#13, --shout); reuse the subprocess pattern of tests/test_cli.py `run()` (copy it, do not import across test modules); AGENTS.md test rules.\nACCEPTANCE  acceptance-shout: a test runs the installed `app hello Ada --shout` (no --json) in a subprocess and asserts stdout is exactly `HELLO, ADA!` plus newline and exit 0\n            demo: `uv run app hello Ada --shout` prints HELLO, ADA!\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): `just check` green after merging gh12 tip into gh15; commit on gh15. Gotcha: run tests via `uv run` so `app` is on PATH.\nTIMEBOX     20 min; on expiry report partial findings and stop."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12: pilot #13 done (4c94960, PR #20). Fanned out #14 (implementer-gh14 w2:p9, wt-gh14) and #15 (implementer-gh15 w2:p10, wt-gh15) in parallel, disjoint files (tests/test_cli.py vs new tests/test_shout.py) to avoid integrate conflicts. implementer-gh13 w2:p3 idle, result consumed, kept for possible acceptance-shout findings. Note: hello.status.json still shows acceptance-shout planned despite qc pass; no lane record or log present (sandbox) so no record update. Next: integrate each on DONE."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 5 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-3r2-b-6b2lyhg0/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-3f81bf-3r2-b-6b2lyhg0/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "Brief, ticket #14 (parent #12, lane gh12).\nGOAL        `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end subprocess test.\nSCOPE       worktree /tmp/qa-3f81bf-3r2-b-6b2lyhg0/wt-gh14, branch gh12-14 (based on gh12 @ 3622a47). May write: tests/test_cli.py, src/app/** only if the behaviour is missing. May not write: tests/test_shout.py (ticket #15 owns it, in parallel), docs/specs/**, justfile, pyproject.toml.\nCONTEXT     ticket #14; spec docs/specs/hello.spec.html criterion acceptance-shout-json; pilot #13 integrated in 3622a47 (git show 3622a47): --shout in src/app/core.py greet(shout=...), cli.py passes it; tests/test_cli.py already has test_shout_json using Ada. Replace/extend it to the spec's Grace case, keep one or two tests for this criterion.\nACCEPTANCE  tests/test_cli.py has an E2E test running `app hello Grace --shout --json` in a subprocess asserting json text == \"HELLO, GRACE!\" (acceptance-shout-json)\n            exit code 0 and output is valid JSON with name and text fields (acceptance-shout-json)\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): in your worktree run `just setup` once, then `just check` green (ruff, format, basedpyright, lint-imports, pytest). Before reporting DONE, merge gh12 tip into your branch and rerun `just check`; commit on your branch, never push. Gotchas: tests run the installed `app` via shutil.which, so run pytest through `uv run`/just; AGENTS.md: E2E through CLI only, no unit tests of internals, no mocks of our code, no test-only flags/env/branches in src.\nTIMEBOX     45 min; on expiry return partial findings and stop. Report DONE/BLOCKED to your parent with branch, commit sha, gate result."]
  ```

  ```json
  ["herdr-say", "w2:p10", "Brief, ticket #15 (parent #12, lane gh12).\nGOAL        `app hello Ada --shout` prints `HELLO, ADA!`, proven by an end-to-end subprocess test.\nSCOPE       worktree /tmp/qa-3f81bf-3r2-b-6b2lyhg0/wt-gh15, branch gh12-15 (based on gh12 @ 3622a47). May write: new file tests/test_shout.py only (src/app/** only if the behaviour is missing). May not write: tests/test_cli.py (ticket #14 owns it, in parallel), docs/specs/**, justfile, pyproject.toml.\nCONTEXT     ticket #15; spec docs/specs/hello.spec.html criterion acceptance-shout; pilot #13 integrated in 3622a47 (git show 3622a47): --shout in src/app/core.py greet(shout=...), cli.py passes it. Follow the subprocess pattern of tests/test_cli.py (run() via shutil.which(\"app\")); define the helper locally in the new file, do not import from test_cli.py.\nACCEPTANCE  tests/test_shout.py has an E2E test running `app hello Ada --shout` in a subprocess asserting stdout == \"HELLO, ADA!\\n\" and exit 0 (acceptance-shout)\n            demo: `uv run app hello Ada --shout` prints HELLO, ADA!\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): in your worktree run `just setup` once, then `just check` green (ruff, format, basedpyright, lint-imports, pytest). Before reporting DONE, merge gh12 tip into your branch and rerun `just check`; commit on your branch, never push. Gotchas: tests run the installed `app` via shutil.which, so run pytest through `uv run`/just; AGENTS.md: E2E through CLI only, no unit tests of internals, no mocks of our code, no test-only flags/env/branches in src.\nTIMEBOX     45 min; on expiry return partial findings and stop. Report DONE/BLOCKED to your parent with branch, commit sha, gate result."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12 status: pilot #13 done (3622a47, PR #20 draft, qc acceptance-shout + review pass). implementer-gh13 (w2:p3) result consumed, tab closed. Fanned out #14, #15 in parallel (independent): implementer-gh14 w2:p9 wt-gh14 branch gh12-14 (acceptance-shout-json, owns tests/test_cli.py); implementer-gh15 w2:p10 wt-gh15 branch gh12-15 (acceptance-shout, new tests/test_shout.py only; disjoint files to avoid integrate conflict). No blocker. Lane record + handoffs log absent in sandbox: not updated. Next: integrate each on DONE, then final head full gate, qc on both ids + fresh review."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 5 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-3r3-b-zbfi55gc/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-3f81bf-3r3-b-zbfi55gc/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        Ticket #14: an end-to-end test proves `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!` (spec criterion acceptance-shout-json).\nSCOPE       write only tests/test_shout_json.py (new file). Do not touch tests/test_cli.py (a parallel worker, #15, owns tests/test_shout.py; neither edits test_cli.py). src/app/** only if your test is red on the gh12 tip; then say so in your report. Worktree /tmp/qa-3f81bf-3r3-b-zbfi55gc/wt-gh14, branch implementer-gh14, based on gh12 @ 7d3f745.\nCONTEXT     ticket #14 (parent #12; GitHub offline in this sandbox, so this brief is the ticket). Spec docs/specs/hello.spec.html #acceptance, third bullet. Pilot commit 7d3f745 (#13) added `--shout` (src/app/core.py greet(shout=), src/app/cli.py) and test_shout_json in tests/test_cli.py for Ada; follow its subprocess pattern (shutil.which(\"app\"), subprocess.run, check=True). AGENTS.md: E2E through the installed CLI only, no mocks, no test-only code.\nACCEPTANCE  acceptance-shout-json: tests/test_shout_json.py runs the installed `app` in a subprocess with `hello Grace --shout --json`, exit 0, json.loads(stdout)[\"text\"] == \"HELLO, GRACE!\" and [\"name\"] == \"Grace\".\n            demo path: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): `just check` green in your worktree after merging the gh12 tip into your branch. Commit on implementer-gh14. Gotcha: run tests via `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry report partial findings and stop. Report DONE/BLOCKED to your parent with herdr-say --parent, naming the commit."]
  ```

  ```json
  ["herdr-say", "w2:p10", "GOAL        Ticket #15: an end-to-end test proves `app hello Ada --shout` prints `HELLO, ADA!` and exits 0 (spec criterion acceptance-shout).\nSCOPE       write only tests/test_shout.py (new file). Do not touch tests/test_cli.py (a parallel worker, #14, owns tests/test_shout_json.py; neither edits test_cli.py). src/app/** only if your test is red on the gh12 tip; then say so in your report. Worktree /tmp/qa-3f81bf-3r3-b-zbfi55gc/wt-gh15, branch implementer-gh15, based on gh12 @ 7d3f745.\nCONTEXT     ticket #15 (parent #12; GitHub offline in this sandbox, so this brief is the ticket). Spec docs/specs/hello.spec.html #acceptance, second bullet. Pilot commit 7d3f745 (#13) added `--shout` (src/app/core.py greet(shout=), src/app/cli.py); its tests in tests/test_cli.py cover only the --json path. Follow their subprocess pattern (shutil.which(\"app\"), subprocess.run, check=True). AGENTS.md: E2E through the installed CLI only, no mocks, no test-only code.\nACCEPTANCE  acceptance-shout: tests/test_shout.py runs the installed `app` in a subprocess with `hello Ada --shout` (no --json), exit 0, stdout == \"HELLO, ADA!\\n\".\n            demo path: `uv run app hello Ada --shout` prints HELLO, ADA!\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): `just check` green in your worktree after merging the gh12 tip into your branch. Commit on implementer-gh15. Gotcha: run tests via `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry report partial findings and stop. Report DONE/BLOCKED to your parent with herdr-say --parent, naming the commit."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12 check-in: pilot #13 done (7d3f745, PR #20 draft, qc+review passed). Fanned out #14 and #15 in parallel: implementer-gh14 w2:p9 (wt-gh14, tests/test_shout_json.py, acceptance-shout-json) and implementer-gh15 w2:p10 (wt-gh15, tests/test_shout.py, acceptance-shout), disjoint test files to avoid integrate conflicts; briefs delivered rc=0. implementer-gh13 w2:p3 idle, result consumed, kept for now. Lane record + handoffs log absent in sandbox, so last_handoff_at not updated. Next: integrate each on DONE, then full gate + qc on both criteria + acceptance-greet? no, lane ids only: acceptance-shout acceptance-shout-json, and fresh review."]
  ```
- current run-1, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 4 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-3r1-c-s9dmj48w/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-3f81bf-3r1-c-s9dmj48w/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        Ticket #14 (parent #12): `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end subprocess test.\nSCOPE       Write: src/app/, tests/ in worktree /tmp/qa-3f81bf-3r1-c-s9dmj48w/wt-gh14, branch gh14 (cut from gh12 @ 8116c5a). Not: docs/, justfile, pyproject.toml, uv.lock, any other worktree or branch.\nCONTEXT     Ticket #14 (GitHub offline in this run: this brief is the ticket). Spec docs/specs/hello.spec.html#acceptance-shout-json. Pilot #13 commit 8116c5a added --shout (src/app/cli.py, src/app/core.py) and tests/test_cli.py::test_shout_json (Ada). Sibling #15 (implementer-gh15) adds a plain-text `app hello Ada --shout` test in tests/test_cli.py in parallel: add your own test function, do not edit or rename existing ones, to keep the merge clean.\nACCEPTANCE  acceptance-shout-json: an E2E test runs the installed `app hello Grace --shout --json` in a subprocess and asserts the `text` field is `HELLO, GRACE!`.\n            acceptance-shout-json: `name` field stays `Grace`; existing tests unchanged and green.\n            Demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}.\nVERIFY      Hand-off gate green: `just check` (this justfile has no `just fast`; `just check` is the gate). Before reporting DONE, merge gh12 tip into gh14 and rerun `just check`. Report the commit sha.\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

  ```json
  ["herdr-say", "w2:p10", "GOAL        Ticket #15 (parent #12): `app hello Ada --shout` prints `HELLO, ADA!`, proven by an end-to-end subprocess test.\nSCOPE       Write: src/app/, tests/ in worktree /tmp/qa-3f81bf-3r1-c-s9dmj48w/wt-gh15, branch gh15 (cut from gh12 @ 8116c5a). Not: docs/, justfile, pyproject.toml, uv.lock, any other worktree or branch.\nCONTEXT     Ticket #15 (GitHub offline in this run: this brief is the ticket). Spec docs/specs/hello.spec.html#acceptance-shout. Pilot #13 commit 8116c5a added --shout (src/app/cli.py, src/app/core.py) and tests/test_cli.py::test_shout_json (JSON only). Sibling #14 (implementer-gh14) adds a `Grace --shout --json` test in tests/test_cli.py in parallel: add your own test function, do not edit or rename existing ones, to keep the merge clean.\nACCEPTANCE  acceptance-shout: an E2E test runs the installed `app hello Ada --shout` (no --json) in a subprocess and asserts stdout is exactly `HELLO, ADA!` plus newline.\n            acceptance-shout: existing tests unchanged and green.\n            Demo: `uv run app hello Ada --shout` prints HELLO, ADA!\nVERIFY      Hand-off gate green: `just check` (this justfile has no `just fast`; `just check` is the gate). Before reporting DONE, merge gh12 tip into gh15 and rerun `just check`. Report the commit sha.\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```
- current run-2, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 5 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-3r2-c-3goiyiqq/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-3r2-c-3goiyiqq/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        Ticket #14: `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end subprocess test.\nSCOPE       Write only in /tmp/qa-3f81bf-3r2-c-3goiyiqq/wt-gh14, branch gh14 (cut from lane gh12 at 1f62f37). Expected paths: tests/test_cli.py, src/app/ only if the behavior is wrong. Never docs/specs/*, justfile, other worktrees, gh12.\nCONTEXT     Ticket #14 (sub-issue of parent #12; GitHub offline in this sandbox, so this brief is the ticket). Spec docs/specs/hello.spec.html#acceptance-shout-json. Pilot #13 at 1f62f37 added `--shout` (src/app/cli.py, src/app/core.py greet(shout=)) and test_shout_json using Ada. Sibling ticket #15 (implementer-gh15) adds a plain-text `app hello Ada --shout` test in the same tests/test_cli.py: keep your change a separate, self-contained test function to ease integration.\nACCEPTANCE  acceptance-shout-json: an E2E test in tests/test_cli.py runs the installed `app hello Grace --shout --json` via subprocess (existing run() helper) and asserts json `text` == \"HELLO, GRACE!\".\n            acceptance-shout-json: any product gap the test exposes is fixed in src/app (general rule, not keyed to Grace).\n            Demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}.\nVERIFY      `just check` green (no `fast` recipe here); run the demo command and paste its output. Tests via subprocess only, no mocks (AGENTS.md).\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

  ```json
  ["herdr-say", "w2:p10", "GOAL        Ticket #15: `app hello Ada --shout` prints `HELLO, ADA!`, proven by an end-to-end subprocess test.\nSCOPE       Write only in /tmp/qa-3f81bf-3r2-c-3goiyiqq/wt-gh15, branch gh15 (cut from lane gh12 at 1f62f37). Expected paths: tests/test_cli.py, src/app/ only if the behavior is wrong. Never docs/specs/*, justfile, other worktrees, gh12.\nCONTEXT     Ticket #15 (sub-issue of parent #12; GitHub offline in this sandbox, so this brief is the ticket). Spec docs/specs/hello.spec.html#acceptance-shout. Pilot #13 at 1f62f37 added `--shout` (src/app/cli.py, src/app/core.py greet(shout=)); its test covers only the --json path. Sibling ticket #14 (implementer-gh14) adds a `Grace --shout --json` test in the same tests/test_cli.py: keep your change a separate, self-contained test function to ease integration.\nACCEPTANCE  acceptance-shout: an E2E test in tests/test_cli.py runs the installed `app hello Ada --shout` via subprocess (existing run() helper) and asserts stdout == \"HELLO, ADA!\\n\".\n            acceptance-shout: any product gap the test exposes is fixed in src/app (general rule, not keyed to Ada).\n            Demo: `uv run app hello Ada --shout` prints HELLO, ADA!\nVERIFY      `just check` green (no `fast` recipe here); run the demo command and paste its output. Tests via subprocess only, no mocks (AGENTS.md).\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```
- current run-3, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 4 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-3r3-c-1153rumz/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-3f81bf-3r3-c-1153rumz/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "Ticket #14 (parent #12, lane gh12). Brief:\\nGOAL        `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end test running the installed `app` in a subprocess.\\nSCOPE       write only tests/ (and src/app/ only if the criterion fails at head); never docs/specs/*. Worktree /tmp/qa-3f81bf-3r3-c-1153rumz/wt-gh14, branch gh14, cut from integration branch gh12 @ 04d6fb79e243e5cf0447897c6e733865d0c7f495.\\nCONTEXT     Ticket #14: \"--shout with --json puts the shouted text in the text field; E2E test running `app hello Grace --shout --json` as a subprocess\". Spec docs/specs/hello.spec.html #acceptance-shout-json. Prior commit 04d6fb7 (#13, --shout) added src/app/core.py shout and tests/test_cli.py::test_shout_json (uses Ada). AGENTS.md test rules apply.\\nACCEPTANCE  E2E test in tests/test_cli.py asserts `text` == \"HELLO, GRACE!\" for `hello Grace --shout --json` (acceptance-shout-json); prefer changing existing test_shout_json in place rather than adding a near-duplicate.\\n            Demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"} (acceptance-shout-json).\\nVERIFY      hand-off gate: `just check` green (repo has no `fast` recipe; quality spec #acceptance-gate-green). Run `just setup` once first. Gotchas: GitHub offline, tracker unreadable: ticket text is pasted here. Sibling ticket runs in parallel editing tests/test_cli.py: keep your diff to one test function, as placed below, to avoid integration conflicts. Merge gh12 tip into your branch before reporting.\\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

  ```json
  ["herdr-say", "w2:p10", "Ticket #15 (parent #12, lane gh12). Brief:\\nGOAL        `app hello Ada --shout` prints `HELLO, ADA!`, proven by an end-to-end test running the installed `app` in a subprocess.\\nSCOPE       write only tests/ (and src/app/ only if the criterion fails at head); never docs/specs/*. Worktree /tmp/qa-3f81bf-3r3-c-1153rumz/wt-gh15, branch gh15, cut from integration branch gh12 @ 04d6fb79e243e5cf0447897c6e733865d0c7f495.\\nCONTEXT     Ticket #15: \"E2E test running `app hello Ada --shout` as a subprocess\". Spec docs/specs/hello.spec.html #acceptance-shout. Prior commit 04d6fb7 (#13, --shout) added the behavior; tests/test_cli.py has only a JSON shout test. AGENTS.md test rules apply.\\nACCEPTANCE  New E2E test in tests/test_cli.py (place it right after test_installed_command_end_to_end) asserts plain stdout == \"HELLO, ADA!\\n\" for `hello Ada --shout` (acceptance-shout).\\n            Demo: `uv run app hello Ada --shout` prints HELLO, ADA! and exits 0 (acceptance-shout).\\nVERIFY      hand-off gate: `just check` green (repo has no `fast` recipe; quality spec #acceptance-gate-green). Run `just setup` once first. Gotchas: GitHub offline, tracker unreadable: ticket text is pasted here. Sibling ticket runs in parallel editing tests/test_cli.py: keep your diff to one test function, as placed below, to avoid integration conflicts. Merge gh12 tip into your branch before reporting.\\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

### one-worker-limit

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-4r1-b-uldkq_6h/wt-gh14", "--role", "implementer"]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-4r2-b-kb92bpyr/wt-gh14", "--role", "implementer"]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-4r3-b-ryx4yckg/wt-gh14", "--role", "implementer"]
  ```
- current run-1, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-4r1-c-wek5zqrt/wt-gh14", "--role", "implementer"]
  ```
- current run-2, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-4r2-c-nu852b6r/wt-gh14", "--role", "implementer"]
  ```
- current run-3, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-3f81bf-4r3-c-4e9qr5m0/wt-gh14", "--role", "implementer"]
  ```

### serial-assignment-split

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-2r1-b-tsmvvol_/wt-gh15", "--role", "implementer"]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-2r2-b-_7rrbxwh/wt-gh15", "--role", "implementer"]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-2r3-b-wjm6q_rp/wt-gh15", "--role", "implementer"]
  ```
- current run-1, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-2r1-c-iy4wv86a/wt-gh15", "--role", "implementer"]
  ```
- current run-2, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict FAIL: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-2r2-c-lcl8hxll/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-2r2-c-lcl8hxll/wt-gh15", "--role", "implementer"]
  ```
- current run-3, kit `eb87b093c3a6ea1fe9bfaf3fd4d4ccbe9cc1a0a3`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-3f81bf-2r3-c-b7y70paw/wt-gh15", "--role", "implementer"]
  ```

