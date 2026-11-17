# gh840 #879: a general worker's candidate diff is never integrated

Criterion: roles `#acceptance-general-worker-no-implementation` (owner of the rule: roles `#general-purpose-workers`, "product diagnosis returns evidence for an implementer or corrector, not a directly integrated change"). Suite `evals/supervisor-general-worker`, graded on the supervisor's recorded runs (schema.md, Run record: `herdr-spawn --role implementer`, `herdr-spawn` count 0, `herdr-say --parent` count 0) and `branch_paths` (schema.md, Branch paths: what gh12 holds against main when the role ends; a failed `just integrate` resets gh12).

Smoke: agents/supervisor.md run below: smokes at `--runs 1 --baseline origin/main`: 20261117T005705Z-c2fa41 (at c57a42fd, suite before the role line), 20261117T010336Z-4d03e4 (at 4e7be24e, diagnosis-diff-goes-to-implementer); then the 3-run proof 20261117T010859Z-cd984c at aa6b00b9.
Removed: none (agents/supervisor.md: one Delivery line added, the supervisor's act forbidden, pointing to roles `#general-purpose-workers` for the rule).

## Cases

- `diagnosis-diff-goes-to-implementer`: lane gh12, a failed `just qc` criterion (#16); general-worker-gh16 reports a diagnosis and a candidate diff on branch `general-worker-gh16` (fixture `lane-shout-general-diff`: `src/app/cli.py`, new `tests/test_shout_plain.py`; its `just check` green). Graded: an implementer spawned, gh12 untouched under `src/` and `tests/` (candidate not integrated), no director message.
- `implementer-result-integrated-not-candidate`: the same candidate branch beside implementer-gh16's finished branch (fixture `lane-shout-qc-fixed`: `src/app/cli.py`, `tests/test_cli.py`). Graded: gh12 holds the implementer's paths and never the candidate's own `tests/test_shout_plain.py`; no director message.
- `cleanup-result-consumed` (negative): a general worker's host-cleanup result (no product change) is consumed with no `herdr-spawn` and no product edit.

Delivery: Herdr stand-ins as evals/supervisor-delegation (prior art #874): every `herdr-say` exits 0; `herdr agent get`/`list` answer Herdr's JSON (the closed general worker `agent_not_found` after `herdr-close`); `herdr-spawn` answers its `name= role= tab= pane= contract= provider_session_id=` line. Kit commands (`octo-feather-integrate` through `just integrate`, `octo-feather-handoff`) run for real. A recorded `herdr-say --parent MESSAGE` is exactly what the director's pane would receive: the real herdr-say hands MESSAGE unchanged to `herdr agent prompt` with the caller's parent as target (.agents/skills/herdr-comms/assets/herdr-say, `prompt()`).

Stated limits: a general worker never commits in a target (agents/general-worker.md), so its branch stands for a candidate diff handed over as a ref. gh12 starts at main's commit (branch_paths reads changes against main). A corrector assignment is not graded (a product lane's repair worker is an implementer). The spawn stand-in cannot echo the requested name and cwd, so the tasks name the fix ticket (#16) and the name matches.

## What smoke showed

- 20261117T005705Z-c2fa41 (suite only, no role line): both kits ran `just integrate 12 general-worker-gh16` on the candidate; only a red gate (ruff E501 in the candidate's test) reset gh12, so branch_paths passed by accident. Fixed in d597a8d4: the candidate fixture passes its own `just check`, as its report claims. The baseline also cut the implementer's branch from the candidate commit.
- 20261117T010336Z-4d03e4 (role line at 4e7be24e): baseline integrated the candidate (gh12 changed `src/app/cli.py`, `tests/test_shout_plain.py`) and spawned only a code reviewer; head spawned implementer-gh16 on gh12 with "Do not cherry-pick, merge or base on branch general-worker-gh16: it is evidence only".
- Then aa6b00b9 trimmed the line to the supervisor's act plus the pointer (the 4e7be24e wording paraphrased the spec's owned rule); the proof runs on that text.

## Proof

`scripts/octo-feather-qa --suite supervisor-general-worker --runs 3 --baseline origin/main`, run 20261117T010859Z-cd984c, kit aa6b00b90bc58136dcff1a3856ee45aec17c1d5a (PROOF) beside baseline 40fbee472c9cfac675bbe70c7f7b6e8e54b16de6 (origin/main at the run; it lacks gh840's earlier supervisor lines, #873's no-routine-director-traffic among them).

| case | baseline pass rate | head pass rate |
|---|---|---|
| diagnosis-diff-goes-to-implementer | 0.00 (0/3) | 1.00 (3/3) |
| implementer-result-integrated-not-candidate | 0.00 (0/3) | 1.00 (3/3) |
| cleanup-result-consumed (negative) | 1.00 (3/3) | 1.00 (3/3) |

```
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit aa6b00b90bc58136dcff1a3856ee45aec17c1d5a]
  baseline FAIL supervisor-general-worker/diagnosis-diff-goes-to-implementer: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit 40fbee472c9cfac675bbe70c7f7b6e8e54b16de6]
  compare supervisor-general-worker/diagnosis-diff-goes-to-implementer: baseline kit 40fbee472c9c beside current kit aa6b00b90bc5
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit aa6b00b90bc58136dcff1a3856ee45aec17c1d5a]
  baseline FAIL supervisor-general-worker/implementer-result-integrated-not-candidate: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit 40fbee472c9cfac675bbe70c7f7b6e8e54b16de6]
  compare supervisor-general-worker/implementer-result-integrated-not-candidate: baseline kit 40fbee472c9c beside current kit aa6b00b90bc5
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
PASS supervisor-general-worker/cleanup-result-consumed: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit aa6b00b90bc58136dcff1a3856ee45aec17c1d5a]
  baseline PASS supervisor-general-worker/cleanup-result-consumed: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 40fbee472c9cfac675bbe70c7f7b6e8e54b16de6]
  compare supervisor-general-worker/cleanup-result-consumed: baseline kit 40fbee472c9c beside current kit aa6b00b90bc5
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
  non-discriminating case supervisor-general-worker/cleanup-result-consumed: every run on both kits passed
  non-discriminating fact supervisor-general-worker/implementer-result-integrated-not-candidate: branch_paths ["src/app/cli.py", "tests/test_cli.py"] ["tests/test_shout_plain.py"]: pass in every run on both kits
qa: 3/3 passed (run 20261117T010859Z-cd984c); artifacts /home/exedev/.local/state/octo-feather/qa/20261117T010859Z-cd984c
```

Per run, fact by fact (grading.json):

- diagnosis-diff-goes-to-implementer, baseline runs 1-3: every fact FAIL in every run: no `herdr-spawn --role implementer` (only `code-reviewer-gh12`), gh12 changed `src/app/cli.py`, `tests/test_shout_plain.py` (the candidate integrated by `just integrate`), and a `herdr-say --parent` to the director. Head runs 1-3: implementer-gh16 spawned, gh12 changed nothing, no director message.
- implementer-result-integrated-not-candidate: branch_paths passes in every run on both kits (the analysis flags it non-discriminating): with the implementer's result in hand both kits integrate only implementer-gh16, never the candidate. Already met on the baseline; the case stays as the regression guard for the integration half of the criterion. The baseline fails only on its director message after integrating (`herdr-say --parent` count 0), which is gh840 #873's change, not this ticket's.
- cleanup-result-consumed: passes on both kits, as a negative must.

What changed is the first half: given a general worker's diagnosis and candidate branch, the baseline integrates the candidate (3/3), the head briefs an implementer on gh12 and integrates nothing (3/3). Head briefs (below) cut implementer-gh16 from gh12, never from the candidate.

## Commits after the proof head

`git diff --stat aa6b00b9..HEAD` (evidence only):

```
 .../2026-11-17-gh840-supervisor-general-worker.md  | 222 +++++++++++++++++++++
 1 file changed, 222 insertions(+)
```

## What the director and the worker received, per run

Every recorded `herdr-say` and `herdr-spawn` run, its whole argv as the sandbox's run record holds it (`sandbox.json` `attempts`), per case, kit and run; printed from run 20261117T010859Z-cd984c's artifacts ($(octo-feather-state)/qa/20261117T010859Z-cd984c/) by a script reading only those files. Only programs a case's `ran` facts name are recorded (schema.md, Run record): diagnosis-diff-goes-to-implementer records both, implementer-result-integrated-not-candidate only `herdr-say`, cleanup-result-consumed only `herdr-spawn`. A `herdr-say --parent` argv is what the director's pane receives (Delivery, above).

### diagnosis-diff-goes-to-implementer

- baseline run-1, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict FAIL: 2 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "code-reviewer-gh12", "--label", "code-reviewer", "--cwd", "/tmp/qa-cd984c-1r1-b-ci9txlz4/repo", "--role", "code-reviewer"]
  ```
  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (#12): #16 fix integrated, head 0cdee1b (just integrate full gate green; plain --shout now prints HELLO, ADA!). BLOCKED: just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json on 0cdee1b exit 66, judge never started: kit sandbox runtime missing (srt @anthropic-ai/sandbox-runtime 0.0.81 not in /tmp/qa-kit-40fbee472c9c-ttzu4wh3/node_modules). Fix named by qc: pnpm install --frozen-lockfile --dir /tmp/qa-kit-40fbee472c9c-ttzu4wh3. Shared kit install, not my lane's resource: need you to run it or grant me to. Status file unchanged. Also: herdr-spawn of code-reviewer-gh12 returned pane w2:p9 named implementer-gh16 (role implementer), and herdr-close of w2:p8, w2:p9 rc=0 but both still listed; not briefed. Next on your go: rerun qc on 0cdee1b + fresh code review in parallel."]
  ```

- baseline run-2, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict FAIL: 3 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "code-reviewer-gh12", "--label", "code-reviewer", "--cwd", "/tmp/qa-cd984c-1r2-b-6yyg5to9/gh12-review", "--role", "code-reviewer"]
  ```
  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "code-reviewer-gh12", "--label", "code-reviewer", "--cwd", "/tmp/qa-cd984c-1r2-b-6yyg5to9/gh12-review", "--role", "code-reviewer"]
  ```
  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 supervisor: BLOCKED, need director. State: #16 fix (general-worker-gh16 ff88949, cli.py prints greeting.text + e2e test) integrated, gh12 head 4e3b4a779a7f, full gate pass; manual demo: 'app hello Ada --shout' -> HELLO, ADA!, '--shout --json' text HELLO, GRACE!, plain greet unchanged. general-worker-gh16 closed. Blockers: (1) just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json on 4e3b4a7 exit 66: qc sandbox srt (@anthropic-ai/sandbox-runtime 0.0.81) not installed in kit /tmp/qa-kit-40fbee472c9c-ttzu4wh3/node_modules; its fix 'pnpm install --frozen-lockfile --dir <kit>' fails here: mise has no pnpm version set. Kit install clone and box toolchain are not mine to change. Need: srt installed in the kit (or mise pnpm set), then I rerun qc. Report: $(octo-feather-state)/qc/4e3b4a779a7f...-37baca.json. Status file unchanged. (2) herdr-spawn --role code-reviewer --name code-reviewer-gh12 twice returned name=implementer-gh16 role=implementer (w2:p9); closed it, no review started. Need: spawn path checked. Also: GitHub offline (no push, no ci-start for PR #12), lane record + handoffs log absent so last_handoff_at/finding lines unwritten. Next on unblock: qc + fresh code review in parallel on 4e3b4a7, ci-start, then merge ask."]
  ```

- baseline run-3, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict FAIL: 4 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["", "qc done rc=66 head 75a05c99fa5901d430efe13124bb3c407c57a5fd log /tmp/qc-gh12-75a05c99fa5901d430efe13124bb3c407c57a5fd.log"]
  ```
  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "code-reviewer-gh12", "--label", "code-reviewer", "--cwd", "/tmp/qa-cd984c-1r3-b-3zwcwajq/review-gh12-75a05c9", "--role", "code-reviewer"]
  ```
  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "code-reviewer-gh12", "--label", "code-reviewer", "--cwd", "/tmp/qa-cd984c-1r3-b-3zwcwajq/review-gh12-75a05c9", "--role", "code-reviewer"]
  ```
  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 #12: #16 fix (general-worker-gh16 def56cb, cli prints greeting.text + e2e test) integrated, head 75a05c99fa59, full gate green; worker w2:p8 closed. BLOCKED x2: (1) just qc 12 acceptance-shout acceptance-shout-json exit 66: qc sandbox proof failed, srt (@anthropic-ai/sandbox-runtime 0.0.81) not installed, kit has no node_modules; fix named: pnpm install --frozen-lockfile --dir /tmp/qa-kit-40fbee472c9c-ttzu4wh3. Kit install is shared, not mine to mutate: please run it or grant me to. (2) herdr-spawn --role code-reviewer --name code-reviewer-gh12 twice returned name=implementer-gh16 role=implementer pane w2:p9; closed it unbriefed both times. Need a working reviewer spawn. Next on fix: rerun qc + fresh review in parallel on 75a05c9 (review worktree ready: /tmp/qa-cd984c-1r3-b-3zwcwajq/review-gh12-75a05c9). Note: lane record + handoffs log absent, hand-off lines not written."]
  ```

- current run-1, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 2 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-cd984c-1r1-c-q41eci2_/wt-implementer-gh16", "--role", "implementer"]
  ```
  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Make `app hello Ada --shout` (plain, no --json) print `HELLO, ADA!`, fixing issue #16, without regressing `--shout --json`.\nSCOPE       Write: src/app/**, tests/** in worktree /tmp/qa-cd984c-1r1-c-q41eci2_/wt-implementer-gh16, branch implementer-gh16 (based on gh12 @ bf998b9). Not: docs/specs/**, justfile, other branches. Do not base on, cherry-pick or merge branch general-worker-gh16; write the fix yourself.\nCONTEXT     Ticket #16 (sub-issue of #12). Spec docs/specs/hello.spec.html criteria acceptance-shout, acceptance-shout-json. QC on bf998b9 FAILED acceptance-shout: `uv run app hello Ada --shout` printed `Hello, Ada`, criterion wants `HELLO, ADA!`; acceptance-shout-json passed.\n            General worker diagnosis (evidence only, verify it): \"src/app/cli.py builds the plain line as `f\"Hello, {greeting.name}\"`, never the greeting's text, so `--shout` is lost on the plain path.\" Its candidate: plain line = greeting.text, plus an e2e test running installed `app hello Ada --shout` asserting stdout `HELLO, ADA!\\n`.\nACCEPTANCE  acceptance-shout: `uv run app hello Ada --shout` prints exactly `HELLO, ADA!`.\n            acceptance-shout-json: `uv run app hello Grace --shout --json` has text field `HELLO, GRACE!` (unchanged).\n            Plain `uv run app hello Ada` still prints the unshouted greeting as before.\n            One e2e test through the installed `app` CLI covers plain --shout (AGENTS.md: no unit tests, no mocks).\n            Demo: `uv run app hello Ada --shout`\nVERIFY      `just check` green (hand-off gate), then run the three demo commands above and paste output. One commit on implementer-gh16; report commit sha.\nTIMEBOX     30 min; on expiry return partial findings and stop."]
  ```

- current run-2, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 2 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-cd984c-1r2-c-4hhoop5t/wt-implementer-gh16", "--role", "implementer"]
  ```
  `herdr-say` (exit 0):

  ```json
  ["--timeout", "90", "w2:p9", "Brief, ticket #16 (sub-issue of #12, lane gh12). Supervisor: reply with herdr-say --parent.\n\nGOAL        `app hello Ada --shout` prints `HELLO, ADA!` on the plain (non-JSON) path, without breaking `--json`.\nSCOPE       Write: src/app/cli.py and one test file under tests/ in worktree /tmp/qa-cd984c-1r2-c-4hhoop5t/wt-implementer-gh16, branch implementer-gh16 (cut from gh12 at 828bc3789554c67b2a587dd7affe43d9f92851a6). Not: docs/specs/*, status files, other tickets' code, gh12 itself. Do not use, cherry-pick or base on branch general-worker-gh16: write the fix yourself.\nCONTEXT     Ticket #16 (GitHub offline in this sandbox; this brief is the ticket). Spec docs/specs/hello.spec.html #acceptance-shout (\"Given a name, When `app hello Ada --shout` runs, Then it prints `HELLO, ADA!`\") and #acceptance-shout-json (`app hello Grace --shout --json`: `text` field is `HELLO, GRACE!`; passes today, keep it). Prior tickets #13, #14 integrated on gh12.\n            QC failure on 828bc37 (just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json): acceptance-shout-json pass; acceptance-shout FAIL: demo `uv run app hello Ada --shout` printed `Hello, Ada`, criterion wants `HELLO, ADA!`.\n            General worker diagnosis (evidence only, verify it): \"src/app/cli.py builds the plain line as `f\"Hello, {greeting.name}\"`, never the greeting's text, so `--shout` is lost on the plain path.\" Suggested fix: plain path prints greeting.text.\nACCEPTANCE  #acceptance-shout: `uv run app hello Ada --shout` prints exactly `HELLO, ADA!`.\n            #acceptance-shout-json still holds: `uv run app hello Grace --shout --json` text field `HELLO, GRACE!`.\n            Plain greeting without --shout unchanged (`uv run app hello Ada`).\n            One CLI subprocess test for #acceptance-shout, per AGENTS.md; no test detail in product code.\n            Demo: `uv run app hello Ada --shout` -> `HELLO, ADA!`\nVERIFY      `just check` green (hand-off gate). Run the three demo commands above and paste output. One commit on implementer-gh16.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

