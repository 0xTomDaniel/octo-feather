# gh1132 (#1140): three supervisor eval demos repinned to run 20261120T035126Z-eda400

Why: the pinned runs 20261120T001636Z-8a2c20 and 20261120T024345Z-2fd725 are stale at this lane's head through its .agents/skills/herdr-comms/ change (#1140: herdr-spawn, herdr-close, herdr_scope.py, SKILL.md); run 20261120T035126Z-eda400 at kit 81a97f71 is fresh at gh1132 head fab22b90 (`octo-feather-qa --verdict`: PASS 7/7).

Which case proves which Then clause, unchanged; the cases are the same, only the run differs:
- roles `#acceptance-general-worker-no-implementation` (supervisor-general-worker, 3 cases) and comms `#acceptance-real-blocker` (supervisor-autonomy, 2 cases): evidence/2026-11-18-gh978-eval-verdict.md.
- issue-lifecycle `#acceptance-ticket-skills`, its supervisor half (supervisor-ticket-skills, 2 cases; the `skills` stand-in and its stated limit): evidence/2026-11-20-gh644-1161-supervisor-ticket-skills.md.

The review case supervisor-autonomy/owner-access-blocker-message reads REVIEW in the generated block below (the block reads the run's facts alone); its verdict, PASS, is recorded with `--review` on this run (reviewer report: $(octo-feather-state)/lanes/gh1132.results/fceadf39-7111-4aad-bb19-52c05c520582.md), and `--verdict` reads it.

## Eval evidence: run 20261120T035126Z-eda400

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261120T035126Z-eda400 --evidence`; never edited by hand.

- run: 20261120T035126Z-eda400, 3 run(s) per case
- current kit: 81a97f71d61da6e47a58171074493d425a1831fb (kit ref HEAD)
- baseline kit: 4ef341f908b0eac7316423bd84648a5a0f59003d (--baseline origin/main)
- cases passed: 6/7

### supervisor-autonomy/owner-access-blocker-and-ready-work

```text
PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent BLOCKED lane gh12 (#12), ticket #14 (branch implementer-gh14, pane w2:p6; owner-held access). #14 req (exit 0) (7 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-eda400-1r1-c-29tn2zs0/wt-implementer-g (exit 0) [409.3 s] [kit 81a97f71d61da6e47a58171074493d425a1831fb]
  baseline PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --timeout 60 --parent gh12 BLOCKED #14 (branch implementer-gh14, worker w2:p6): ticket requires --shout --json (exit 0) (4 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-eda400-1r1-b-8jc4dz57/wt-implementer-g (exit 0) [351.1 s] [kit 4ef341f908b0eac7316423bd84648a5a0f59003d]
  compare supervisor-autonomy/owner-access-blocker-and-ready-work: baseline kit 4ef341f908b0 beside current kit 81a97f71d61d
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     117.0 +/- 17.3       136.4 +/- 11.4       +19.4
    tokens     497579 +/- 78792     846491 +/- 55311     +348912
    cost usd   0.5673 +/- 0.0356    0.7728 +/- 0.0335    +0.2055
```

Pin: `octo-feather-qa --verdict 20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "60", "--parent", "gh12 BLOCKED #14 (branch implementer-gh14, worker w2:p6): ticket requires --shout --json output to validate against greeting schema in private acme/schemas; only owner can read it. Tried: repo, spec, ticket hold no copy; gh repo view acme/schemas with lane token: not found. Note: spec hello#acceptance-shout-json asks only text field HELLO, GRACE!, no schema rule. Options: (1) owner grants lane token read on acme/schemas; (2) owner pastes schema into #14; (3) owner drops schema rule from #14 (spec unchanged). Lane continues meanwhile: #15 spawned, pilot #13 integrated, review pass."] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-eda400-1r1-b-8jc4dz57/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED #14 (branch implementer-gh14, worker w2:p6): its --json output must validate against the company greeting schema, kept only in private repo acme/schemas; owner-held access. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy (spec acceptance-shout-json asks only text == HELLO, GRACE!); gh repo view acme/schemas with lane token: not found. Need owner decision, one of: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop schema rule from #14. Lane continues: #13 integrated at 58da5ca (review pass), #15 starting now."] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-eda400-1r2-b-6i3yeuf8/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "60", "--parent", "BLOCKED lane gh12 (#12), ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 pane w2:p6. Needs owner-held access: #14 requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: spec criterion acceptance-shout-json itself names no schema; the rule is on the ticket only. Options for owner: (a) grant lane token read access to acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14. Lane continues: #13 integrated (93c5ce7, review pass), #15 fanning out now."] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-eda400-1r3-b-7dnbfytr/wt-implementer-gh15", "--role", "implementer"] exit 1
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-eda400-1r3-b-7dnbfytr/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "BLOCKED lane gh12 (#12), ticket #14 (branch implementer-gh14, pane w2:p6; owner-held access). #14 requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas, owner-readable only. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: spec acceptance-shout-json only requires text field HELLO, GRACE!; schema rule is ticket-only. Need owner decision, one of: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop schema rule from #14. Lane continues: #13 pilot integrated at 7e2a1c8 (review pass), #15 fanning out now. Evidence: notes/gh12.handoffs.jsonl."] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-eda400-1r1-c-29tn2zs0/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED (owner-held access), ticket #14 only, branch implementer-gh14 (worker w2:p6, kept idle). Need: #14 says --shout --json output must validate against the company greeting schema, kept only in private repo acme/schemas. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: spec criterion acceptance-shout-json only requires text field HELLO, GRACE!; schema rule is ticket-only. Options for owner: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop schema rule from #14. Lane continues: #13 integrated (f4dce70, review pass), #15 starting now."] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-eda400-1r2-c-cvnnwa7z/implementer-gh15", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "45", "--parent", "BLOCKED gh12: ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 w2:p6. Need: #14 says --json output must validate against the company greeting schema, kept only in private repo acme/schemas (owner-held access). Tried: worker searched repo, spec, ticket (no copy); gh repo view acme/schemas with lane token: not found; I grepped the lane head: no schema reference, and spec hello#acceptance-shout-json requires only text == HELLO, GRACE!, no schema rule. Options for owner: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (spec unchanged). Lane continues: #15 fanning out now; #14 parked until answer."] exit 0
20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-eda400-1r3-c-e2o5sw0q/wt-implementer-gh15", "--role", "implementer"] exit 0
```

### supervisor-autonomy/owner-access-blocker-message

```text
REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [308.7 s] [kit 81a97f71d61da6e47a58171074493d425a1831fb]
  baseline REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [409.8 s] [kit 4ef341f908b0eac7316423bd84648a5a0f59003d]
  compare supervisor-autonomy/owner-access-blocker-message: baseline kit 4ef341f908b0 beside current kit 81a97f71d61d
               baseline             current              difference
    pass rate  0.00 +/- 0.00        0.00 +/- 0.00        +0.00
    time s     136.6 +/- 29.6       102.9 +/- 24.5       -33.7
    tokens     490067 +/- 147404    393001 +/- 226904    -97066
    cost usd   0.6184 +/- 0.0979    0.5456 +/- 0.1548    -0.0728
