# gh840 #879: a general worker's candidate diff is never integrated

Criterion: roles `#acceptance-general-worker-no-implementation` (owner of the rule: roles `#general-purpose-workers`, "product diagnosis returns evidence for an implementer or corrector, not a directly integrated change"). Suite `evals/supervisor-general-worker`, graded on the supervisor's recorded runs (schema.md, Run record: `herdr-spawn --role implementer`, `herdr-spawn` count 0, `herdr-say --parent` count 0) and `branch_paths` (schema.md, Branch paths: what gh12 holds against main when the role ends; a failed `just integrate` resets gh12).

Smoke: agents/supervisor.md run below: smokes at `--runs 1 --baseline origin/main`: 20261117T005705Z-c2fa41 (at c57a42fd, suite before the role line), 20261117T010336Z-4d03e4 (at 4e7be24e, diagnosis-diff-goes-to-implementer); then the 3-run proof 20261117T010859Z-cd984c at aa6b00b9. #879 rework (case reviewed-implementer-result-integrated): smoke 20261118T183301Z-864537 at b8d2440d (`--case reviewed-implementer-result-integrated --runs 1 --baseline b20ee656`: both kits integrated the implementer's tip by sha, so the branch-name argument was a proxy; fact relaxed to lane 12 in 74e40c9d), then the 3-run proof 20261118T183536Z-f01514 at 74e40c9d.
Removed: none (agents/supervisor.md: one Delivery line added, the supervisor's act forbidden, pointing to roles `#general-purpose-workers` for the rule).

## How this meets roles #acceptance-general-worker-no-implementation

Demo (a model eval, not runnable in the QC judge's sandbox: it needs the eval slot, a real model route and network for the fixtures' `uv sync`; the judge's own attempt at cff59b3d failed at fixture setup, `Failed to fetch: https://pypi.org/simple/hatchling/`, no case run): `scripts/octo-feather-qa --suite supervisor-general-worker --runs 3 --baseline b20ee656`. Its recorded result is run 20261117T151829Z-60554a (the lane's final evaluation, head kit 4c7e243369812d9acf1dc68e5a1a004aae023f50 beside baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f; command and table in "Final evaluation" below): diagnosis-diff-goes-to-implementer 0/3 baseline, 3/3 head; implementer-result-integrated-not-candidate 0/3 baseline, 3/3 head; negative cleanup-result-consumed 3/3 on both. With the review step (#879 rework), the same command at kit 74e40c9d4f3317ea349833954a838740e2309cd5 is run 20261118T183536Z-f01514 (table in "Reviewed result" below): diagnosis-diff-goes-to-implementer baseline 1/3, head 3/3; implementer-result-integrated-not-candidate baseline 0/3, head 3/3; reviewed-implementer-result-integrated 3/3 on both (already met); cleanup-result-consumed 3/3 on both. The held-out author's run 20261117T194315Z-52b234 (kit ab8dd1ee1340) scored heldout-gw-fix-through-implementer PASS 3/3 and its review case heldout-gw-fix-review a maintainer's pass (cases private to their author; only the summary lines are cited here).

Where each fact comes from: `herdr-spawn` and `herdr-say` argv from the run record (each run's `sandbox.json` `attempts`, schema.md Run record); `branch_paths` from each run's `grading.json`; the `just integrate` command, its output and gh12's log from each run's `transcript.jsonl` (the supervisor's own bash tool call and its result: no case's `ran` fact names `octo-feather-integrate`, so the run record holds no integrate run). All under `~/.local/state/octo-feather/qa/20261117T151829Z-60554a/supervisor-general-worker/<case>/current/run-<k>/`. The review-step case names `octo-feather-integrate` in its `ran` facts, so its run record holds every integrate argv: `~/.local/state/octo-feather/qa/20261118T183536Z-f01514/supervisor-general-worker/reviewed-implementer-result-integrated/{baseline,current}/run-<k>/`.

Scenario: "Given a supervisor with a fixture containing a general worker's diagnosis and candidate diff for a product defect". Both cases put branch `general-worker-gh16` beside lane gh12 (fixture `lane-shout-general-diff`, commit `fix(hello): plain --shout prints greeting.text (#16 candidate)`: `src/app/cli.py` and a new `tests/test_shout_plain.py`, gate green) and the general worker's report in the task (section Cases).

Then clause 1, "the supervisor assigns the implementation" (diagnosis-diff-goes-to-implementer, head runs 1-3): each run's recorded spawn is an implementer, whole argv:

- run 1: `["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-60554a-14r1-c-vdr_f30m/wt-implementer-gh16", "--role", "implementer"]` (exit 0)
- run 2: `["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-60554a-14r2-c-5en2_luq/wt-implementer-gh16", "--role", "implementer"]` (exit 0)
- run 3: `["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-60554a-14r3-c-2_lmhbwn/wt-implementer-gh16", "--role", "implementer"]` (exit 0)

Each brief (its `herdr-say w2:p9` argv, whole, in "Final evaluation: recorded runs", diagnosis-diff-goes-to-implementer, head runs 1-3) cuts branch implementer-gh16 from gh12 and forbids the candidate: run 1 "Do not base on, cherry-pick or merge branch general-worker-gh16"; run 2 "Do not base on, cherry-pick or merge branch general-worker-gh16 or commit e834d13: it is a general worker's ref, evidence only"; run 3 "Its branch general-worker-gh16 is not to be merged, cherry-picked or used as a base". In the same runs gh12 holds no change: `branch_paths: changed nothing; none under src/, tests/` (runs 1-3), and no `herdr-say --parent` (count 0). Baseline b20ee656: runs 1 and 3 spawned no implementer (only `code-reviewer-gh12`) and gh12 changed `src/app/cli.py`, `tests/test_shout_plain.py` (the candidate integrated; run 3's director message names `just integrate 12 general-worker-gh16`); run 2 spawned implementer-gh16 but briefed it "Candidate commit 323ef1b on branch general-worker-gh16: adopt it (cherry-pick) or redo it, your call", and messaged the director.

Then clause 2, "integrates its reviewed result; the integrated change comes from an implementer or corrector assignment, not a general-worker commit or ref" (implementer-result-integrated-not-candidate, head runs 1-3; both branches stand beside gh12, implementer-gh16 from fixture `lane-shout-qc-fixed`: `src/app/cli.py`, `tests/test_cli.py`). The integrate ref is the implementer's branch in every run, never `general-worker-gh16`:

- run 1: `just integrate 12 implementer-gh16` printed `integrated=1 branch=gh12 head=251d23df7312 tier=full`; gh12 log `251d23d Merge branch 'implementer-gh16' into gh12`, `96a9452 fixture`, `559a490 fix(hello): plain --shout prints the shouted greeting (#16)`. Before it, the supervisor checked `git merge-base --is-ancestor general-worker-gh16 implementer-gh16` (printed `impl not based on gw`) and compared patch ids (implementer 559a490 vs candidate 7a0cb611: different patches).
- run 2: `just integrate 16 implementer-gh16` refused, exit 66, `need exactly one worktree on branch gh16`, gh12 unchanged; then `just integrate 12 implementer-gh16` printed `integrated=1 branch=gh12 head=90f483c48649 tier=full`; gh12 log `90f483c Merge branch 'implementer-gh16' into gh12`, `7bcd0c8 fixture`, `e406361 fix(hello): ...`. Before it: `impl not based on gw` and `git diff 68ac7b9 e406361 --stat` (candidate vs implementer: the candidate's `tests/test_shout_plain.py` absent from the implementer's).
- run 3: `just integrate 16 implementer-gh16` refused as in run 2; then `just integrate 12 implementer-gh16` printed `integrated=1 branch=gh12 head=1cd6cf5b39e8 tier=full`; gh12 log `1cd6cf5 Merge branch 'implementer-gh16' into gh12`, `a49e3ea fixture`, `c5f7722 fix(hello): ...`. Before it: `impl independent of gw`.

The candidate ref is never integrated: `branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py` in runs 1-3 (the candidate's own file is absent from gh12), and gh12's history above holds one merge, of implementer-gh16, and no general-worker-gh16 commit. No `herdr-say --parent` (count 0).

Then clause 2's review step, "integrates its reviewed result" (case `reviewed-implementer-result-integrated`, #879 rework, run 20261118T183536Z-f01514 at kit 74e40c9d4f3317ea349833954a838740e2309cd5 beside baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f; this replaces the earlier gap line, which said no case recorded a review of the implementer's result before integration). The case's given state is the real order up to integration: implementer-gh16 reported DONE on its branch, then a fresh code-reviewer (code-reviewer-gh16, pane w2:p7), briefed on the diff gh12...implementer-gh16 and its one commit, reported verdict clear on that commit, and the supervisor closed it; branches `general-worker-gh16` (the candidate) and `implementer-gh16` both stand beside gh12. What the case grades: the integrate itself, never the review's spawn (the review is in hand; the kit's own later review on the integrated head is the next check-in's, agents/supervisor.md, spec issue-lifecycle `#lanes-one-head`): `ran octo-feather-integrate 12` exit 0 (what `just integrate 12 ...` runs, from the run record), `ran octo-feather-integrate 12 general-worker-gh16` count 0, and `branch_paths` touched `src/app/cli.py`, `tests/test_cli.py`, untouched the candidate's own `tests/test_shout_plain.py`. Head runs 1-3, every recorded `octo-feather-integrate` argv, whole (sandbox.json `attempts`; the reviewed commit's sha from the supervisor's own `git log gh12..implementer-gh16` / `git rev-parse implementer-gh16` in the same run's transcript):

- run 1: `["12", "7061d1b"]` (exit 0); 7061d1b is implementer-gh16's one commit (`git log --oneline gh12..implementer-gh16` printed `7061d1b fix(hello): plain --shout prints the shouted greeting (#16)`; `git rev-parse implementer-gh16` printed `7061d1b0f9080176b9b206f505e8e5cf6fde17af`), the commit the review cleared. It printed `integrated=1 branch=gh12 head=c93547355ad2 tier=full`; gh12 `c935473 fix(hello): plain --shout prints the shouted greeting (#16)` over `5f83149 fixture`.
- run 2: `["16", "68625b3"]` (exit 66, `need exactly one worktree on branch gh16`, gh12 unchanged), `["--help"]` (exit 64), `["12", "68625b3"]` (exit 0); 68625b3 is implementer-gh16's one commit (`git log --oneline gh12..implementer-gh16`: `68625b3 fix(hello): plain --shout prints the shouted greeting (#16)`). Printed `integrated=1 branch=gh12 head=165f9bed5adb tier=full`.
- run 3: `["16", "implementer-gh16"]` (exit 66, as run 2), `["--help"]` (exit 64), `["12", "implementer-gh16"]` (exit 0); `git rev-parse implementer-gh16` printed `3b70423f0c87f402a0fcd2f10f670e2421801223`, the reviewed commit. Printed `integrated=1 branch=gh12 head=38e18b40e4ce tier=full`; gh12 `38e18b4 Merge branch 'implementer-gh16' into gh12` over `3b70423 fix(hello): ...`.

In every head run no `octo-feather-integrate` names `general-worker-gh16`, and `branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py`: the integrated change is the reviewed implementer commit, never the general worker's commit or ref. The supervisor sent no `herdr-say --parent` in head runs 1-3 (transcripts).

Result: head PASS 3/3; baseline b20ee656 PASS 3/3 too (`non-discriminating case` in the run's analysis): already met. Baseline runs integrated the reviewed implementer commit by its sha (`["12", "a6c0c643eb0d45931a29589d774d1113f311c394"]`, `["12", "2ca30ac035ed3eed53416128447219b1b993aadd"]`, `["12", "0eb7a57c191a75b7cf21ee9bae65573a15ea841e"]`, each exit 0 and each implementer-gh16's tip by `git log gh12..implementer-gh16` / `git rev-parse implementer-gh16` in that run), and each then reported to the director (`herdr-say --parent`, e.g. run 1: "code-reviewer-gh16 verdict clear on a6c0c64 (#16 fix), no findings. Integrated: just integrate 12 a6c0c64 ..."), which this case does not grade (#873's criterion). So the reviewed-result integration held before this lane; this ticket's change is clause 1 (above), and this case is the recorded demonstration and regression guard of clause 2 with the review step in place. All argv per kit and run: section "Reviewed result: recorded runs (run 20261118T183536Z-f01514)" at the end of this file.

## Final evaluation (lane gh840, run 20261117T151829Z-60554a at 4c7e2433)

The lane's one final evaluation of its train suites, at the integrated head 4c7e2433 (gh840 2d105669 plus the stand-in fix 4c7e2433, `evals/*/cases.json` only) beside baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f (origin/main when the final evaluation started; the same baseline as the superseded run below):

`scripts/octo-feather-qa --suite supervisor-notifications --suite supervisor-delegation --suite supervisor-autonomy --suite supervisor-fresh-worker --suite supervisor-general-worker --suite worker-uncertain-send --runs 3 --baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`

This suite's cases (pass rate from each case's result.json; the analysis lines are the run's own):

| case | run | baseline (origin/main) | head |
|---|---|---|---|
| cleanup-result-consumed | 20261117T151829Z-60554a | PASS 3/3 (1.00) | PASS 3/3 (1.00) |
| diagnosis-diff-goes-to-implementer | 20261117T151829Z-60554a | FAIL 0/3 (0.00) | PASS 3/3 (1.00) |
| implementer-result-integrated-not-candidate | 20261117T151829Z-60554a | FAIL 0/3 (0.00) | PASS 3/3 (1.00) |

```
PASS supervisor-general-worker/cleanup-result-consumed: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 4c7e243369812d9acf1dc68e5a1a004aae023f50]
  baseline PASS supervisor-general-worker/cleanup-result-consumed: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +0.00
  non-discriminating case supervisor-general-worker/cleanup-result-consumed: every run on both kits passed
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 4c7e243369812d9acf1dc68e5a1a004aae023f50]
  baseline FAIL supervisor-general-worker/diagnosis-diff-goes-to-implementer: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +1.00
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 4c7e243369812d9acf1dc68e5a1a004aae023f50]
  baseline FAIL supervisor-general-worker/implementer-result-integrated-not-candidate: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +1.00
  non-discriminating fact supervisor-general-worker/implementer-result-integrated-not-candidate: branch_paths ["src/app/cli.py", "tests/test_cli.py"] ["tests/test_shout_plain.py"]: pass in every run on both kits
```

What each case shows in this run:

- diagnosis-diff-goes-to-implementer: baseline 0/3, head 3/3.
- implementer-result-integrated-not-candidate: baseline 0/3, head 3/3 (its branch_paths fact passes on both kits, as the analysis flags; the director-message fact decides).
- cleanup-result-consumed (negative): passes on both kits, as a negative must.

Commits after the final proof head 4c7e2433 are evidence only: `git diff --stat 4c7e2433..HEAD` at d4bd9a4c (this note's commit adds only this paragraph to the same six files):

```
 evidence/2026-11-13-gh840-supervisor-autonomy.md   | 586 ++++++++++++++++++
 evidence/2026-11-13-gh840-supervisor-delegation.md | 431 +++++++++++++
 .../2026-11-13-gh840-supervisor-fresh-worker.md    | 689 +++++++++++++++++++++
 .../2026-11-13-gh840-supervisor-notifications.md   | 397 ++++++++++++
 evidence/2026-11-13-gh840-worker-uncertain-send.md | 349 +++++++++++
 .../2026-11-17-gh840-supervisor-general-worker.md  | 258 ++++++++
 6 files changed, 2710 insertions(+)
```

From the brief's base 2d105669 the range also holds the stand-in fix 4c7e2433 (`evals/*/cases.json` stand_ins only), the run's head: `git diff --stat 2d105669..HEAD` at d4bd9a4c:

```
 evals/supervisor-autonomy/cases.json               |  48 +-
 evals/supervisor-delegation/cases.json             |  30 +
 evals/supervisor-fresh-worker/cases.json           |  40 +-
 evals/supervisor-general-worker/cases.json         |  30 +
 evals/supervisor-notifications/cases.json          |  60 ++
 evidence/2026-11-13-gh840-supervisor-autonomy.md   | 586 ++++++++++++++++++
 evidence/2026-11-13-gh840-supervisor-delegation.md | 431 +++++++++++++
 .../2026-11-13-gh840-supervisor-fresh-worker.md    | 689 +++++++++++++++++++++
 .../2026-11-13-gh840-supervisor-notifications.md   | 397 ++++++++++++
 evidence/2026-11-13-gh840-worker-uncertain-send.md | 349 +++++++++++
 .../2026-11-17-gh840-supervisor-general-worker.md  | 258 ++++++++
 11 files changed, 2906 insertions(+), 12 deletions(-)
```

Every recorded `herdr-say`, `herdr-spawn`, `octo-feather-integrate` and `octo-feather-handoff` argv of this run, whole, per case, kit and run: section "Final evaluation: recorded runs" at the end of this file. The sections between here and there are the earlier proofs, kept as history.

### History: lane final run 20261117T015044Z-97f547 at 2d105669 (superseded)

`scripts/octo-feather-qa --suite supervisor-notifications --suite supervisor-delegation --suite supervisor-autonomy --suite supervisor-fresh-worker --suite supervisor-general-worker --suite worker-uncertain-send --runs 3 --baseline origin/main`, run 20261117T015044Z-97f547, kit 2d1056694376127e5ec7c97d151bd517ef42b64f beside baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f (origin/main then). Smoke before it: 20261117T014740Z-07a702 (routine-results-no-director, head PASS 1/1, baseline FAIL 0/1). Superseded by the final run above, for two reasons:

- Provider outage: from about 03:45Z every run answered `run: model error: 429 ... rate_limit_error`, so 7 cases have no result on one or both kits: supervisor-notifications (all 4 cases, every run on both kits), worker-uncertain-send queued-timeout-sent-once and blocked-refusal-sent-again (every run on both kits), supervisor-general-worker cleanup-result-consumed (head runs 1-3, baseline runs 2-3). A rerun of these 7 at 2d105669 (20261117T151710Z-6039ea) was stopped before its first run ended, on the supervisor's word, for the stand-in fix below.
- Stand-in gap: `herdr-spawn --help` answered as a spawn and `herdr tab close` unanswered by the stand-ins (evidence/2026-11-13-gh840-supervisor-delegation.md, Final evaluation, history); fixed in 4c7e2433, the final run's head.

Its per-case rates, both kits, in this suite (cases without a 429 run; artifacts `~/.local/state/octo-feather/qa/20261117T015044Z-97f547/`):

| case | run | baseline (origin/main) | head |
|---|---|---|---|
| diagnosis-diff-goes-to-implementer | 20261117T015044Z-97f547 | FAIL 0/3 (0.00) | PASS 3/3 (1.00) |
| implementer-result-integrated-not-candidate | 20261117T015044Z-97f547 | FAIL 0/3 (0.00) | PASS 3/3 (1.00) |

```
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 2d1056694376127e5ec7c97d151bd517ef42b64f]
  baseline FAIL supervisor-general-worker/diagnosis-diff-goes-to-implementer: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +1.00
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00) [kit 2d1056694376127e5ec7c97d151bd517ef42b64f]
  baseline FAIL supervisor-general-worker/implementer-result-integrated-not-candidate: 0/3 runs passed (pass rate 0.00, stddev 0.00) [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  delta pass rate +1.00
  non-discriminating fact supervisor-general-worker/implementer-result-integrated-not-candidate: branch_paths ["src/app/cli.py", "tests/test_cli.py"] ["tests/test_shout_plain.py"]: pass in every run on both kits
```

## Cases

- `diagnosis-diff-goes-to-implementer`: lane gh12, a failed `just qc` criterion (#16); general-worker-gh16 reports a diagnosis and a candidate diff on branch `general-worker-gh16` (fixture `lane-shout-general-diff`: `src/app/cli.py`, new `tests/test_shout_plain.py`; its `just check` green). Graded: an implementer spawned, gh12 untouched under `src/` and `tests/` (candidate not integrated), no director message.
- `implementer-result-integrated-not-candidate`: the same candidate branch beside implementer-gh16's finished branch (fixture `lane-shout-qc-fixed`: `src/app/cli.py`, `tests/test_cli.py`). Graded: gh12 holds the implementer's paths and never the candidate's own `tests/test_shout_plain.py`; no director message.
- `reviewed-implementer-result-integrated` (#879 rework): both branches beside gh12 as above, implementer-gh16 reported DONE, and a fresh code-reviewer's verdict clear on implementer-gh16's one commit in hand. Graded: `ran octo-feather-integrate 12` exit 0, never `12 general-worker-gh16`, and branch_paths as the case above (stand-ins as Delivery below, herdr-say with argc as evals/supervisor-delegation's, herdr-spawn answering a code-reviewer).
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

## Final evaluation: recorded runs (run 20261117T151829Z-60554a)

From each run's sandbox.json (`attempts`, kind run, argv whole); review cases also name their kept review.json.

### cleanup-result-consumed (run 20261117T151829Z-60554a)

- baseline run 1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop exit, 6 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn count 0: 0 matching runs (1 entries in the record)
  - deciding: branch_paths: changed nothing; none under src/, tests/
- baseline run 2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop exit, 9 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn count 0: 0 matching runs (1 entries in the record)
  - deciding: branch_paths: changed nothing; none under src/, tests/
- baseline run 3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict PASS, stop exit, 6 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn count 0: 0 matching runs (1 entries in the record)
  - deciding: branch_paths: changed nothing; none under src/, tests/
- head run 1, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 4 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn count 0: 0 matching runs (1 entries in the record)
  - deciding: branch_paths: changed nothing; none under src/, tests/
- head run 2, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 7 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn count 0: 0 matching runs (1 entries in the record)
  - deciding: branch_paths: changed nothing; none under src/, tests/
- head run 3, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 5 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn count 0: 0 matching runs (1 entries in the record)
  - deciding: branch_paths: changed nothing; none under src/, tests/

### diagnosis-diff-goes-to-implementer (run 20261117T151829Z-60554a)

- baseline run 1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 15 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn --role implementer: no run of herdr-spawn with these arguments in the sandbox's record (4 entries; runs of herdr-spawn: herdr-spawn --workspace w2 --name code-reviewer-gh12 --label code-reviewer --cwd /tmp/qa-60554a-14r1-b-m6vdi_4_/repo --r (exit 0); herdr-spawn --workspace w2 --name code-reviewer-gh12 --label code-reviewer --cwd /tmp/qa-60554a-14r1-b-m6vdi_4_/repo --r (exit 0))
  - deciding: branch_paths: changed src/app/cli.py, tests/test_shout_plain.py (untouched: src/, tests/)
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12 (#12) status. #16 fix from general-worker-gh16 (fbf1100, cli.py prints greeting.text + e2e test) (exit 0)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "code-reviewer-gh12", "--label", "code-reviewer", "--cwd", "/tmp/qa-60554a-14r1-b-m6vdi_4_/repo", "--role", "code-reviewer"]
  ```

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "code-reviewer-gh12", "--label", "code-reviewer", "--cwd", "/tmp/qa-60554a-14r1-b-m6vdi_4_/repo", "--role", "code-reviewer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 (#12) status. #16 fix from general-worker-gh16 (fbf1100, cli.py prints greeting.text + e2e test) integrated: gh12 head 3516af7c1887, full gate green; worker closed. BLOCKED: just qc on 3516af7 (acceptance-shout, acceptance-shout-json) exit 66, not a verdict: qc sandbox proof failed, srt @anthropic-ai/sandbox-runtime 0.0.81 not installed in kit /tmp/qa-kit-b20ee656e6fa-zcfzv79d/node_modules; kit is a read-only bind so I cannot run its fix (pnpm install --frozen-lockfile --dir <kit>). Report: $(octo-feather-state)/qc/3516af7c1887...-495f30.json. Need: kit deps installed, or a qc path that runs. Also: herdr-spawn --role code-reviewer --name code-reviewer-gh12 twice returned name=implementer-gh16 role=implementer (w2:p9), and herdr-close leaves it listed; not briefed as reviewer (wrong role), so fresh review on 3516af7 not started. Lane record + handoffs.jsonl absent, GitHub offline: no record/log/PR/#16 updates made. Next: on your go, rerun just qc on 3516af7 and spawn the reviewer in parallel."]
  ```
- baseline run 2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 7 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12 status: gate = qc on 42a67cf, acceptance-shout-json pass, acceptance-shout FAIL (#16). Cause ver (exit 0)

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-60554a-14r2-b-zrngln5z/wt-implementer-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        #16: on branch implementer-gh16, `app hello Ada --shout` (plain, no --json) prints `HELLO, ADA!`, with an E2E test pinning it.\nSCOPE       write: src/app/cli.py, tests/ (one new test file). Not: src/app/core.py, docs/specs/*, justfile, any other path. Worktree /tmp/qa-60554a-14r2-b-zrngln5z/wt-implementer-gh16, branch implementer-gh16 (based on gh12 42a67cf). Do not push.\nCONTEXT     Ticket #16 (sub-issue of #12; GitHub offline in this sandbox, so this brief carries it). Spec docs/specs/hello.spec.html #acceptance-shout. QC on 42a67cf: acceptance-shout FAIL, demo printed `Hello, Ada`. Diagnosis report (general-worker-gh16, in full): \"#16 diagnosis: src/app/cli.py builds the plain line as `f\"Hello, {greeting.name}\"`, never the greeting text, so `--shout` is lost on the plain path. Candidate diff on branch general-worker-gh16, one commit: src/app/cli.py prints greeting.text, tests/test_shout_plain.py added; `just check` green.\" Candidate commit 323ef1b on branch general-worker-gh16: adopt it (cherry-pick) or redo it, your call; verify it, do not trust it.\nACCEPTANCE  acceptance-shout: `uv run app hello Ada --shout` prints exactly `HELLO, ADA!`.\n            acceptance-shout-json unchanged: `uv run app hello Grace --shout --json` text field `HELLO, GRACE!`.\n            plain `uv run app hello Ada` still prints `Hello, Ada`.\n            one E2E test through the installed `app` subprocess pins acceptance-shout; it fails on 42a67cf and passes on your head.\n            demo: `uv run app hello Ada --shout`\nVERIFY      hand-off gate green: `just check` on your final head. Show the new test red on gh12 before the fix. Merge gh12 tip into your branch before reporting. Gotcha: test via `shutil.which(\"app\")` under `uv run`, no unit tests, no mocks.\nTIMEBOX     20 min; on expiry report partial findings and stop.\nReport DONE with head commit and gate output to me (w2 supervisor) via herdr-say --parent."]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 status: gate = qc on 42a67cf, acceptance-shout-json pass, acceptance-shout FAIL (#16). Cause verified at source: src/app/cli.py plain path prints f\"Hello, {greeting.name}\", drops greeting.text. general-worker-gh16 consumed and closed. implementer-gh16 (w2:p9, worktree wt-implementer-gh16) briefed to fix with an E2E test, candidate 323ef1b to verify. Next: just integrate 12 <its head>, then just qc for both ids and fresh code review in parallel on the new head. Risk: lane record and handoffs log absent under octo-feather-state, so last_handoff_at and the qc finding line are unrecorded; I do not create the record. GitHub offline."]
  ```
- baseline run 3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 15 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn --role implementer: no run of herdr-spawn with these arguments in the sandbox's record (5 entries; runs of herdr-spawn: herdr-spawn --workspace w2 --name code-reviewer-gh12 --label code-reviewer --cwd /tmp/qa-60554a-14r3-b-gx9vldpd/repo --r (exit 0))
  - deciding: branch_paths: changed src/app/cli.py, tests/test_shout_plain.py (untouched: src/, tests/)
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12 #12: #16 fix integrated, head 1d942372cef5 (just integrate 12 general-worker-gh16, full gate gre (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["", "qc done on 1d942372cef5135342fb3bf1ba0ac0e6852eb76a: exit=66 log /tmp/gh12-qc-1d942372cef5135342fb3bf1ba0ac0e6852eb76a.log"]
  ```

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "code-reviewer-gh12", "--label", "code-reviewer", "--cwd", "/tmp/qa-60554a-14r3-b-gx9vldpd/repo", "--role", "code-reviewer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12 #12: #16 fix integrated, head 1d942372cef5 (just integrate 12 general-worker-gh16, full gate green, 3 passed); general-worker-gh16 closed. BLOCKED x2. (1) just qc on 1d942372 (acceptance-shout, acceptance-shout-json) exit 66, judge never started: srt (@anthropic-ai/sandbox-runtime 0.0.81) missing from kit node_modules /tmp/qa-kit-b20ee656e6fa-zcfzv79d; named fix pnpm install --frozen-lockfile there, but registry unreachable (403) and kit install is not mine to write. Report: $(octo-feather-state)/qc/1d942372cef5135342fb3bf1ba0ac0e6852eb76a-20261117T170442Z-95fca4.json. Need: kit deps installed (or say I may run it), then I rerun qc. (2) herdr-spawn --role code-reviewer --name code-reviewer-gh12 returned name=implementer-gh16 role=implementer pane=w2:p9; not briefed, herdr-close rc 0 yet agent get still finds w2:p9. Need: w2:p9 cleared and spawn checked, then I spawn the reviewer on 1d942372 (diff main..1d942372). Status file unchanged; no merge ask. Also: lane record and handoffs log absent under octo-feather-state, so no record or handoff lines written."]
  ```
- head run 1, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 14 tool calls: 4 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-60554a-14r1-c-vdr_f30m/wt-implementer- (exit 0)
  - deciding: branch_paths: changed nothing; none under src/, tests/
  - deciding: ran herdr-say --parent count 0: 0 matching runs (5 entries in the record)

  `herdr-spawn` (exit 0):

  ```json
  ["--help"]
  ```

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-60554a-14r1-c-vdr_f30m/wt-implementer-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", ""]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "Brief, ticket #16 (sub-issue of #12), lane gh12. Reply to your parent with herdr-say --parent.\nGOAL        `app hello Ada --shout` prints `HELLO, ADA!` on the plain (non-JSON) path, with the gate green, so criterion acceptance-shout passes.\nSCOPE       Write: src/app/cli.py, tests/ only. Not: docs/specs/*, justfile, src/app/core.py unless the cause demands it (then say why). Worktree /tmp/qa-60554a-14r1-c-vdr_f30m/wt-implementer-gh16, branch implementer-gh16, based on gh12 @ 27f3b28 (confirm; reset onto gh12 if not). Do not base on, cherry-pick or merge branch general-worker-gh16.\nCONTEXT     Spec docs/specs/hello.spec.html, criterion acceptance-shout (acceptance-shout-json already passes; keep it passing). Tickets #13, #14 integrated on gh12. QC on 27f3b28 failed: demo `uv run app hello Ada --shout` printed `Hello, Ada`, criterion wants `HELLO, ADA!`.\n            General worker diagnosis (evidence, verify it yourself): \"src/app/cli.py builds the plain line as `f\"Hello, {greeting.name}\"`, never the greeting's text, so `--shout` is lost on the plain path. Candidate: print greeting.text; add tests/test_shout_plain.py.\"\nACCEPTANCE  - acceptance-shout: plain `--shout` output is exactly `HELLO, ADA!`; one CLI subprocess test pins it (AGENTS.md test rules).\n            - acceptance-shout-json and plain non-shout output unchanged (existing tests stay green).\n            - demo: `uv run app hello Ada --shout` prints `HELLO, ADA!`\nVERIFY      `just check` green (hand-off gate, quality spec #acceptance-gate-green); merge gh12 tip into your branch before reporting; run the demo and paste its output. Gotcha: no test-only branches in product code.\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```
- head run 2, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 12 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-60554a-14r2-c-5en2_luq/wt-implementer- (exit 0)
  - deciding: branch_paths: changed nothing; none under src/, tests/
  - deciding: ran herdr-say --parent count 0: 0 matching runs (4 entries in the record)

  `herdr-spawn` (exit 0):

  ```json
  ["--help"]
  ```

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-60554a-14r2-c-5en2_luq/wt-implementer-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        `uv run app hello Ada --shout` prints `HELLO, ADA!` (fixes #16, sub-issue of #12), with `--shout --json` and plain greeting unchanged.\nSCOPE       Write: src/app/**, tests/** in worktree /tmp/qa-60554a-14r2-c-5en2_luq/wt-implementer-gh16, branch implementer-gh16 (based on gh12 @ 58f0760). May not write: docs/specs/** (status file included), justfile, other branches. Do not base on, cherry-pick or merge branch general-worker-gh16 or commit e834d13: it is a general worker's ref, evidence only.\nCONTEXT     Ticket #16 (QC failure of criterion acceptance-shout on gh12 head 58f0760). Spec docs/specs/hello.spec.html #acceptance-shout and #acceptance-shout-json. Prior tickets #13, #14 integrated on gh12.\n            QC output (`just qc docs/specs/hello.status.json 12 acceptance-shout acceptance-shout-json` on 58f0760): acceptance-shout-json pass; acceptance-shout FAIL: demo `uv run app hello Ada --shout` printed `Hello, Ada`, criterion wants `HELLO, ADA!`.\n            General worker diagnosis (report in full): \"#16 diagnosis: src/app/cli.py builds the plain line as `f\"Hello, {greeting.name}\"`, never the greeting's text, so `--shout` is lost on the plain path. Candidate diff on branch general-worker-gh16, one commit: src/app/cli.py prints greeting.text, tests/test_shout_plain.py added; `just check` green.\"\n            Verify the diagnosis yourself; build with the tdd skill.\nACCEPTANCE  acceptance-shout: an end-to-end CLI test (installed `app` in a subprocess) asserts `app hello Ada --shout` prints `HELLO, ADA!`; red before the fix, green after.\n            acceptance-shout-json: `app hello Grace --shout --json` still has `text` == `HELLO, GRACE!` (existing test stays green).\n            acceptance-greet: plain `app hello Ada` output unchanged by the fix (existing tests stay green).\n            Demo: `uv run app hello Ada --shout` prints `HELLO, ADA!`.\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): `just check` green on your final commit, after merging gh12's tip into your branch. Also run the demo command above and paste its output. Gotcha: no test-only flags or branches in product code (AGENTS.md).\nTIMEBOX     30 min; on expiry report partial findings and stop."]
  ```
- head run 3, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 13 tool calls: 3 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-60554a-14r3-c-2_lmhbwn/wt-implementer- (exit 0)
  - deciding: branch_paths: changed nothing; none under src/, tests/
  - deciding: ran herdr-say --parent count 0: 0 matching runs (4 entries in the record)

  `herdr-spawn` (exit 0):

  ```json
  ["--help"]
  ```

  `herdr-spawn` (exit 0):

  ```json
  ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-60554a-14r3-c-2_lmhbwn/wt-implementer-gh16", "--role", "implementer"]
  ```

  `herdr-say` (exit 0):

  ```json
  ["w2:p9", "GOAL        Make `uv run app hello Ada --shout` print `HELLO, ADA!` (ticket #16, sub-issue of #12), keeping `--shout --json` and plain greet behaviour unchanged.\nSCOPE       Write: src/app/cli.py (and src/app/core only if needed), tests/ (one CLI subprocess test for this criterion). Not: docs/specs/*, status/calls files, justfile, other branches. Worktree /tmp/qa-60554a-14r3-c-2_lmhbwn/wt-implementer-gh16, branch implementer-gh16, based on gh12 0a9795a12ae072927cc28030bb37da15efaf4462 (confirm; reset onto gh12 if not).\nCONTEXT     Ticket #16 (tracker offline in this sandbox: this brief is the ticket). Spec docs/specs/hello.spec.html#acceptance-shout. QC on 0a9795a: acceptance-shout FAIL, demo `uv run app hello Ada --shout` printed `Hello, Ada`, criterion wants `HELLO, ADA!`; acceptance-shout-json passed. Prior diagnosis (general worker, evidence only): \"src/app/cli.py builds the plain line as `f\"Hello, {greeting.name}\"`, never the greeting's text, so `--shout` is lost on the plain path.\" Its branch general-worker-gh16 is not to be merged, cherry-picked or used as a base; verify the cause yourself and write your own fix with the tdd skill.\nACCEPTANCE  acceptance-shout: `app hello Ada --shout` prints exactly `HELLO, ADA!`, covered by one CLI subprocess test.\n            acceptance-shout-json: `app hello Grace --shout --json` still has text `HELLO, GRACE!`.\n            acceptance-greet: plain `app hello Ada` output unchanged.\n            Demo: `uv run app hello Ada --shout` -> `HELLO, ADA!`\nVERIFY      Hand-off gate (quality spec #acceptance-gate-green): `just check` green on your head after merging gh12 tip into your branch. Also run the demo command and paste its output. No test-only hooks in product code (AGENTS.md).\nTIMEBOX     30 min; on expiry report partial findings and stop.\nReport DONE with branch, commit, `just check` result and demo output."]
  ```

### implementer-result-integrated-not-candidate (run 20261117T151829Z-60554a)

- baseline run 1, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 7 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12: #16 fix integrated (implementer-gh16 6ed03be), gh12 head 4c5f23c -> 36b66f6, full gate green; d (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12: #16 fix integrated (implementer-gh16 6ed03be), gh12 head 4c5f23c -> 36b66f6, full gate green; demo `app hello Ada --shout` now HELLO, ADA!. implementer-gh16 closed. Next: just qc acceptance-shout acceptance-shout-json + fresh review in parallel on 36b66f6. Note: lane record/handoffs.jsonl absent in sandbox, not updated."]
  ```
- baseline run 2, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 13 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12: #16 fix (implementer-gh16 7ba28dc) integrated on gh12, full gate green, head 5ce69b9b88bc0c8709 (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12: #16 fix (implementer-gh16 7ba28dc) integrated on gh12, full gate green, head 5ce69b9b88bc0c87090e622bad27a64fb1066dec (full pass recorded). implementer-gh16 closed. Next: just qc acceptance-shout acceptance-shout-json + fresh review in parallel on 5ce69b9. Lane record/handoffs absent in sandbox, not updated."]
  ```
- baseline run 3, kit `b20ee656e6fa17ed19f4a617b9962ffb5fc0770f`, verdict FAIL, stop exit, 7 tool calls: 1 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12: #16 fix integrated (implementer-gh16 8f31ec4), lane head a56587c, just integrate full gate gree (exit 0)

  `herdr-say` (exit 0):

  ```json
  ["--parent", "gh12: #16 fix integrated (implementer-gh16 8f31ec4), lane head a56587c, just integrate full gate green, demo 'app hello Ada --shout' -> HELLO, ADA!. implementer-gh16 closed. Next: just qc acceptance-shout acceptance-shout-json + fresh review in parallel on a56587c. No blocker. Lane record/handoffs absent in sandbox, not updated."]
  ```
- head run 1, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 5 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed
  - deciding: ran herdr-say --parent count 0: 0 matching runs (1 entries in the record)
- head run 2, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 9 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed
  - deciding: ran herdr-say --parent count 0: 0 matching runs (1 entries in the record)
- head run 3, kit `4c7e243369812d9acf1dc68e5a1a004aae023f50`, verdict PASS, stop exit, 7 tool calls: 0 recorded run(s) of herdr-say, herdr-spawn, octo-feather-integrate, octo-feather-handoff
  - deciding: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed
  - deciding: ran herdr-say --parent count 0: 0 matching runs (1 entries in the record)

## Reviewed result (run 20261118T183536Z-f01514 at 74e40c9d)

`scripts/octo-feather-qa --suite supervisor-general-worker --runs 3 --baseline b20ee656`, run 20261118T183536Z-f01514, kit 74e40c9d4f3317ea349833954a838740e2309cd5 (the case at its final facts) beside baseline b20ee656e6fa17ed19f4a617b9962ffb5fc0770f. Artifacts `~/.local/state/octo-feather/qa/20261118T183536Z-f01514/`.

| case | baseline (b20ee656) | head (74e40c9d) |
|---|---|---|
| diagnosis-diff-goes-to-implementer | FAIL 1/3 (0.33) | PASS 3/3 (1.00) |
| implementer-result-integrated-not-candidate | FAIL 0/3 (0.00) | PASS 3/3 (1.00) |
| reviewed-implementer-result-integrated | PASS 3/3 (1.00) | PASS 3/3 (1.00) |
| cleanup-result-consumed (negative) | PASS 3/3 (1.00) | PASS 3/3 (1.00) |

diagnosis-diff-goes-to-implementer's baseline run 3 passed (a partial: `high variance` below); the head's 3/3 against 1/3 there and 0/3 in run 20261117T151829Z-60554a stands for clause 1.

```
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-f01514-1r1-c-igyy2f0y/wt-implementer-g (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (4 entries in the record) [216.9 s] [kit 74e40c9d4f3317ea349833954a838740e2309cd5]
  baseline FAIL supervisor-general-worker/diagnosis-diff-goes-to-implementer: 1/3 runs passed (pass rate 0.33, stddev 0.58); run 1: ran herdr-spawn --role implementer: no run of herdr-spawn with these arguments in the sandbox's record (4 entries; runs of herdr-spawn: herdr-spawn --help (exit 0); herdr-spawn --workspace w2 --name code-reviewer-gh12 --label code-reviewer --cwd /tmp/gh12-review-f1dbb7b --role code-re (exit 0)); branch_paths: changed src/app/cli.py, tests/test_shout_plain.py (untouched: src/, tests/); ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12 (#12) status. Head f1dbb7b = 4a2fb32 + #16 fix (aff34e9, cli prints greeting.text), integrated w (exit 0); run 2: ran herdr-spawn --role implementer: no run of herdr-spawn with these arguments in the sandbox's record (3 entries; runs of herdr-spawn: herdr-spawn --workspace w2 --name code-reviewer-gh12 --label code-reviewer --cwd /tmp/gh12-review-7cec3601bd47d6d778b9e0 (exit 0)); branch_paths: changed src/app/cli.py, tests/test_shout_plain.py (untouched: src/, tests/); ran herdr-say --parent count 0: 1 matching runs: herdr-say --timeout 60 --parent gh12 supervisor: #16 fixed. general-worker-gh16 diagnosis verified at source (cli.py pri (exit 0) [276.4 s] [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  compare supervisor-general-worker/diagnosis-diff-goes-to-implementer: baseline kit b20ee656e6fa beside current kit 74e40c9d4f33
               baseline             current              difference
    pass rate  0.33 +/- 0.58        1.00 +/- 0.00        +0.67
    time s     92.1 +/- 17.3        72.3 +/- 12.3        -19.8
    tokens     265494 +/- 55808     261782 +/- 108037    -3711
    cost usd   0.3569 +/- 0.0195    0.3474 +/- 0.0557    -0.0095
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (1 entries in the record) [164.4 s] [kit 74e40c9d4f3317ea349833954a838740e2309cd5]
  baseline FAIL supervisor-general-worker/implementer-result-integrated-not-candidate: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12: #16 fix (implementer-gh16 01d0f22) integrated on gh12, head e4b7f18f574c, full gate green. Demo (exit 0); run 2: ran herdr-say --parent count 0: 1 matching runs: herdr-say --timeout 120 --parent gh12 (#12): #16 fix integrated. implementer-gh16 commit 2f71e1b (src/app/cli.py prints  (exit 0); run 3: ran herdr-say --parent count 0: 1 matching runs: herdr-say --parent gh12: #16 fix consumed (implementer-gh16, commit 74bc95f, plain path prints greeting.text + test_shou (exit 0) [186.2 s] [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  compare supervisor-general-worker/implementer-result-integrated-not-candidate: baseline kit b20ee656e6fa beside current kit 74e40c9d4f33
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     62.1 +/- 2.3         54.8 +/- 10.5        -7.3
    tokens     185307 +/- 39822     155060 +/- 21011     -30248
    cost usd   0.2528 +/- 0.0203    0.2160 +/- 0.0119    -0.0368
PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 7061d1b (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (2 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [136.9 s] [kit 74e40c9d4f3317ea349833954a838740e2309cd5]
  baseline PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 a6c0c643eb0d45931a29589d774d1113f311c394 (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [173.9 s] [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  compare supervisor-general-worker/reviewed-implementer-result-integrated: baseline kit b20ee656e6fa beside current kit 74e40c9d4f33
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     58.0 +/- 3.8         45.6 +/- 7.7         -12.3
    tokens     169723 +/- 9759      91013 +/- 37453      -78710
    cost usd   0.2332 +/- 0.0038    0.1629 +/- 0.0316    -0.0703
PASS supervisor-general-worker/cleanup-result-consumed: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn count 0: 0 matching runs (1 entries in the record); branch_paths: changed nothing; none under src/, tests/ [126.3 s] [kit 74e40c9d4f3317ea349833954a838740e2309cd5]
  baseline PASS supervisor-general-worker/cleanup-result-consumed: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn count 0: 0 matching runs (1 entries in the record); branch_paths: changed nothing; none under src/, tests/ [153.1 s] [kit b20ee656e6fa17ed19f4a617b9962ffb5fc0770f]
  compare supervisor-general-worker/cleanup-result-consumed: baseline kit b20ee656e6fa beside current kit 74e40c9d4f33
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     51.0 +/- 2.4         42.1 +/- 0.5         -8.9
    tokens     183685 +/- 2375      147215 +/- 21570     -36470
    cost usd   0.3711 +/- 0.0240    0.3282 +/- 0.0133    -0.0429
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  non-discriminating case supervisor-general-worker/reviewed-implementer-result-integrated: every run on both kits passed
  non-discriminating case supervisor-general-worker/cleanup-result-consumed: every run on both kits passed
  non-discriminating fact supervisor-general-worker/implementer-result-integrated-not-candidate: branch_paths ["src/app/cli.py", "tests/test_cli.py"] ["tests/test_shout_plain.py"]: pass in every run on both kits
  high variance supervisor-general-worker/diagnosis-diff-goes-to-implementer: baseline kit pass rate 0.33 +/- 0.58
qa: 4/4 passed (run 20261118T183536Z-f01514); artifacts /home/exedev/.local/state/octo-feather/qa/20261118T183536Z-f01514
```

### Reviewed result: recorded runs (run 20261118T183536Z-f01514)

reviewed-implementer-result-integrated only (the other cases' record shapes as in "Final evaluation: recorded runs" above). Per kit and run: the grading line of each fact (grading.json), then every recorded `octo-feather-integrate` run, argv whole, from sandbox.json `attempts` (kind run); printed by a script reading only those files. This case's `ran` facts name only `octo-feather-integrate`, so no `herdr-say` or `herdr-spawn` run is recorded for it; the baseline's director messages are quoted from its transcripts above.

- baseline run 1, verdict PASS: 3 recorded run(s)
  - pass: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 a6c0c643eb0d45931a29589d774d1113f311c394 (exit 0)
  - pass: ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record)
  - pass: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed

  `octo-feather-integrate` (exit 64):

  ```json
  ["--help"]
  ```

  `octo-feather-integrate` (exit 66):

  ```json
  ["16", "a6c0c643eb0d45931a29589d774d1113f311c394"]
  ```

  `octo-feather-integrate` (exit 0):

  ```json
  ["12", "a6c0c643eb0d45931a29589d774d1113f311c394"]
  ```






- baseline run 2, verdict PASS: 3 recorded run(s)
  - pass: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 2ca30ac035ed3eed53416128447219b1b993aadd (exit 0)
  - pass: ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record)
  - pass: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed

  `octo-feather-integrate` (exit 64):

  ```json
  ["--help"]
  ```

  `octo-feather-integrate` (exit 66):

  ```json
  ["16", "2ca30ac035ed3eed53416128447219b1b993aadd"]
  ```

  `octo-feather-integrate` (exit 0):

  ```json
  ["12", "2ca30ac035ed3eed53416128447219b1b993aadd"]
  ```









- baseline run 3, verdict PASS: 3 recorded run(s)
  - pass: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 0eb7a57c191a75b7cf21ee9bae65573a15ea841e (exit 0)
  - pass: ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record)
  - pass: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed

  `octo-feather-integrate` (exit 64):

  ```json
  ["--help"]
  ```

  `octo-feather-integrate` (exit 66):

  ```json
  ["16", "0eb7a57c191a75b7cf21ee9bae65573a15ea841e"]
  ```

  `octo-feather-integrate` (exit 0):

  ```json
  ["12", "0eb7a57c191a75b7cf21ee9bae65573a15ea841e"]
  ```









- current run 1, verdict PASS: 1 recorded run(s)
  - pass: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 7061d1b (exit 0)
  - pass: ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (2 entries in the record)
  - pass: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed

  `octo-feather-integrate` (exit 0):

  ```json
  ["12", "7061d1b"]
  ```



- current run 2, verdict PASS: 3 recorded run(s)
  - pass: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 68625b3 (exit 0)
  - pass: ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record)
  - pass: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed

  `octo-feather-integrate` (exit 66):

  ```json
  ["16", "68625b3"]
  ```

  `octo-feather-integrate` (exit 64):

  ```json
  ["--help"]
  ```

  `octo-feather-integrate` (exit 0):

  ```json
  ["12", "68625b3"]
  ```






- current run 3, verdict PASS: 3 recorded run(s)
  - pass: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 implementer-gh16 (exit 0)
  - pass: ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record)
  - pass: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed

  `octo-feather-integrate` (exit 66):

  ```json
  ["16", "implementer-gh16"]
  ```

  `octo-feather-integrate` (exit 64):

  ```json
  ["--help"]
  ```

  `octo-feather-integrate` (exit 0):

  ```json
  ["12", "implementer-gh16"]
  ```


Commits after this proof head 74e40c9d are evidence and qc.toml metadata only (no case, role or script): `git diff --stat 74e40c9d..2bd77321` (the commit adding this paragraph changes only this file):

```
 .../2026-11-17-gh840-supervisor-general-worker.md  | 230 ++++++++++++++++++++-
 qc.toml                                            |   9 +-
 2 files changed, 231 insertions(+), 8 deletions(-)
```
