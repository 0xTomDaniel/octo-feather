# gh840 #876: fresh worker per independent assignment, ready work cut apart within limits

Criterion: roles `#acceptance-fresh-independent-worker` (rule owners: roles `#general-purpose-workers`, issue-lifecycle `#lanes`), with the #754 supervisor half (serial planning). Suite `evals/supervisor-fresh-worker`, graded on the supervisor's `herdr-spawn` and `herdr-say` runs in the qa sandbox's run record, with the `ran` fact's `count` (schema.md, Run record). Herdr is stood in by each case's `stand_ins` (schema.md, Case), as in the pilot (evidence/2026-11-13-gh840-supervisor-notifications.md, Delivery).

Smoke: agents/supervisor.md evals/supervisor-fresh-worker/ runs at `--runs 1 --baseline origin/main`: 20261113T094831Z-a8d9e9 (first draft, at e1d4d4da before the role change), 20261113T100003Z-b2ef81 and 20261113T101558Z-0203f2 (redrafted cases, role change in); then the stopped proof 20261113T104923Z-3da7bb and the 3-run proof 20261113T110500Z-368339 at c7e915e9.
Removed: agents/supervisor.md "run the implementers of independent tickets (no `Blocked by` between them) in parallel when you judge it practical. That is your call, not a count." (#754: one implementer serially carried independent ready work; replaced by one implementer per unblocked ready ticket within actual resource limits, pointing to issue-lifecycle `#lanes`).

## Role change

agents/supervisor.md, two sites (00ba04ed): Authority, by the spawn naming rule: each independent assignment, a closed one's next ticket included, gets a fresh spawn and a self-contained brief; only the same unfinished assignment resumes (roles spec `#general-purpose-workers`). Delivery, the fan-out: each ready ticket no `Blocked by` holds gets its own implementer, as many at once as actual resource limits allow (issue-lifecycle spec `#lanes`), never queued behind another worker's assignment, an untouched one cut out of a running worker's assignment.

## Cases

All four: lane gh12 after its pilot (#13 integrated at the head, fixtures lane-shout-main and lane-shout-wip), remaining tickets #14 and #15, implementer-gh13 (pane w2:p3, session s-w2:p3) the #13 worker.

- `closed-assignment-fresh-worker`: implementer-gh13 parked after DONE, its session holding the #13 code #14 extends; #15 Blocked by #14; room for two. Facts: exactly one `herdr-spawn --role implementer`, `--name implementer-gh14`, no `herdr-spawn --resume`, no `herdr-say w2:p3` or `herdr-say implementer-gh13`.
- `serial-assignment-split`: implementer-gh13 running, briefed #14 and #15 as one serial assignment, on #14; #15 untouched; room for two. Facts: exactly one implementer spawn, `--name implementer-gh15`, no `--resume`.
- `independent-ready-split`: implementer-gh13 idle after DONE; #14 and #15 independent; room for two. Facts: exactly two implementer spawns, gh14 and gh15, and the no-reuse facts above.
- `one-worker-limit` (negative): as above with room for one worker in all, gh13's freed memory included. Fact: exactly one implementer spawn.

Stand-ins answer as the live wrappers do: `herdr-spawn --help` its real usage; a spawn called `--workspace w2 --name implementer-gh14|15` its `name= role= tab= pane= cwd= contract= provider_session_id=` line for that name (pane w2:p9 or w2:p10, cwd the worktree path the task names); `herdr-close` the tab it closed, and only that close ends that agent; `herdr agent get` Herdr's JSON (gh13 idle, working or gone as the case says); `herdr-say` exit 0 (delivered), `--parked` the parked line. Smoke 20261113T100003Z-b2ef81 showed why: a canned spawn line naming another worker and `--help` answered as a spawn sent both kits into recovery (double spawns, a worker closed by a wrong close), fixed in dfc45680.

Stated limits (also in the suite description):
- Self-contained brief: no fact grades a brief's content (`ran` matches arguments exactly). Every brief sent is copied below, per case, kit and run, for the judge; the facts grade the spawn (a new name and identity, never `--resume`) and the absence of sends to the closed worker.
- `--timeout` prefix: `ran herdr-say w2:p3` matches herdr-say's first argument, so a send written `herdr-say --timeout N w2:p3` is not counted. In the proof, 10 recorded sends start `--timeout` (listed below); none targets w2:p3 or implementer-gh13.
- A spawn whose call does not start `--workspace w2 --name` gets a generic answer (pane w2:p11); none in the proof did.

## Proof

`scripts/octo-feather-qa --suite supervisor-fresh-worker --runs 3 --baseline origin/main`, run 20261113T110500Z-368339, kit c7e915e90c6c (PROOF below) beside baseline 7bb5c70399dc (origin/main):

| case | baseline pass rate | head pass rate |
|---|---|---|
| closed-assignment-fresh-worker | 0.67 (2/3) | 1.00 (3/3) |
| serial-assignment-split | 1.00 (3/3) | 1.00 (3/3) |
| independent-ready-split | 1.00 (3/3) | 1.00 (3/3) |
| one-worker-limit (negative) | 1.00 (3/3) | 1.00 (3/3) |

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

- closed-assignment-fresh-worker: baseline run-2 spawned `herdr-spawn --workspace w2 --name implementer-gh14 --label worker-2 --cwd .../wt-gh14 --role implementer --resume s-w2:p3`, the closed #13 session, for the new ticket. Partial, stated: the baseline fails 1 of 3 here; over every run of this case's final form on origin/main it resumed the closed session in 4 of 7 (smoke 20261113T101558Z-0203f2 run 1, stopped proof 20261113T104923Z-3da7bb runs 1 and 3, this proof run 2); at the head 0 of 7 (same runs).
- serial-assignment-split, independent-ready-split, one-worker-limit: non-discriminating at fixture scale. Both kits cut #15 out of the running worker's assignment, start two workers for two independent tickets with room, and one with room for one. The #754 serial pattern (one worker carrying audit, inventory and repair in a real lane, evidence/2026-11-12-gh754-supervisor-preintervention.md on 35d01c7) did not reproduce in a three-ticket toy lane; the cases stay as regression guards, untuned. The gh754 train replays on the real kit history are the cases at that scale (below).
- Earlier, at e1d4d4da (the gh840 tip before the role change), smoke 20261113T094831Z-a8d9e9 saw the head kit start two workers with room for one; that task's resource line was ambiguous (room beside open panes, one of them closable) and was reworded before the proof.

The stopped proof 20261113T104923Z-3da7bb (at 20a68c4e) is not counted for the split and limit cases: a generator slip gave independent-ready-split and one-worker-limit two conflicting resource lines and no DONE line, fixed in c7e915e9. Its closed-assignment and serial-split runs had the final tasks: closed-assignment baseline 1/3, head 3/3; serial-split 3/3 on both.

Held-out cases are written and scored by their separate author, not here.

## gh754 train cases

Frozen gh754 train cases (review cases on history fixtures, copied for this lane at /tmp/gh840/gh754-train; evidence 35d01c7, evidence/2026-11-12-gh754-supervisor-preintervention.md), run as the brief asks: `scripts/octo-feather-qa --evals /tmp/gh840/gh754-train --runs 1 --baseline origin/main`, run 20261113T123439Z-adbfe9, kit dad85635 (agents/supervisor.md identical to the proof head c7e915e9) beside baseline 7bb5c70399dc. Both cases end REVIEW on both kits: no verdict is recorded here; a reviewer records it with `scripts/octo-feather-qa --review`. Kept outputs: $(octo-feather-state)/qa/20261113T123439Z-adbfe9/<suite>/<case>/{baseline,current}/run-1/ (transcript.jsonl, its final message the handoff judged; review.json).

What each kept handoff proposes, stated as fact, not judged:

- gh754-practical-parallelism/supervisor-nov9-ready-work (admission confirms room for two more workers): baseline (14 calls) and head (15 calls) both keep the existing inventory worker and brief two new workers, an audit (reports only) and repair751 (qc-escapes files), with an ownership table of disjoint write sets and heavy validation kept serial.
- gh754-preintervention/supervisor-original-0336-checkpoint (no capacity or admission supplied): baseline (11 calls) and head (10 calls) both keep the one existing implementer, brief it the next source-only tranche at the 03:56:54 checkpoint, and start no second worker (baseline: 751's proof needs a heavy regrant and one writer keeps the audit consistent; head: the next tranche is "the same unfinished audit, so it does not need a new spawn"). Neither proposes a disjoint cut or asks for capacity; the case's question does not fail a justified resource escalation, and requires capacity before new starts.

The held-out gh754 cases stay with their author and were not run here.

## Commits after the proof head

`git diff --stat c7e915e9..HEAD` (PROOF c7e915e9; evidence, docs and the qc.toml metadata entry only, before the merge of the gh840 tip that follows):

```
 docs/owed-evals/876.md                               |   5 +
 evidence/2026-11-13-gh840-supervisor-fresh-worker.md | 393 +++++++++++++++++++++++++++++++++++++++
 qc.toml                                              |   7 +
 3 files changed, 405 insertions(+)
```

## Every herdr-spawn and herdr-say run, per case, kit and run

Every recorded `herdr-spawn` and `herdr-say` run, its arguments as the sandbox's run record holds them (`sandbox.json` `attempts`, each argument up to 4000 characters), printed from run 20261113T110500Z-368339's artifacts ($(octo-feather-state)/qa/20261113T110500Z-368339/) by a script reading only those files. A worker brief is a `herdr-say` to the spawned pane (w2:p9, w2:p10); `--parent` sends are to the director. Case order: closed-assignment-fresh-worker, independent-ready-split, one-worker-limit, serial-assignment-split.

Run `20261113T110500Z-368339`.

### closed-assignment-fresh-worker

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 4 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-1r1-b-b8lyg_69/repo/../wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        `app hello Grace --shout --json` run as a subprocess prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end test built on a reusable subprocess helper (ticket #14, parent #12).\nSCOPE       write: tests/test_cli.py, and src/app/cli.py / src/app/core.py only if the behaviour needs it. Not: docs/specs/*, justfile, other tickets' scope (#15, the `app hello Ada --shout` e2e test, is NOT yours). Worktree /tmp/qa-368339-1r1-b-b8lyg_69/wt-gh14, branch gh14, cut from integration branch gh12 @ 1ad594a.\nCONTEXT     ticket #14 (tracker; GitHub offline in this sandbox, so this brief is the ticket); spec docs/specs/hello.spec.html criterion acceptance-shout-json. Prior commit 1ad594a (#13): core.greet(..., shout=) and cli `--shout`; tests/test_cli.py has test_shout_json (in-process) and test_installed_command_end_to_end (inline subprocess). #15 (Blocked by #14) will reuse your subprocess helper for `app hello Ada --shout`: make it a small module-level helper in tests/test_cli.py taking argv, returning the completed process, and switch test_installed_command_end_to_end to it.\nACCEPTANCE  acceptance-shout-json: e2e test runs the installed `app` as a subprocess with `hello Grace --shout --json`, asserts exit 0 and json `text` == `HELLO, GRACE!`.\n            acceptance-shout-json: the subprocess helper is shared (existing e2e test uses it), no test detail in production code.\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate green: `just fast` if the recipe exists, else `just check`. Then run the demo command and paste its output. Merge gh12 tip into gh14 before reporting.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12 status: pilot #13 done (head 1ad594a, PR #20 draft, qc acceptance-shout + review passed). Fan-out: #14 frontier only (#15 Blocked by #14). Spawned implementer-gh14 fresh (pane w2:p9, session s-w2:p9, worktree ../wt-gh14 branch gh14 @ 1ad594a), brief delivered rc=0. Did not resume parked s-w2:p3: per-ticket worker name, #13 context is in commit 1ad594a. Next: on #14 DONE, integrate, then spawn implementer-gh15. Lane record + handoffs log absent in sandbox: last_handoff_at and spawn line not written. No blocker."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict FAIL: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-368339-1r2-b-33yj37ne/repo/../wt-gh14", "--role", "implementer", "--resume", "s-w2:p3"]
  ```

  ```json
  ["herdr-say", "w2:p9", "Brief: ticket #14 (lane gh12, parent #12). If this conversation holds your #13 work, that is context only: #13 is integrated; this is a new unit in a new worktree.\nGOAL        `app hello Grace --shout --json` run as a subprocess prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end subprocess test built on a reusable subprocess helper that #15 will reuse.\nSCOPE       write: tests/test_cli.py; src/app/cli.py and src/app/core.py only if the test proves a change needed. Not: docs/specs/**, justfile, pyproject.toml, .github/**, AGENTS.md. Worktree /tmp/qa-368339-1r2-b-33yj37ne/wt-gh14, branch gh14, based on gh12 @ d4977211b947cf96a02c4325f21ac9143fa6d7a5.\nCONTEXT     ticket #14 (GitHub offline in this run: this brief is its text); spec docs/specs/hello.spec.html#acceptance-shout-json; prior commit d4977211 (#13: core.greet(..., shout=), cli --shout, in-process test_shout_json). Existing subprocess pattern: tests/test_cli.py::test_installed_command_end_to_end; factor it into one helper (e.g. run_app(*args) -> CompletedProcess) and keep that test using it. #15 (Blocked by #14) will add `app hello Ada --shout` E2E with the same helper.\nACCEPTANCE  acceptance-shout-json: a subprocess test runs the installed `app hello Grace --shout --json` and asserts json `text` == \"HELLO, GRACE!\" (and `name` == \"Grace\")\n            acceptance-shout-json: one shared subprocess helper in tests/test_cli.py, used by both subprocess tests; no test-only code in src/\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): `just check` green in your worktree; merge gh12 tip into gh14 before reporting. Gotcha: run tests via `uv run` so `app` is on PATH. Keep suite small: one or two tests per criterion.\nTIMEBOX     30 min; on expiry return partial findings and stop.\nReport to me (supervisor) per your role's Output."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 3 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-1r3-b-ph96c474/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        `app hello Grace --shout --json` run as a subprocess prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end test through a reusable subprocess helper (ticket #14).\nSCOPE       write: tests/test_cli.py; src/app/cli.py and src/app/core.py only if the e2e test exposes a defect. Not: docs/specs/**, justfile, pyproject.toml, any other path. Worktree /tmp/qa-368339-1r3-b-ph96c474/wt-gh14, branch gh14 (cut from gh12 @ ef33c89).\nCONTEXT     ticket #14 (sub-issue of #12; #15 is Blocked by it and will reuse your helper for `app hello Ada --shout`). Spec docs/specs/hello.spec.html#acceptance-shout-json. Prior commit ef33c89 (#13: core.greet(..., shout=), cli `--shout`, in-process test_shout_json). Existing subprocess pattern: tests/test_cli.py::test_installed_command_end_to_end. AGENTS.md rules: tests through the CLI only, no mocks of our code, no test detail in production code, 1-2 tests per criterion.\nACCEPTANCE  - tests/test_cli.py has one subprocess helper (finds `app` on PATH, runs it with given args, returns the completed process) that test_installed_command_end_to_end also uses; no duplicated subprocess code. (acceptance-shout-json)\n            - a new e2e test runs `app hello Grace --shout --json` via the helper and asserts exit 0 and json `text` == \"HELLO, GRACE!\". (acceptance-shout-json)\n            - demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate green (quality spec #acceptance-gate-green): `just fast` and `just check` in the worktree; merge gh12 tip into gh14 before reporting. Gotcha: run tests through `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry return partial findings and stop.\nReport to your parent pane with herdr-say --parent per your role's Output."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12 status: pilot #13 done at ef33c89 (qc acceptance-shout + review pass, draft PR #20). Next: #14 implementer-gh14 spawned fresh (pane w2:p9, session s-w2:p9, wt ../wt-gh14, branch gh14 off ef33c89), brief sent; #15 waits (Blocked by #14). Did not resume parked s-w2:p3: name rule is per ticket and #13 work is in ef33c89, pointed to in brief. Lane record + handoffs log absent in sandbox: last_handoff_at and spawn line not written. Next action: integrate #14 on its DONE, then spawn #15."]
  ```
- current run-1, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 3 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-1r1-c-6c2oahca/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "--timeout", "120", "w2:p9", "GOAL        `app hello Grace --shout --json` run as an installed subprocess prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end test built on a reusable subprocess helper that ticket #15 will call.\nSCOPE       write: tests/test_cli.py; src/app/cli.py and src/app/core.py only if the behaviour is wrong. Not: docs/specs/**, justfile, pyproject.toml, uv.lock, any other path. Worktree /tmp/qa-368339-1r1-c-6c2oahca/wt-gh14, branch gh14, based on lane branch gh12 at 08be3891b4140beff6ebadbf6ab0513da1c4081e.\nCONTEXT     Ticket #14 (parent #12). Spec docs/specs/hello.spec.html#acceptance-shout-json. Prior commit 08be389 (#13): core.greet(name, shout=) and cli `--shout`; tests/test_cli.py already has in-process test_shout_json and test_installed_command_end_to_end (inline subprocess.run). AGENTS.md test rules: E2E through the `app` command, no unit tests, no mocks of our code, no test-only production code. Ticket #15 (acceptance-shout, `app hello Ada --shout`) is Blocked by this one and will reuse your helper: make it a plain module-level function in tests/test_cli.py (e.g. `run_app(*args) -> subprocess.CompletedProcess[str]`, resolves `app` via shutil.which), and move test_installed_command_end_to_end onto it.\nACCEPTANCE  acceptance-shout-json: an E2E test runs `app hello Grace --shout --json` as a subprocess via the helper and asserts json `text` == \"HELLO, GRACE!\".\n            acceptance-shout-json: the helper is reusable by #15 (one function, takes argv, returns the completed process).\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      hand-off gate green (quality spec #acceptance-gate-green): `just check` in the worktree; then `uv run app hello Grace --shout --json`. Merge gh12 tip into gh14 before reporting. Gotcha: run pytest via `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry report partial findings and stop.\nReport to supervisor via herdr-say --parent."]
  ```
- current run-2, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 3 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-368339-1r2-c-vcurj5p5/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "--timeout", "120", "w2:p9", "GOAL        Add an end-to-end test that runs the installed `app hello Grace --shout --json` as a subprocess and asserts the JSON `text` field is `HELLO, GRACE!`, via a reusable subprocess helper in tests/test_cli.py (ticket #15 will reuse it); fix product code only if that test fails.\nSCOPE       Write: tests/test_cli.py; src/app/cli.py and src/app/core.py only if the e2e test exposes a defect. Not: docs/specs/**, justfile, pyproject.toml, uv.lock, .githooks, CI. Do not write the `app hello Ada --shout` e2e test (that is #15). Worktree /tmp/qa-368339-1r2-c-vcurj5p5/wt-gh14, branch gh14, cut from lane branch gh12 @ f0f8103.\nCONTEXT     Ticket #14 (parent #12). Spec docs/specs/hello.spec.html#acceptance-shout-json. Prior commit f0f8103 (#13): core.greet(..., shout=) and cli `--shout`; tests/test_cli.py already has in-process test_shout_json and subprocess test_installed_command_end_to_end (shutil.which(\"app\") + subprocess.run): extract its subprocess call into a helper both use. AGENTS.md rules: tests through CLI only, no mocks of own code, no test-only code in src.\nACCEPTANCE  1. tests/test_cli.py has one subprocess helper (runs the installed `app` with args, returns parsed stdout or CompletedProcess) used by test_installed_command_end_to_end and the new test (acceptance-shout-json).\n            2. New e2e test: subprocess `app hello Grace --shout --json` exits 0, json[\"text\"] == \"HELLO, GRACE!\" (acceptance-shout-json).\n            3. No production-code change unless needed to make (2) pass; no test-only flags/env/branches in src.\n            4. Demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}.\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): `just check` green in the worktree (`just setup` first if .venv missing). Merge gh12 tip into gh14 before reporting. Gotcha: run pytest via `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry, commit what you have, report partial findings, stop.\nReport DONE/BLOCKED to supervisor with branch, head sha, gate result."]
  ```
- current run-3, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-368339-1r3-c-vtzrkcdj/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p11", "GOAL        Ticket #14 (sub-issue of #12): `app hello Grace --shout --json` prints JSON whose `text` field is `HELLO, GRACE!`, proven by an end-to-end test that runs the installed `app` command as a subprocess through a reusable subprocess helper.\nSCOPE       Worktree /tmp/qa-368339-1r3-c-vtzrkcdj/wt-gh14, branch gh14 (cut from lane gh12 head b58f260; confirm `git merge-base --is-ancestor b58f260 HEAD`, reset onto gh12 if not). May write: tests/test_cli.py; src/app/cli.py and src/app/core.py only if the demo fails. May not write: docs/ (spec, status file), justfile, pyproject.toml, uv.lock, any other worktree.\nCONTEXT     Spec docs/specs/hello.spec.html#acceptance-shout-json. Prior commit b58f260 (#13): core.greet(name, *, shout=False) upper-cases text and appends SHOUT_SUFFIX \"!\"; cli.py `--shout` flag passes shout=; in-process test test_shout_json already covers Ada. Existing E2E pattern: test_installed_command_end_to_end (shutil.which(\"app\") + subprocess.run). Factor that into one small helper, e.g. `run_app(*args) -> subprocess.CompletedProcess[str]`, reused by the existing E2E test and the new one: ticket #15 (acceptance-shout, `app hello Ada --shout`) is Blocked by #14 and will reuse it. AGENTS.md: tests through the CLI only, no mocks of our code, no test-only code in production, keep suite small.\nACCEPTANCE  acceptance-shout-json: new E2E test runs `app hello Grace --shout --json` via the helper and asserts json.loads(stdout)[\"text\"] == \"HELLO, GRACE!\" (and name == \"Grace\").\n            acceptance-shout-json: helper is a module-level function in tests/test_cli.py; the existing E2E test uses it.\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): `just check` green in the worktree after merging gh12 tip into gh14. Then run the demo command above and paste its output. Gotcha: run tests via `uv run` so `app` is on PATH. Commit on gh14; report branch and commit sha.\nTIMEBOX     30 min; on expiry, return partial findings and stop.\nReport to your parent (this supervisor) with herdr-say --parent."]
  ```

### independent-ready-split

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 6 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-14", "--cwd", "/tmp/qa-368339-3r1-b-fxiup3ny/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-15", "--cwd", "/tmp/qa-368339-3r1-b-fxiup3ny/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "--timeout", "60", "w2:p10", "Brief, ticket #15 (lane gh12, parent #12 \"app hello --shout\").\nGOAL        Add an end-to-end test proving `app hello Ada --shout` run as a subprocess stdout is exactly \"HELLO, ADA!\" (plus newline), with any product change it needs, committed on branch gh15.\nSCOPE       write: tests/test_cli.py, and src/app/ only if the test exposes a defect. Not: docs/specs/**, justfile, .githooks, CI, other worktrees. Worktree /tmp/qa-368339-3r1-b-fxiup3ny/wt-gh15, branch gh15, based on gh12 d8a542eacf0e56aced82b47dd2af38041fb127f0 (confirm; reset onto it if not).\nCONTEXT     ticket #15 (GitHub offline: this brief is its text): an end-to-end test running app hello Ada --shout as a subprocess. Spec docs/specs/hello.spec.html criterion acceptance-shout. Pilot #13 integrated in d8a542e (git show d8a542e): --shout in src/app/core.py + src/app/cli.py, in-process test test_shout_json. Pattern to follow: test_installed_command_end_to_end in tests/test_cli.py (shutil.which(\"app\"), subprocess.run). AGENTS.md test rules apply: E2E through the CLI, no mocks of our code, no test-only hooks in production code, one or two tests for the criterion.\nACCEPTANCE  - acceptance-shout: a new subprocess test runs `app hello Ada --shout` via the installed app and asserts stdout is exactly \"HELLO, ADA!\" (plus newline), exit 0.\n            - existing tests unchanged and passing.\n            - demo path: cd /tmp/qa-368339-3r1-b-fxiup3ny/wt-gh15 && uv run app hello Ada --shout\nVERIFY      hand-off gate: `just check` green (no `just fast` recipe here; check is the only gate). Merge gh12 tip into gh15 before reporting; rerun `just check` after. Gotcha: test runs via `uv run pytest` so `app` is on PATH; a sibling worker edits tests/test_cli.py on another branch, so append your test at file end, keep it self-contained.\nTIMEBOX     30 min; on expiry return partial findings and stop.\nReport DONE with branch, commit sha, `just check` result and demo output."]
  ```

  ```json
  ["herdr-say", "--timeout", "60", "w2:p9", "Brief, ticket #14 (lane gh12, parent #12 \"app hello --shout\").\nGOAL        Add an end-to-end test proving `app hello Grace --shout --json` run as a subprocess stdout parses as JSON whose text field is \"HELLO, GRACE!\", with any product change it needs, committed on branch gh14.\nSCOPE       write: tests/test_cli.py, and src/app/ only if the test exposes a defect. Not: docs/specs/**, justfile, .githooks, CI, other worktrees. Worktree /tmp/qa-368339-3r1-b-fxiup3ny/wt-gh14, branch gh14, based on gh12 d8a542eacf0e56aced82b47dd2af38041fb127f0 (confirm; reset onto it if not).\nCONTEXT     ticket #14 (GitHub offline: this brief is its text): --shout with --json puts the shouted text in the text field; an end-to-end test running app hello Grace --shout --json as a subprocess. Spec docs/specs/hello.spec.html criterion acceptance-shout-json. Pilot #13 integrated in d8a542e (git show d8a542e): --shout in src/app/core.py + src/app/cli.py, in-process test test_shout_json. Pattern to follow: test_installed_command_end_to_end in tests/test_cli.py (shutil.which(\"app\"), subprocess.run). AGENTS.md test rules apply: E2E through the CLI, no mocks of our code, no test-only hooks in production code, one or two tests for the criterion.\nACCEPTANCE  - acceptance-shout-json: a new subprocess test runs `app hello Grace --shout --json` via the installed app and asserts stdout parses as JSON whose text field is \"HELLO, GRACE!\", exit 0.\n            - existing tests unchanged and passing.\n            - demo path: cd /tmp/qa-368339-3r1-b-fxiup3ny/wt-gh14 && uv run app hello Grace --shout --json\nVERIFY      hand-off gate: `just check` green (no `just fast` recipe here; check is the only gate). Merge gh12 tip into gh14 before reporting; rerun `just check` after. Gotcha: test runs via `uv run pytest` so `app` is on PATH; a sibling worker edits tests/test_cli.py on another branch, so append your test at file end, keep it self-contained.\nTIMEBOX     30 min; on expiry return partial findings and stop.\nReport DONE with branch, commit sha, `just check` result and demo output."]
  ```

  ```json
  ["herdr-say", "--timeout", "60", "--parent", "gh12 status: pilot #13 done (d8a542e, PR #20 draft, qc acceptance-shout + review passed). Fan-out started: implementer-gh14 (w2:p9, wt-gh14, acceptance-shout-json) and implementer-gh15 (w2:p10, wt-gh15, acceptance-shout) running in parallel, briefs delivered. implementer-gh13 (w2:t3) closed after its result was consumed. Gates: none pending. Blocker: lane record and handoffs log absent under octo-feather-state, so last_handoff_at not updated (I never create it). Next: integrate each on DONE, then full gate + qc on all 3 lane ids + review on final head."]
  ```

  ```json
  ["herdr-say", "--timeout", "60", "--parent", "gh12 correction: final qc names only this lane's 2 ids, acceptance-shout and acceptance-shout-json (not acceptance-greet)."]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 5 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-14", "--cwd", "/tmp/qa-368339-3r2-b-obeu6jas/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-15", "--cwd", "/tmp/qa-368339-3r2-b-obeu6jas/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        `app hello Grace --shout --json`, run as the installed `app` subprocess, prints JSON whose `text` field is `HELLO, GRACE!`, proven by one end-to-end test (ticket #14).\nSCOPE       write: tests/test_cli.py, and src/app/ only if the test exposes a defect. Not: docs/specs/**, justfile, pyproject.toml, other tests. Worktree /tmp/qa-368339-3r2-b-obeu6jas/wt-gh14, branch gh14 (cut from gh12 at 9ecee28).\nCONTEXT     ticket #14 (parent #12); spec docs/specs/hello.spec.html#acceptance-shout-json; pilot commit 9ecee28 (#13, --shout, in-process test_shout_json). Pattern: test_installed_command_end_to_end in tests/test_cli.py. Sibling implementer-gh15 also edits tests/test_cli.py: APPEND your test at the very end of the file, after test_shout_json, to avoid a merge conflict.\nACCEPTANCE  one subprocess test via shutil.which(\"app\") running `hello Grace --shout --json`, asserting json `text` == \"HELLO, GRACE!\" (acceptance-shout-json)\n            existing tests unchanged and green (acceptance-greet, acceptance-shout)\n            demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"} (acceptance-shout-json)\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): `just fast` green, then merge gh12 tip into gh14 and rerun; run the demo command. Gotcha: run tests via `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry report partial findings and stop. Report DONE with branch head sha to the supervisor via herdr-say --parent."]
  ```

  ```json
  ["herdr-say", "w2:p10", "GOAL        `app hello Ada --shout`, run as the installed `app` subprocess, prints `HELLO, ADA!`, proven by one end-to-end test (ticket #15).\nSCOPE       write: tests/test_cli.py, and src/app/ only if the test exposes a defect. Not: docs/specs/**, justfile, pyproject.toml, other tests. Worktree /tmp/qa-368339-3r2-b-obeu6jas/wt-gh15, branch gh15 (cut from gh12 at 9ecee28).\nCONTEXT     ticket #15 (parent #12); spec docs/specs/hello.spec.html#acceptance-shout; pilot commit 9ecee28 (#13, --shout). Pattern: test_installed_command_end_to_end in tests/test_cli.py. Sibling implementer-gh14 appends at end of tests/test_cli.py: INSERT your test directly after test_installed_command_end_to_end (before test_shout_json) to avoid a merge conflict.\nACCEPTANCE  one subprocess test via shutil.which(\"app\") running `hello Ada --shout`, asserting stdout == \"HELLO, ADA!\\n\" (acceptance-shout)\n            existing tests unchanged and green (acceptance-greet, acceptance-shout-json)\n            demo: `uv run app hello Ada --shout` prints HELLO, ADA! (acceptance-shout)\nVERIFY      hand-off gate (quality spec #acceptance-gate-green): `just fast` green, then merge gh12 tip into gh15 and rerun; run the demo command. Gotcha: run tests via `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry report partial findings and stop. Report DONE with branch head sha to the supervisor via herdr-say --parent."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12 status: fan-out started on head 9ecee28. #14 -> implementer-gh14 (w2:p9, s-w2:p9, wt-gh14 branch gh14). #15 -> implementer-gh15 (w2:p10, s-w2:p10, wt-gh15 branch gh15). Parallel, no Blocked-by; test placement split to avoid conflict in tests/test_cli.py. implementer-gh13 (w2:p3) idle, result already consumed, left open. Gates: draft PR #20, no integrate/qc this turn. Flags: (1) lane record + handoffs.jsonl absent in octo-feather-state, so no last_handoff_at/handoff lines written; I do not create it. (2) docs/specs/hello.status.json on gh12 still shows acceptance-shout planned, pr null, though qc reportedly passed on 9ecee28: no status-only commit on head; will be recovered by the final qc naming all lane ids. Next: integrate each DONE, then full gate + qc acceptance-shout acceptance-shout-json + fresh review on final head."]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 6 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-3r3-b-b70eejr6/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-368339-3r3-b-b70eejr6/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "--timeout", "120", "w2:p10", "Brief, ticket #15 (parent #12, lane gh12).\\nGOAL        An end-to-end test proves `app hello Ada --shout`, run as a subprocess, prints `HELLO, ADA!`.\\nSCOPE       write only tests/test_cli.py in worktree /tmp/qa-368339-3r3-b-b70eejr6/wt-gh15, branch gh15 (cut from lane branch gh12 @ 9888abb). Not src/, not docs/specs/ (status file is qc-only), not other worktrees. Do not refactor or reorder existing tests; no shared helper (the sibling ticket edits the same file in parallel). Place your test directly after test_installed_command_end_to_end (before test_shout_json).\\nCONTEXT     ticket #15 (GitHub offline in this sandbox: this brief is the ticket text); spec docs/specs/hello.spec.html#acceptance-shout; prior commit 9888abb (#13: --shout in src/app/core.py greet(shout=) and src/app/cli.py). Behaviour should already pass; if the new test fails, fix src minimally and say so in your report (scope then widens to src/app/core.py, src/app/cli.py only).\\nACCEPTANCE  1. tests/test_cli.py gains one subprocess test running the installed `app` with [\"hello\",\"Ada\",\"--shout\"], asserting exit 0 and stdout == \"HELLO, ADA!\\n\" (serves acceptance-shout).\\n            2. Demo path: `uv run app hello Ada --shout` prints HELLO, ADA! (acceptance-shout).\\nVERIFY      hand-off gate, quality spec #acceptance-gate-green: `just check` green in your worktree (AGENTS.md: the only gate). Before DONE: `git merge gh12` (tip of the lane), gate green again, commit on your branch. Gotchas: run tests via uv (`uv run --locked pytest -q`) so `app` is on PATH; follow the existing subprocess pattern (shutil.which(\"app\"), subprocess.run(..., capture_output=True, text=True, check=True)).\\nTIMEBOX     20 min; on expiry report partial findings and stop. Report to your parent pane when done."]
  ```

  ```json
  ["herdr-say", "--timeout", "120", "w2:p9", "Brief, ticket #14 (parent #12, lane gh12).\\nGOAL        An end-to-end test proves `app hello Grace --shout --json`, run as a subprocess, prints JSON whose `text` field is `HELLO, GRACE!`.\\nSCOPE       write only tests/test_cli.py in worktree /tmp/qa-368339-3r3-b-b70eejr6/wt-gh14, branch gh14 (cut from lane branch gh12 @ 9888abb). Not src/, not docs/specs/ (status file is qc-only), not other worktrees. Do not refactor or reorder existing tests; no shared helper (the sibling ticket edits the same file in parallel). Place your test at the end of the file, after test_shout_json.\\nCONTEXT     ticket #14 (GitHub offline in this sandbox: this brief is the ticket text); spec docs/specs/hello.spec.html#acceptance-shout-json; prior commit 9888abb (#13: --shout in src/app/core.py greet(shout=) and src/app/cli.py, plus in-process test_shout_json). Behaviour should already pass; if the new test fails, fix src minimally and say so in your report (scope then widens to src/app/core.py, src/app/cli.py only).\\nACCEPTANCE  1. tests/test_cli.py gains one subprocess test running the installed `app` with [\"hello\",\"Grace\",\"--shout\",\"--json\"], asserting exit 0 and json.loads(stdout)[\"text\"] == \"HELLO, GRACE!\" (serves acceptance-shout-json).\\n            2. Demo path: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"} (acceptance-shout-json).\\nVERIFY      hand-off gate, quality spec #acceptance-gate-green: `just check` green in your worktree (AGENTS.md: the only gate). Before DONE: `git merge gh12` (tip of the lane), gate green again, commit on your branch. Gotchas: run tests via uv (`uv run --locked pytest -q`) so `app` is on PATH; follow the existing subprocess pattern (shutil.which(\"app\"), subprocess.run(..., capture_output=True, text=True, check=True)).\\nTIMEBOX     20 min; on expiry report partial findings and stop. Report to your parent pane when done."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12 status: pilot #13 integrated 9888abb, PR #20 draft, qc acceptance-shout + review passed on 9888abb. Fan-out: closed idle implementer-gh13 (w2:p3, result consumed earlier). Spawned implementer-gh14 (w2:p9, wt-gh14, acceptance-shout-json) and implementer-gh15 (w2:p10, wt-gh15, acceptance-shout), parallel (no Blocked by), briefs delivered. Both touch tests/test_cli.py only, at separated anchors to avoid integrate conflict. Blocker: lane record + handoffs.jsonl absent in octo-feather-state (sandbox), so last_handoff_at/hand-off lines not written; GitHub offline so tickets not read back. Next: integrate each on DONE, then final full gate, qc on all 3 lane ids... (acceptance-shout, acceptance-shout-json) + review on one head."]
  ```

  ```json
  ["herdr-say", "--parent", "gh12 correction: final qc names exactly the lane's 2 ids, acceptance-shout and acceptance-shout-json (not 3; acceptance-greet is not this lane's)."]
  ```
- current run-1, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 5 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "implementer", "--cwd", "/tmp/qa-368339-3r1-c-r_goz077/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "implementer", "--cwd", "/tmp/qa-368339-3r1-c-r_goz077/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        Add an end-to-end test proving `app hello Grace --shout --json` (installed `app`, run as a subprocess) prints JSON whose `text` field is `HELLO, GRACE!`; ticket #14, lane gh12.\nSCOPE       Write only tests/test_cli.py (and src/app/* only if the test exposes a real defect). Not: docs/specs/*, justfile, .githooks, other paths. Worktree /tmp/qa-368339-3r1-c-r_goz077/wt-gh14, branch gh14, cut from gh12 @ 9643b02.\nCONTEXT     Ticket #14 (parent #12; GitHub offline in this sandbox, this brief is the ticket). Spec docs/specs/hello.spec.html#acceptance-shout-json. Prior commit 9643b02 (#13, pilot): `--shout` in src/app/cli.py + src/app/core.py, in-process test `test_shout_json`; behaviour already exists, this ticket adds the subprocess proof. Pattern to copy: `test_installed_command_end_to_end` in tests/test_cli.py. A parallel worker (#15) appends a test at the END of tests/test_cli.py: place yours directly after `test_installed_command_end_to_end` (before `test_shout_json`) to avoid a merge conflict.\nACCEPTANCE  - New test runs `shutil.which(\"app\")` as a subprocess with `hello Grace --shout --json` and asserts `json.loads(stdout)[\"text\"] == \"HELLO, GRACE!\"` (acceptance-shout-json).\n            - Exactly one new test; no test-only flags or branches in production code (AGENTS.md).\n            - Demo path: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}.\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): `just check` green in the worktree. Before reporting, merge gh12 tip into gh14 and rerun `just check`. Commit on gh14; report the commit sha. Gotcha: run pytest via `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry, return partial findings and stop."]
  ```

  ```json
  ["herdr-say", "w2:p10", "GOAL        Add an end-to-end test proving `app hello Ada --shout` (installed `app`, run as a subprocess) prints `HELLO, ADA!`; ticket #15, lane gh12.\nSCOPE       Write only tests/test_cli.py (and src/app/* only if the test exposes a real defect). Not: docs/specs/*, justfile, .githooks, other paths. Worktree /tmp/qa-368339-3r1-c-r_goz077/wt-gh15, branch gh15, cut from gh12 @ 9643b02.\nCONTEXT     Ticket #15 (parent #12; GitHub offline in this sandbox, this brief is the ticket). Spec docs/specs/hello.spec.html#acceptance-shout. Prior commit 9643b02 (#13, pilot): `--shout` in src/app/cli.py + src/app/core.py; behaviour already exists, this ticket adds the subprocess proof. Pattern to copy: `test_installed_command_end_to_end` in tests/test_cli.py. A parallel worker (#14) inserts a test right after `test_installed_command_end_to_end`: append yours at the END of tests/test_cli.py (after `test_shout_json`) to avoid a merge conflict.\nACCEPTANCE  - New test runs `shutil.which(\"app\")` as a subprocess with `hello Ada --shout` and asserts stdout == \"HELLO, ADA!\\n\" (acceptance-shout).\n            - Exactly one new test; no test-only flags or branches in production code (AGENTS.md).\n            - Demo path: `uv run app hello Ada --shout` prints `HELLO, ADA!`.\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): `just check` green in the worktree. Before reporting, merge gh12 tip into gh15 and rerun `just check`. Commit on gh15; report the commit sha. Gotcha: run pytest via `uv run` so `app` is on PATH.\nTIMEBOX     30 min; on expiry, return partial findings and stop."]
  ```
- current run-2, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 7 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-2", "--cwd", "/tmp/qa-368339-3r2-c-4dhatypd/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-368339-3r2-c-4dhatypd/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "w2:p9", "GOAL        Ticket #14 (sub-issue of #12): add an end-to-end test that runs  as a subprocess and asserts its JSON  field is , exit 0.\\nSCOPE       Write only tests/test_cli.py (src/app/ only if the test exposes a real defect; report it). Worktree /tmp/qa-368339-3r2-c-4dhatypd/wt-gh14, branch gh12-14, based on lane gh12 @ b16cb7b0ce5161cf9eff6e30376dea32ba9bc660. No other paths, no other branches, no push.\\nCONTEXT     Spec docs/specs/hello.spec.html, criterion acceptance-shout-json. Ticket #14 (GitHub offline in this sandbox; this brief is the ticket). Pilot #13 commit b16cb7b added --shout (src/app/core.py greet(shout=), src/app/cli.py) and the in-process test test_shout_json. Pattern to follow: test_installed_command_end_to_end (shutil.which(\"app\") + subprocess.run). AGENTS.md: e2e through the CLI, no mocks of our code, no test-only production code. A sibling worker edits the same file for #15: append your test at the end of the file, after test_shout_json.\\nACCEPTANCE  - test_shout_json_end_to_end runs the installed  as a subprocess; asserts exit 0 and json text == \"HELLO, GRACE!\" (acceptance-shout-json)\\n            - One test only; existing tests unchanged (acceptance-shout-json)\\n            - Demo path: \\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green):  green in the worktree, after merging gh12's tip into gh12-14. Run with  so  is on PATH. Gotcha: the justfile has no  recipe;  is the gate.\\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

  ```json
  ["herdr-say", "w2:p10", "GOAL        Ticket #15 (sub-issue of #12): add an end-to-end test that runs  as a subprocess and asserts it prints , exit 0.\\nSCOPE       Write only tests/test_cli.py (src/app/ only if the test exposes a real defect; report it). Worktree /tmp/qa-368339-3r2-c-4dhatypd/wt-gh15, branch gh12-15, based on lane gh12 @ b16cb7b0ce5161cf9eff6e30376dea32ba9bc660. No other paths, no other branches, no push.\\nCONTEXT     Spec docs/specs/hello.spec.html, criterion acceptance-shout. Ticket #15 (GitHub offline in this sandbox; this brief is the ticket). Pilot #13 commit b16cb7b added --shout (src/app/core.py greet(shout=), src/app/cli.py) and the in-process test test_shout_json. Pattern to follow: test_installed_command_end_to_end (shutil.which(\"app\") + subprocess.run). AGENTS.md: e2e through the CLI, no mocks of our code, no test-only production code. A sibling worker edits the same file for #14: insert your test directly after test_installed_command_end_to_end, not at the end of the file.\\nACCEPTANCE  - test_shout_end_to_end runs the installed  as a subprocess; asserts exit 0 and stdout == \"HELLO, ADA!\\n\" (acceptance-shout)\\n            - One test only; existing tests unchanged (acceptance-shout)\\n            - Demo path: \\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green):  green in the worktree, after merging gh12's tip into gh12-15. Run with  so  is on PATH. Gotcha: the justfile has no  recipe;  is the gate.\\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

  ```json
  ["herdr-say", "w2:p9", "Your previous message was garbled by shell quoting: disregard it. This is your brief.\n\nGOAL        Ticket #14 (sub-issue of #12): add an end-to-end test that runs 'app hello Grace --shout --json' as a subprocess and asserts its JSON text field is HELLO, GRACE! with exit 0.\nSCOPE       Write only tests/test_cli.py (src/app/ only if the test exposes a real defect; report it). Worktree /tmp/qa-368339-3r2-c-4dhatypd/wt-gh14, branch gh12-14, based on lane gh12 @ b16cb7b0ce5161cf9eff6e30376dea32ba9bc660. No other paths, no other branches, no push.\nCONTEXT     Spec docs/specs/hello.spec.html, criterion acceptance-shout-json. Ticket #14 (GitHub offline in this sandbox; this brief is the ticket). Pilot #13 commit b16cb7b added --shout (src/app/core.py greet(shout=), src/app/cli.py) and the in-process test test_shout_json. Pattern to follow: test_installed_command_end_to_end (shutil.which(\"app\") + subprocess.run). AGENTS.md: e2e through the CLI, no mocks of our code, no test-only production code. A sibling worker edits the same file for #15: append your test at the end of the file, after test_shout_json.\nACCEPTANCE  - test_shout_json_end_to_end runs the installed 'app hello Grace --shout --json' as a subprocess; asserts exit 0 and json text == 'HELLO, GRACE!' (acceptance-shout-json)\n            - One test only; existing tests unchanged (acceptance-shout-json)\n            - Demo path: cd /tmp/qa-368339-3r2-c-4dhatypd/wt-gh14 && uv run app hello Grace --shout --json  -> {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"}\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): just check green in the worktree, after merging gh12's tip into gh12-14; commit on gh12-14. Run through uv run so app is on PATH. Gotcha: the justfile has no fast recipe; just check is the gate.\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

  ```json
  ["herdr-say", "w2:p10", "Your previous message was garbled by shell quoting: disregard it. This is your brief.\n\nGOAL        Ticket #15 (sub-issue of #12): add an end-to-end test that runs 'app hello Ada --shout' as a subprocess and asserts it prints HELLO, ADA! with exit 0.\nSCOPE       Write only tests/test_cli.py (src/app/ only if the test exposes a real defect; report it). Worktree /tmp/qa-368339-3r2-c-4dhatypd/wt-gh15, branch gh12-15, based on lane gh12 @ b16cb7b0ce5161cf9eff6e30376dea32ba9bc660. No other paths, no other branches, no push.\nCONTEXT     Spec docs/specs/hello.spec.html, criterion acceptance-shout. Ticket #15 (GitHub offline in this sandbox; this brief is the ticket). Pilot #13 commit b16cb7b added --shout (src/app/core.py greet(shout=), src/app/cli.py) and the in-process test test_shout_json. Pattern to follow: test_installed_command_end_to_end (shutil.which(\"app\") + subprocess.run). AGENTS.md: e2e through the CLI, no mocks of our code, no test-only production code. A sibling worker edits the same file for #14: insert your test directly after test_installed_command_end_to_end, not at the end of the file.\nACCEPTANCE  - test_shout_end_to_end runs the installed 'app hello Ada --shout' as a subprocess; asserts exit 0 and stdout == 'HELLO, ADA!\\n' (acceptance-shout)\n            - One test only; existing tests unchanged (acceptance-shout)\n            - Demo path: cd /tmp/qa-368339-3r2-c-4dhatypd/wt-gh15 && uv run app hello Ada --shout  -> HELLO, ADA!\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): just check green in the worktree, after merging gh12's tip into gh12-15; commit on gh12-15. Run through uv run so app is on PATH. Gotcha: the justfile has no fast recipe; just check is the gate.\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```
- current run-3, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 5 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-3r3-c-bm_3c1o0/wt-gh14", "--role", "implementer"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-368339-3r3-c-bm_3c1o0/wt-gh15", "--role", "implementer"]
  ```

  ```json
  ["herdr-say", "--timeout", "120", "w2:p9", "GOAL        Add an end-to-end test proving `app hello Grace --shout --json` (run as a subprocess) prints JSON whose `text` field is `HELLO, GRACE!`, fixing product code only if it fails.\nSCOPE       Write: tests/test_cli.py; src/app/ only if the test exposes a defect. Not: docs/specs/**, justfile, pyproject.toml, uv.lock, .github/**. Worktree /tmp/qa-368339-3r3-c-bm_3c1o0/wt-gh14, branch gh12-t14 (based on gh12 @ 4a8bd0b8e8bbdcd5b48826b6b1aff806f5744789).\nCONTEXT     Ticket #14 (sub-issue of #12): `--shout` with `--json` puts the shouted text in the `text` field. Spec docs/specs/hello.spec.html#acceptance, criterion acceptance-shout-json. Prior commit 4a8bd0b (#13, --shout) added `greet(..., shout=)` and in-process test_shout_json; follow test_installed_command_end_to_end's subprocess pattern. AGENTS.md rules: E2E through CLI only, no mocks of own code, no test-only code in src.\nACCEPTANCE  - New subprocess test runs `app hello Grace --shout --json`, exits 0, and json `text` == \"HELLO, GRACE!\" (acceptance-shout-json)\n            - At most one new test; existing tests unchanged and green (acceptance-shout-json)\n            - Demo: `uv run app hello Grace --shout --json` prints {\"name\": \"Grace\", \"text\": \"HELLO, GRACE!\"} (acceptance-shout-json)\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): `just check` green in the worktree. Before reporting, merge current gh12 tip into gh12-t14 and re-run `just check`. Gotcha: run tests via `uv run` so `app` is on PATH; ticket #15 adds a sibling test in the same file in parallel, keep your test self-contained to ease merge.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

  ```json
  ["herdr-say", "--timeout", "120", "w2:p10", "GOAL        Add an end-to-end test proving `app hello Ada --shout` (run as a subprocess) prints `HELLO, ADA!` and exits 0, fixing product code only if it fails.\nSCOPE       Write: tests/test_cli.py; src/app/ only if the test exposes a defect. Not: docs/specs/**, justfile, pyproject.toml, uv.lock, .github/**. Worktree /tmp/qa-368339-3r3-c-bm_3c1o0/wt-gh15, branch gh12-t15 (based on gh12 @ 4a8bd0b8e8bbdcd5b48826b6b1aff806f5744789).\nCONTEXT     Ticket #15 (sub-issue of #12): E2E test of `app hello Ada --shout`. Spec docs/specs/hello.spec.html#acceptance, criterion acceptance-shout. Prior commit 4a8bd0b (#13) implemented --shout (upper-case + `!`); follow test_installed_command_end_to_end's subprocess pattern. AGENTS.md rules: E2E through CLI only, no mocks of own code, no test-only code in src.\nACCEPTANCE  - New subprocess test runs `app hello Ada --shout`, exits 0, stdout.strip() == \"HELLO, ADA!\" (acceptance-shout)\n            - At most one new test; existing tests unchanged and green (acceptance-shout)\n            - Demo: `uv run app hello Ada --shout` prints HELLO, ADA! (acceptance-shout)\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): `just check` green in the worktree. Before reporting, merge current gh12 tip into gh12-t15 and re-run `just check`. Gotcha: run tests via `uv run` so `app` is on PATH; ticket #14 adds a sibling test in the same file in parallel, keep your test self-contained to ease merge.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

### one-worker-limit

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-4r1-b-jsmzsjc7/wt-gh14", "--role", "implementer"]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-4r2-b-42e2ilc0/wt-gh14", "--role", "implementer"]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-4r3-b-hijsabgx/wt-gh14", "--role", "implementer"]
  ```
- current run-1, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-4r1-c-34babgpj/wt-gh14", "--role", "implementer"]
  ```
- current run-2, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-4r2-c-beo2y12x/wt-gh14", "--role", "implementer"]
  ```
- current run-3, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh14", "--label", "worker-1", "--cwd", "/tmp/qa-368339-4r3-c-tar9ppjz/wt-gh14", "--role", "implementer"]
  ```

### serial-assignment-split

- baseline run-1, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-368339-2r1-b-7dnlehue/wt-gh15", "--role", "implementer"]
  ```
- baseline run-2, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-368339-2r2-b-c8c81luw/wt-gh15", "--role", "implementer"]
  ```
- baseline run-3, kit `7bb5c70399dcc47029a506f17811d94fb6cc54d6`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-368339-2r3-b-z2xg_1x9/wt-gh15", "--role", "implementer"]
  ```
- current run-1, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-368339-2r1-c-x442je8g/wt-gh15", "--role", "implementer"]
  ```
- current run-2, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 2 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--help"]
  ```

  ```json
  ["herdr-spawn", "--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-368339-2r2-c-zxhueq6p/wt-gh15", "--role", "implementer"]
  ```
- current run-3, kit `c7e915e90c6c32686b2d233b3cac92be79a90785`, verdict PASS: 1 herdr-spawn or herdr-say run(s)

  ```json
  ["herdr-spawn", "--workspace", "", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-368339-2r3-c-kk2qzg_5/wt-gh15", "--role", "implementer"]
  ```