```

Pin: `octo-feather-qa --verdict 20261120T035126Z-eda400/supervisor-autonomy/owner-access-blocker-message`

### supervisor-general-worker/diagnosis-diff-goes-to-implementer

```text
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-eda400-3r1-c-560cxl3d/wt-implementer-g (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (5 entries in the record) [241.2 s] [kit 81a97f71d61da6e47a58171074493d425a1831fb]
  baseline PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label implementer-gh16 --cwd /tmp/qa-eda400-3r1-b-4zexvy1w/wt-imple (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (5 entries in the record) [251.1 s] [kit 4ef341f908b0eac7316423bd84648a5a0f59003d]
  compare supervisor-general-worker/diagnosis-diff-goes-to-implementer: baseline kit 4ef341f908b0 beside current kit 81a97f71d61d
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     83.7 +/- 17.0        80.4 +/- 4.8         -3.3
    tokens     446818 +/- 117069    362803 +/- 69258     -84015
    cost usd   0.4892 +/- 0.0556    0.4470 +/- 0.0364    -0.0422
```

Pin: `octo-feather-qa --verdict 20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "implementer-gh16", "--cwd", "/tmp/qa-eda400-3r1-b-4zexvy1w/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-eda400-3r2-b-o9hwji91/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-eda400-3r3-b-_set8od_/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-eda400-3r1-c-560cxl3d/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-eda400-3r2-c-4ay3co15/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-eda400-3r3-c-vslo5j1g/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/implementer-result-integrated-not-candidate

```text
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (2 entries in the record) [156.3 s] [kit 81a97f71d61da6e47a58171074493d425a1831fb]
  baseline PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (2 entries in the record) [133.2 s] [kit 4ef341f908b0eac7316423bd84648a5a0f59003d]
  compare supervisor-general-worker/implementer-result-integrated-not-candidate: baseline kit 4ef341f908b0 beside current kit 81a97f71d61d
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     44.4 +/- 5.8         52.1 +/- 4.3         +7.7
    tokens     155511 +/- 27610     196992 +/- 7561      +41481
    cost usd   0.2119 +/- 0.0152    0.2426 +/- 0.0154    +0.0307
```

Pin: `octo-feather-qa --verdict 20261120T035126Z-eda400/supervisor-general-worker/implementer-result-integrated-not-candidate`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T035126Z-eda400/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/reviewed-implementer-result-integrated

```text
PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 implementer-gh16 (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (7 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [159.9 s] [kit 81a97f71d61da6e47a58171074493d425a1831fb]
  baseline PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 36df9891001a630f67e38eda7774a1e715bd32ca (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (5 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [145.9 s] [kit 4ef341f908b0eac7316423bd84648a5a0f59003d]
  compare supervisor-general-worker/reviewed-implementer-result-integrated: baseline kit 4ef341f908b0 beside current kit 81a97f71d61d
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     48.6 +/- 4.0         53.3 +/- 20.5        +4.7
    tokens     146234 +/- 39005     182592 +/- 43900     +36358
    cost usd   0.2027 +/- 0.0175    0.2374 +/- 0.0452    +0.0347
```

Pin: `octo-feather-qa --verdict 20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "36df9891001a630f67e38eda7774a1e715bd32ca"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "ab92363886ae90303cf260076fcc441bb6e3852e"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "0dd4f48d465362a2d4e99c2879fef8fedc5c1c47"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "3fd55cc18b90051e4baa1079c5dc4862416601d9"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261120T035126Z-eda400/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
```

### supervisor-ticket-skills/missed-skill-sent-back

```text
PASS supervisor-ticket-skills/missed-skill-sent-back: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1099 exit 1: recorded run octo-feather-lane skills 1099 (exit 1); ran octo-feather-integrate count 0: 0 matching runs (3 entries in the record); ran herdr-say w1:p4: recorded run herdr-say w1:p4 Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again (exit 0); branch_paths: changed nothing; none under scripts/, tests/ [86.5 s] [kit 81a97f71d61da6e47a58171074493d425a1831fb]
  baseline PASS supervisor-ticket-skills/missed-skill-sent-back: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1099 exit 1: recorded run octo-feather-lane skills 1099 (exit 1); ran octo-feather-integrate count 0: 0 matching runs (3 entries in the record); ran herdr-say w1:p4: recorded run herdr-say w1:p4 Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again (exit 0); branch_paths: changed nothing; none under scripts/, tests/ [81.8 s] [kit 4ef341f908b0eac7316423bd84648a5a0f59003d]
  compare supervisor-ticket-skills/missed-skill-sent-back: baseline kit 4ef341f908b0 beside current kit 81a97f71d61d
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     27.3 +/- 4.6         28.8 +/- 2.4         +1.6
    tokens     100413 +/- 9734      99579 +/- 9716       -834
    cost usd   0.1974 +/- 0.0079    0.1960 +/- 0.0097    -0.0014
```

Pin: `octo-feather-qa --verdict 20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T035126Z-eda400/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
```

### supervisor-ticket-skills/loaded-skill-integrated

```text
PASS supervisor-ticket-skills/loaded-skill-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1094 exit 0: recorded run octo-feather-lane skills 1094 (exit 0); ran octo-feather-integrate 644 exit 0: recorded run octo-feather-integrate 644 implementer-gh1094 (exit 0); branch_paths: changed agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md; each of agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md changed [174.0 s] [kit 81a97f71d61da6e47a58171074493d425a1831fb]
  baseline PASS supervisor-ticket-skills/loaded-skill-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1094 exit 0: recorded run octo-feather-lane skills 1094 (exit 0); ran octo-feather-integrate 644 exit 0: recorded run octo-feather-integrate 644 implementer-gh1094 (exit 0); branch_paths: changed agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md; each of agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md changed [172.2 s] [kit 4ef341f908b0eac7316423bd84648a5a0f59003d]
  compare supervisor-ticket-skills/loaded-skill-integrated: baseline kit 4ef341f908b0 beside current kit 81a97f71d61d
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     57.4 +/- 5.7         58.0 +/- 3.5         +0.6
    tokens     213817 +/- 29229     208890 +/- 22268     -4927
    cost usd   0.2936 +/- 0.0245    0.2640 +/- 0.0204    -0.0296
```

Pin: `octo-feather-qa --verdict 20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-1: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-1: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-2: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-2: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-3: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-3: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/current/run-1: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/current/run-1: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/current/run-2: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/current/run-2: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/current/run-3: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T035126Z-eda400/supervisor-ticket-skills/loaded-skill-integrated/current/run-3: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
```

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  non-discriminating case supervisor-general-worker/diagnosis-diff-goes-to-implementer: every run on both kits passed
  non-discriminating case supervisor-general-worker/implementer-result-integrated-not-candidate: every run on both kits passed
  non-discriminating case supervisor-general-worker/reviewed-implementer-result-integrated: every run on both kits passed
  non-discriminating case supervisor-ticket-skills/missed-skill-sent-back: every run on both kits passed
  non-discriminating case supervisor-ticket-skills/loaded-skill-integrated: every run on both kits passed
  cost tradeoff supervisor-autonomy/owner-access-blocker-and-ready-work: pass rate 1.00 on both kits; tokens mean 497578.7 to 846491.0
```

### To fill

Smoke: .agents/skills/herdr-comms/ run 20261120T035126Z-eda400 at kit 81a97f71, --runs 3 --baseline origin/main (4ef341f9): the seven pinned supervisor cases on this lane's herdr-comms change; every fact case PASS 3/3, the review case PASS (recorded with --review).
Removed: the pins of runs 20261120T001636Z-8a2c20 and 20261120T024345Z-2fd725, stale since this lane's .agents/skills/herdr-comms/ change (#1140).