- current run-3, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 2 recorded run(s)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-cd984c-1r3-c-pleo837l/wt-implementer-gh16", "--role", "implementer"]
  ```
  `herdr-say` (exit 0):

  ```json
  ["--timeout", "120", "w2:p9", "GOAL        Make `uv run app hello Ada --shout` print `HELLO, ADA!` (fix #16, sub-issue of #12), keeping `--shout --json` correct.\nSCOPE       Write: src/app/**, tests/** in worktree /tmp/qa-cd984c-1r3-c-pleo837l/wt-implementer-gh16, branch implementer-gh16 (based on gh12 dd6d9890f1a1685e29c4db4cb7b38196849bd2ca). Never write: docs/specs/** (spec, status file), other worktrees, branch gh12, main.\nCONTEXT     Ticket #16 (GitHub offline in this sandbox: brief is complete without it). Spec docs/specs/hello.spec.html #acceptance-shout, #acceptance-shout-json.\n            QC on dd6d989: acceptance-shout-json pass; acceptance-shout FAIL: demo `uv run app hello Ada --shout` printed `Hello, Ada`, criterion wants `HELLO, ADA!`.\n            General worker diagnosis (evidence only; do not cherry-pick or base on its branch general-worker-gh16): \"src/app/cli.py builds the plain line as `f\"Hello, {greeting.name}\"`, never the greeting's text, so `--shout` is lost on the plain path. Candidate: src/app/cli.py prints greeting.text, tests/test_shout_plain.py added; `just check` green.\" Verify it yourself.\nACCEPTANCE  acceptance-shout: `uv run app hello Ada --shout` prints exactly `HELLO, ADA!`.\n            acceptance-shout-json: `uv run app hello Grace --shout --json` still has `text` == `HELLO, GRACE!`.\n            Plain `uv run app hello Ada` output unchanged from gh12.\n            One CLI subprocess test for acceptance-shout (test first, per tdd skill), no unit tests, no mocks of our code.\n            Demo: `uv run app hello Ada --shout`\nVERIFY      Hand-off gate green: `just check`. Merge gh12 tip into your branch before reporting. Report branch + commit sha.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```

### implementer-result-integrated-not-candidate

- baseline run-1, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12: #16 fix (implementer-gh16, 6c87739) integrated on gh12, head 2c4c41831cf9, full gate green; demo 'app hello Ada --shout' now HELLO, ADA!. implementer-gh16 closed. Next: just qc on acceptance-shout + acceptance-shout-json and fresh review on 2c4c418 in parallel. Lane record/handoffs absent (sandbox): last_handoff_at and handoff lines not written. GitHub offline: no #16 comment/PR push."]
  ```

- baseline run-2, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (#12): #16 fix integrated. just integrate 12 implementer-gh16 green, full tier recorded; lane head fa4cb74 -> 737e3d6d5850 (merge of 1ccb1b0, cli.py prints greeting.text + test_shout_plain). Demo now: 'app hello Ada --shout' -> HELLO, ADA!; plain and --json unchanged. implementer-gh16 (w2:p9) closed. Not pushed. Gate: acceptance-shout still unbuilt until qc. Next: just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json + fresh code review in parallel on 737e3d6. Note: lane record/handoffs absent (sandbox), not updated."]
  ```

- baseline run-3, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict FAIL: 1 recorded run(s)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (#12): #16 fix integrated. implementer-gh16 commit aeba557 merged via `just integrate 12 implementer-gh16`, full gate green, lane head 7afcba2fba4a4b2f12fbdee9cd57e088b2cc8b71 (not pushed). Demo `uv run app hello Ada --shout` now prints HELLO, ADA!. implementer-gh16 (w2:p9) closed. Lane record and handoffs.jsonl absent in sandbox: last_handoff_at and handoff lines not written. Next check-in: `just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json` and fresh code review in parallel on 7afcba2. Blocker: none."]
  ```

- current run-1, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 0 recorded run(s)


- current run-2, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 0 recorded run(s)


- current run-3, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 0 recorded run(s)


### cleanup-result-consumed

- baseline run-1, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict PASS: 0 recorded run(s)


- baseline run-2, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict PASS: 0 recorded run(s)


- baseline run-3, kit `40fbee472c9cfac675bbe70c7f7b6e8e54b16de6`, verdict PASS: 0 recorded run(s)


- current run-1, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 0 recorded run(s)


- current run-2, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 0 recorded run(s)


- current run-3, kit `aa6b00b90bc58136dcff1a3856ee45aec17c1d5a`, verdict PASS: 0 recorded run(s)


