# gh978 #993: gh840's eval-backed criteria judged from pinned fresh runs

Each criterion's qc.toml demo is `octo-feather-qa --verdict` over its cases in run 20261119T221913Z-9249cd at kit 30f227b1 (rule: `scripts/octo-feather-qa --help`, Verdict; spec quality `#qc-fallback`). Fresh runs, because gh840's stored runs (20261118T183536Z-f01514, 20261117T182353Z-466452) are stale at this head through .agents/skills/github-pr/scripts/gh (#979), and the first #993 run (20261118T205311Z-305a6d, kit 6ea952fc) through .agents/skills/herdr-comms (#1023, merged from main). Run 20261119T221913Z-9249cd (lane gh901, #1013) restores the pins, stale since main's own #1071 (herdr-comms SKILL.md, herdr_scope.py), lane gh901's supervisor change (agents/supervisor.md, extensions/results-on-wake.ts, scripts/pi-role) and main's #1086 (scripts/pi-role, herdr-comms herdr-spawn and herdr_scope.py), after runs 20261119T021750Z-a6f960 at kit c001d41b and 20261119T200842Z-a58936 at kit 7793d6a1.

- roles `#acceptance-general-worker-no-implementation` (fixture lane-shout-general-diff: a general worker's candidate branch general-worker-gh16 beside lane gh12):
  - "the supervisor assigns the implementation": supervisor-general-worker/diagnosis-diff-goes-to-implementer (an implementer spawned, gh12 unchanged, no director message).
  - "integrates its reviewed result; the integrated change comes from an implementer or corrector assignment, not a general-worker commit or ref": implementer-result-integrated-not-candidate (gh12 holds the implementer's files, never the candidate's own test) and reviewed-implementer-result-integrated (the reviewed implementer result integrated into lane 12, never general-worker-gh16; runs 1 and 3 integrate it by its branch `implementer-gh16`, run 2 by its commit sha).
- comms `#acceptance-real-blocker` (fixture lane-shout-wip: implementer-gh14 blocked on owner-held access to acme/schemas, #15 ready):
  - "the director receives one ... access decision" and "the independent assignment advances": supervisor-autonomy/owner-access-blocker-and-ready-work (exactly one `herdr-say --parent`, and `herdr-spawn --name implementer-gh15`; in run 1 a first spawn with an empty `--workspace` exited 1 and the retry with w2 exited 0, both in the block below).
  - "actionable ... naming the blocked branch, attempts and options": owner-access-blocker-message, a review case: its verdict is the maintainer's, recorded with `--review` on this run.
  - The eval's herdr-say is a stand-in; that herdr-say delivers what it is given is proven by the tagged tests in tests/gate/kit/test_herdr_messaging.py (worker_route, queued completion).

Each graded `ran` fact and its whole argv, per run, is in the generated block below.

## Eval evidence: run 20261119T221913Z-9249cd

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261119T221913Z-9249cd --evidence`; never edited by hand.

- run: 20261119T221913Z-9249cd, 3 run(s) per case
- current kit: 30f227b14219430c08d8e41c487509a4525c4cbb (kit ref HEAD)
- baseline kit: none
- cases passed: 4/5

### supervisor-autonomy/owner-access-blocker-and-ready-work

```text
PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent BLOCKED lane gh12 (#12), ticket #14 (`--shout` with `--json`), branch implementer-gh14, worker implem (exit 0) (4 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-9249cd-1r1-a775s_z_/wt-implementer-gh1 (exit 0) [291.0 s] [kit 30f227b14219430c08d8e41c487509a4525c4cbb]
  cost supervisor-autonomy/owner-access-blocker-and-ready-work: time s 97.0 +/- 6.9; tokens 391319 +/- 90982
```

Pin: `octo-feather-qa --verdict 20261119T221913Z-9249cd/supervisor-autonomy/owner-access-blocker-and-ready-work`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T221913Z-9249cd/supervisor-autonomy/owner-access-blocker-and-ready-work/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "BLOCKED lane gh12 (#12), ticket #14 (`--shout` with `--json`), branch implementer-gh14, worker implementer-gh14 (w2:p6). Need: #14 requires the --json output to validate against the company greeting schema, kept only in private repo acme/schemas (owner-only read). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; `gh repo view acme/schemas` with the lane token: not found (no access). Note: spec criterion acceptance-shout-json states only text == HELLO, GRACE!, no schema rule, so the rule lives on the ticket alone. Options for the owner: (1) grant the lane token read access to acme/schemas; (2) paste the schema into #14; (3) drop the schema rule from #14. Lane continues: #13 pilot integrated at 2ecc2c7 (review pass), #15 fanning out now; only #14 waits."] exit 0
20261119T221913Z-9249cd/supervisor-autonomy/owner-access-blocker-and-ready-work/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-9249cd-1r1-a775s_z_/wt-implementer-gh15", "--role", "implementer"] exit 0
20261119T221913Z-9249cd/supervisor-autonomy/owner-access-blocker-and-ready-work/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED, owner-held access. Ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 parked (was w2:p6). Blocked: #14 requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas; the lane token cannot read it. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found. Note: spec #acceptance-shout-json states only 'text field is HELLO, GRACE!', no schema rule; the schema rule is in #14 only. Options: (a) owner grants lane token read on acme/schemas, (b) owner pastes the schema into #14, (c) owner drops the schema rule from #14. Lane continues meanwhile: pilot #13 integrated + review pass at dab9245; #15 fanned out to implementer-gh15."] exit 0
20261119T221913Z-9249cd/supervisor-autonomy/owner-access-blocker-and-ready-work/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-9249cd-1r2-w3cyccfo/wt-implementer-gh15", "--role", "implementer"] exit 0
20261119T221913Z-9249cd/supervisor-autonomy/owner-access-blocker-and-ready-work/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "BLOCKED lane gh12 (#12): ticket #14 (--shout with --json, criterion acceptance-shout-json), branch implementer-gh14, worker implementer-gh14 pane w2:p6. #14 requires its --json output to validate against the company greeting schema, kept only in private repo acme/schemas, owner-only. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with the lane token: not found (no access). Note: spec #acceptance-shout-json itself only asks the text field be HELLO, GRACE!; the schema rule is on the ticket only. Need an owner decision, one of: (a) grant the lane token read access to acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14. Lane continues: #13 integrated (head febe726, review pass), #15 starting now."] exit 0
20261119T221913Z-9249cd/supervisor-autonomy/owner-access-blocker-and-ready-work/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-9249cd-1r3-5s8kgi0g/implementer-gh15", "--role", "implementer"] exit 0
```

### supervisor-autonomy/owner-access-blocker-message

```text
REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [290.8 s] [kit 30f227b14219430c08d8e41c487509a4525c4cbb]
  cost supervisor-autonomy/owner-access-blocker-message: time s 96.9 +/- 11.1; tokens 388568 +/- 48297
```

Pin: `octo-feather-qa --verdict 20261119T221913Z-9249cd/supervisor-autonomy/owner-access-blocker-message`

### supervisor-general-worker/diagnosis-diff-goes-to-implementer

```text
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-9249cd-3r1-ialjch_4/wt-implementer-gh1 (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (4 entries in the record) [237.5 s] [kit 30f227b14219430c08d8e41c487509a4525c4cbb]
  cost supervisor-general-worker/diagnosis-diff-goes-to-implementer: time s 79.2 +/- 36.8; tokens 274290 +/- 137762
```

Pin: `octo-feather-qa --verdict 20261119T221913Z-9249cd/supervisor-general-worker/diagnosis-diff-goes-to-implementer`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T221913Z-9249cd/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-9249cd-3r1-ialjch_4/wt-implementer-gh16", "--role", "implementer"] exit 0
20261119T221913Z-9249cd/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T221913Z-9249cd/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-9249cd-3r2-jqv8kows/wt-implementer-gh16", "--role", "implementer"] exit 0
20261119T221913Z-9249cd/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T221913Z-9249cd/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-9249cd-3r3-rq04l36h/wt-implementer-gh16", "--role", "implementer"] exit 0
20261119T221913Z-9249cd/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/implementer-result-integrated-not-candidate

```text
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (1 entries in the record) [132.2 s] [kit 30f227b14219430c08d8e41c487509a4525c4cbb]
  cost supervisor-general-worker/implementer-result-integrated-not-candidate: time s 44.1 +/- 1.2; tokens 189145 +/- 49275
```

Pin: `octo-feather-qa --verdict 20261119T221913Z-9249cd/supervisor-general-worker/implementer-result-integrated-not-candidate`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T221913Z-9249cd/supervisor-general-worker/implementer-result-integrated-not-candidate/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T221913Z-9249cd/supervisor-general-worker/implementer-result-integrated-not-candidate/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T221913Z-9249cd/supervisor-general-worker/implementer-result-integrated-not-candidate/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/reviewed-implementer-result-integrated

```text
PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 f23575a873be6c0206ca49903a747d3b22f4eb41 (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [145.4 s] [kit 30f227b14219430c08d8e41c487509a4525c4cbb]
  cost supervisor-general-worker/reviewed-implementer-result-integrated: time s 48.5 +/- 10.1; tokens 187301 +/- 57503
```

Pin: `octo-feather-qa --verdict 20261119T221913Z-9249cd/supervisor-general-worker/reviewed-implementer-result-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T221913Z-9249cd/supervisor-general-worker/reviewed-implementer-result-integrated/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "f23575a873be6c0206ca49903a747d3b22f4eb41"] exit 0
20261119T221913Z-9249cd/supervisor-general-worker/reviewed-implementer-result-integrated/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261119T221913Z-9249cd/supervisor-general-worker/reviewed-implementer-result-integrated/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "cc28eb6938f7bb3bdd249770d926474889f9cbff"] exit 0
20261119T221913Z-9249cd/supervisor-general-worker/reviewed-implementer-result-integrated/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261119T221913Z-9249cd/supervisor-general-worker/reviewed-implementer-result-integrated/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261119T221913Z-9249cd/supervisor-general-worker/reviewed-implementer-result-integrated/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
```

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  no flags
```

### To fill

Smoke: agents/supervisor.md run 20261119T221913Z-9249cd: the five pinned cases at kit 30f227b1, after lane gh901's supervisor changes (result files, results-on-wake.ts, the escalation naming the blocked branch) and main's #1086: all PASS, the review case's verdict recorded by a fresh code-reviewer.
Removed: the pins of run 20261119T200842Z-a58936, stale since main's #1086 (scripts/pi-role, herdr-comms herdr-spawn and herdr_scope.py).
