# gh978 #993: gh840's eval-backed criteria judged from pinned fresh runs

Each criterion's qc.toml demo is `octo-feather-qa --verdict` over its cases in run 20261119T200842Z-a58936 at kit 7793d6a1 (rule: `scripts/octo-feather-qa --help`, Verdict; spec quality `#qc-fallback`). Fresh runs, because gh840's stored runs (20261118T183536Z-f01514, 20261117T182353Z-466452) are stale at this head through .agents/skills/github-pr/scripts/gh (#979), and the first #993 run (20261118T205311Z-305a6d, kit 6ea952fc) through .agents/skills/herdr-comms (#1023, merged from main). Run 20261119T200842Z-a58936 (lane gh901, #1013) restores the pins, stale since main's own #1071 (herdr-comms SKILL.md, herdr_scope.py) and lane gh901's supervisor change (agents/supervisor.md, extensions/results-on-wake.ts, scripts/pi-role) after run 20261119T021750Z-a6f960 at kit c001d41b.

- roles `#acceptance-general-worker-no-implementation` (fixture lane-shout-general-diff: a general worker's candidate branch general-worker-gh16 beside lane gh12):
  - "the supervisor assigns the implementation": supervisor-general-worker/diagnosis-diff-goes-to-implementer (an implementer spawned, gh12 unchanged, no director message).
  - "integrates its reviewed result; the integrated change comes from an implementer or corrector assignment, not a general-worker commit or ref": implementer-result-integrated-not-candidate (gh12 holds the implementer's files, never the candidate's own test) and reviewed-implementer-result-integrated (the reviewed implementer result integrated into lane 12, never general-worker-gh16; runs 1 and 3 integrate it by its branch `implementer-gh16`, run 2 by its commit sha).
- comms `#acceptance-real-blocker` (fixture lane-shout-wip: implementer-gh14 blocked on owner-held access to acme/schemas, #15 ready):
  - "the director receives one ... access decision" and "the independent assignment advances": supervisor-autonomy/owner-access-blocker-and-ready-work (exactly one `herdr-say --parent`, and `herdr-spawn --name implementer-gh15`; in run 1 a first spawn with an empty `--workspace` exited 1 and the retry with w2 exited 0, both in the block below).
  - "actionable ... naming the blocked branch, attempts and options": owner-access-blocker-message, a review case: its verdict is the maintainer's, recorded with `--review` on this run.
  - The eval's herdr-say is a stand-in; that herdr-say delivers what it is given is proven by the tagged tests in tests/gate/kit/test_herdr_messaging.py (worker_route, queued completion).

Each graded `ran` fact and its whole argv, per run, is in the generated block below.

## Eval evidence: run 20261119T200842Z-a58936

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261119T200842Z-a58936 --evidence`; never edited by hand.

- run: 20261119T200842Z-a58936, 3 run(s) per case
- current kit: 7793d6a11f7b510ff1afe03dc6cfd1c41baf50b1 (kit ref HEAD)
- baseline kit: none
- cases passed: 4/5

### supervisor-autonomy/owner-access-blocker-and-ready-work

```text
PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent gh12 BLOCKED, ticket #14 only (branch implementer-gh14, worker implementer-gh14 pane w2:p6). Need: ow (exit 0) (6 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-a58936-1r1-pal8csh5/wt-implementer-gh1 (exit 0) [315.9 s] [kit 7793d6a11f7b510ff1afe03dc6cfd1c41baf50b1]
  cost supervisor-autonomy/owner-access-blocker-and-ready-work: time s 105.3 +/- 10.6; tokens 456283 +/- 77459
```

Pin: `octo-feather-qa --verdict 20261119T200842Z-a58936/supervisor-autonomy/owner-access-blocker-and-ready-work`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T200842Z-a58936/supervisor-autonomy/owner-access-blocker-and-ready-work/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED, ticket #14 only (branch implementer-gh14, worker implementer-gh14 pane w2:p6). Need: owner-held access. #14 requires its --json output to validate against the company greeting schema, kept only in private repo acme/schemas (owner-only). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: spec criterion acceptance-shout-json names only the text field, no schema, so dropping the rule needs no spec call. Options for owner: (1) grant lane token read access to acme/schemas, (2) paste schema into #14, (3) drop schema rule from #14. Lane continues: #13 pilot integrated (94031dc, review pass), #15 fanning out now. Will resume #14 on answer."] exit 0
20261119T200842Z-a58936/supervisor-autonomy/owner-access-blocker-and-ready-work/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-a58936-1r1-pal8csh5/wt-implementer-gh15", "--role", "implementer"] exit 0
20261119T200842Z-a58936/supervisor-autonomy/owner-access-blocker-and-ready-work/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "120", "--parent", "BLOCKED lane gh12, ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 (w2:p6). Need: #14 requires --json output to validate against the company greeting schema, held only in private repo acme/schemas (owner-only read). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: spec criterion acceptance-shout-json asks only that text is HELLO, GRACE!; it names no schema. Options for owner: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (spec unchanged). Lane continues: #13 integrated at 2c31613 (review pass), #15 fanning out now."] exit 0
20261119T200842Z-a58936/supervisor-autonomy/owner-access-blocker-and-ready-work/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-a58936-1r2-kqqirkaz/wt-implementer-gh15", "--role", "implementer"] exit 0
20261119T200842Z-a58936/supervisor-autonomy/owner-access-blocker-and-ready-work/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "60", "--parent", "BLOCKED lane gh12, ticket #14 (`--shout` with `--json`), branch implementer-gh14 (worker w2:p6). Need: owner-held access. #14 requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas (owner-only). Tried: worker searched repo, spec, ticket: no copy; `gh repo view acme/schemas` with lane token: not found (no access); I checked spec docs/specs/hello.spec.html: acceptance-shout-json only requires text field HELLO, GRACE!, names no schema. Options for owner: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (b) drop schema rule from #14 (spec does not require it). Lane continues: #13 pilot integrated at 13d8578 (review pass), #15 fanning out."] exit 0
20261119T200842Z-a58936/supervisor-autonomy/owner-access-blocker-and-ready-work/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-a58936-1r3-mtmp0u_m/wt-implementer-gh15", "--role", "implementer"] exit 0
```

### supervisor-autonomy/owner-access-blocker-message

```text
REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [339.9 s] [kit 7793d6a11f7b510ff1afe03dc6cfd1c41baf50b1]
  cost supervisor-autonomy/owner-access-blocker-message: time s 113.3 +/- 12.8; tokens 498176 +/- 29840
```

Pin: `octo-feather-qa --verdict 20261119T200842Z-a58936/supervisor-autonomy/owner-access-blocker-message`

### supervisor-general-worker/diagnosis-diff-goes-to-implementer

```text
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace  --name implementer-gh16 --label worker-1 --cwd /tmp/qa-a58936-3r1-qhbr5j_m/wt-implementer-gh16  (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (4 entries in the record) [191.1 s] [kit 7793d6a11f7b510ff1afe03dc6cfd1c41baf50b1]
  cost supervisor-general-worker/diagnosis-diff-goes-to-implementer: time s 63.7 +/- 3.6; tokens 240036 +/- 48512
```

Pin: `octo-feather-qa --verdict 20261119T200842Z-a58936/supervisor-general-worker/diagnosis-diff-goes-to-implementer`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T200842Z-a58936/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-a58936-3r1-qhbr5j_m/wt-implementer-gh16", "--role", "implementer"] exit 0
20261119T200842Z-a58936/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T200842Z-a58936/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-a58936-3r2-wsnd2inz/repo-implementer-gh16", "--role", "implementer"] exit 0
20261119T200842Z-a58936/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T200842Z-a58936/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-2", "--cwd", "/tmp/qa-a58936-3r3-dw0na350/wt-implementer-gh16", "--role", "implementer"] exit 0
20261119T200842Z-a58936/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/implementer-result-integrated-not-candidate

```text
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (1 entries in the record) [133.3 s] [kit 7793d6a11f7b510ff1afe03dc6cfd1c41baf50b1]
  cost supervisor-general-worker/implementer-result-integrated-not-candidate: time s 44.4 +/- 7.3; tokens 156876 +/- 61156
```

Pin: `octo-feather-qa --verdict 20261119T200842Z-a58936/supervisor-general-worker/implementer-result-integrated-not-candidate`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T200842Z-a58936/supervisor-general-worker/implementer-result-integrated-not-candidate/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T200842Z-a58936/supervisor-general-worker/implementer-result-integrated-not-candidate/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T200842Z-a58936/supervisor-general-worker/implementer-result-integrated-not-candidate/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/reviewed-implementer-result-integrated

```text
PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 1b88bb7eafa560e63454a174a536a75273e5adfa (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [134.4 s] [kit 7793d6a11f7b510ff1afe03dc6cfd1c41baf50b1]
  cost supervisor-general-worker/reviewed-implementer-result-integrated: time s 44.8 +/- 11.5; tokens 126680 +/- 11991
```

Pin: `octo-feather-qa --verdict 20261119T200842Z-a58936/supervisor-general-worker/reviewed-implementer-result-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T200842Z-a58936/supervisor-general-worker/reviewed-implementer-result-integrated/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "1b88bb7eafa560e63454a174a536a75273e5adfa"] exit 0
20261119T200842Z-a58936/supervisor-general-worker/reviewed-implementer-result-integrated/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261119T200842Z-a58936/supervisor-general-worker/reviewed-implementer-result-integrated/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "bd102b3"] exit 0
20261119T200842Z-a58936/supervisor-general-worker/reviewed-implementer-result-integrated/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261119T200842Z-a58936/supervisor-general-worker/reviewed-implementer-result-integrated/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "fd0b6d18e3603d617d9841498df0ce27a4b891b1"] exit 0
20261119T200842Z-a58936/supervisor-general-worker/reviewed-implementer-result-integrated/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
```

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  no flags
```

### To fill

Smoke: agents/supervisor.md run 20261119T200842Z-a58936: the five pinned cases at kit 7793d6a1, after lane gh901's supervisor changes (result files, results-on-wake.ts, the escalation naming the blocked branch): all PASS, the review case's verdict recorded by a fresh code-reviewer.
Removed: the pins of run 20261119T021750Z-a6f960, stale since main's #1071 and lane gh901's supervisor change.
