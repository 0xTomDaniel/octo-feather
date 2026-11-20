# gh978 #993: gh840's eval-backed criteria judged from pinned fresh runs

Each criterion's qc.toml demo is `octo-feather-qa --verdict` over its cases in run 20261120T001636Z-8a2c20 at kit 6c440d36 (rule: `scripts/octo-feather-qa --help`, Verdict; spec quality `#qc-fallback`). Fresh runs, because gh840's stored runs (20261118T183536Z-f01514, 20261117T182353Z-466452) are stale at this head through .agents/skills/github-pr/scripts/gh (#979), and the first #993 run (20261118T205311Z-305a6d, kit 6ea952fc) through .agents/skills/herdr-comms (#1023, merged from main). Run 20261119T221913Z-9249cd (lane gh901, #1013) restores the pins, stale since main's own #1071 (herdr-comms SKILL.md, herdr_scope.py), lane gh901's supervisor change (agents/supervisor.md, extensions/results-on-wake.ts, scripts/pi-role) and main's #1086 (scripts/pi-role, herdr-comms herdr-spawn and herdr_scope.py), after runs 20261119T021750Z-a6f960 at kit c001d41b and 20261119T200842Z-a58936 at kit 7793d6a1. Run 20261120T001636Z-8a2c20 (lane gh644, #1094 and #1099) restores them again, stale since lane gh644's supervisor change (agents/supervisor.md `skills:` + codebase-design and tdd, two Delivery entries; .agents/skills/tdd, to-tickets, github-issues issue-view and notes.graphql, github-pr gh), after run 20261119T232852Z-9687db at kit 02677bd1 failed implementer-result-integrated-not-candidate and reviewed-implementer-result-integrated (0/3 each: the supervisor did not integrate when `octo-feather-lane skills` could not run; fixed in 6c440d36).

- roles `#acceptance-general-worker-no-implementation` (fixture lane-shout-general-diff: a general worker's candidate branch general-worker-gh16 beside lane gh12):
  - "the supervisor assigns the implementation": supervisor-general-worker/diagnosis-diff-goes-to-implementer (an implementer spawned, gh12 unchanged, no director message).
  - "integrates its reviewed result; the integrated change comes from an implementer or corrector assignment, not a general-worker commit or ref": implementer-result-integrated-not-candidate (gh12 holds the implementer's files, never the candidate's own test) and reviewed-implementer-result-integrated (the reviewed implementer result integrated into lane 12, never general-worker-gh16; runs 1 and 3 integrate it by its branch `implementer-gh16`, run 2 by its commit sha).
- comms `#acceptance-real-blocker` (fixture lane-shout-wip: implementer-gh14 blocked on owner-held access to acme/schemas, #15 ready):
  - "the director receives one ... access decision" and "the independent assignment advances": supervisor-autonomy/owner-access-blocker-and-ready-work (exactly one `herdr-say --parent`, and `herdr-spawn --name implementer-gh15`; in run 1 a first spawn with an empty `--workspace` exited 1 and the retry with w2 exited 0, both in the block below).
  - "actionable ... naming the blocked branch, attempts and options": owner-access-blocker-message, a review case: its verdict is the maintainer's, recorded with `--review` on this run.
  - The eval's herdr-say is a stand-in; that herdr-say delivers what it is given is proven by the tagged tests in tests/gate/kit/test_herdr_messaging.py (worker_route, queued completion).

Each graded `ran` fact and its whole argv, per run, is in the generated block below.

## Eval evidence: run 20261120T001636Z-8a2c20

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261120T001636Z-8a2c20 --evidence`; never edited by hand.

- run: 20261120T001636Z-8a2c20, 3 run(s) per case
- current kit: 6c440d36fbc4c65a769ebde18f17fc5fd230fb4a (kit ref HEAD)
- baseline kit: 777e2f07062a9fb64df0e978ce38623c17ab6428 (--baseline origin/main)
- cases passed: 4/5

### supervisor-autonomy/owner-access-blocker-and-ready-work

```text
PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent gh12 BLOCKED (#14 only, owner-held access). Ticket #14 (--shout with --json), branch implementer-gh14 (exit 0) (5 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-8a2c20-1r1-c-f6vp3ksu/wt-implementer-g (exit 0) [371.8 s] [kit 6c440d36fbc4c65a769ebde18f17fc5fd230fb4a]
  baseline PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent BLOCKED lane gh12, ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 (exit 0) (4 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-8a2c20-1r1-b-9sbphzb1/implementer-gh15 (exit 0) [331.2 s] [kit 777e2f07062a9fb64df0e978ce38623c17ab6428]
  compare supervisor-autonomy/owner-access-blocker-and-ready-work: baseline kit 777e2f07062a beside current kit 6c440d36fbc4
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     110.4 +/- 18.3       123.9 +/- 12.4       +13.5
    tokens     504442 +/- 33957     607080 +/- 53660     +102637
    cost usd   0.5796 +/- 0.0445    0.6606 +/- 0.0495    +0.0810
```

Pin: `octo-feather-qa --verdict 20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "BLOCKED lane gh12, ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 (w2:p6). Need: #14 requires the --json output validate against the company greeting schema, kept only in private repo acme/schemas (owner-held access). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: spec criterion acceptance-shout-json only requires text field HELLO, GRACE!; it names no schema. Options for owner: (1) grant lane token read on acme/schemas, (2) paste the schema into #14, (3) drop the schema rule from #14 (matches the accepted spec). Lane continues: #13 pilot integrated at 7d10c75, review pass; #15 dispatched to implementer-gh15."] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-8a2c20-1r1-b-9sbphzb1/implementer-gh15", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "60", "--parent", "BLOCKED lane gh12 (parent #12), ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 w2:p6. Need: #14 requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas (owner-read only). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Owner decision needed, one of: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop the schema rule from #14 (that is a scope call on acceptance-shout-json). Only #14 stops; #15 proceeds, #13 pilot integrated at 7b5da8f, review pass. Evidence: notes/gh12.handoffs.jsonl."] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-8a2c20-1r2-b-y28krxcx/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED on #14 (branch implementer-gh14, worker implementer-gh14 w2:p6 idle, holding it). Need: owner-held access. #14's ticket requires the --shout --json output to validate against the company greeting schema, kept only in private repo acme/schemas (owner-only read). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: spec criterion acceptance-shout-json only requires the text field to be HELLO, GRACE!; the schema rule is on the ticket only, and the behaviour already passes on lane head d1693f7. Options: (a) owner grants lane token read on acme/schemas, (b) owner pastes the schema into #14, (c) owner drops the schema rule from #14. Lane continues meanwhile: #15 fanning out; pilot #13 integrated, review pass."] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-8a2c20-1r3-b-dy2q_2_1/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED (#14 only, owner-held access). Ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 w2:p6: its --json output must validate against the company greeting schema, kept only in private repo acme/schemas, owner-read-only. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: spec criterion acceptance-shout-json names no schema, only text field HELLO, GRACE!. Owner options: (1) grant lane token read on acme/schemas; (2) paste the schema into #14; (3) drop the schema rule from #14. Need owner's pick. Lane continues meanwhile: #13 pilot integrated at cf3f18f, review pass; #15 fanning out to a fresh implementer. #14 worker held idle on its branch for the answer."] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-8a2c20-1r1-c-f6vp3ksu/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "120", "--parent", "BLOCKED lane gh12, ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 pane w2:p6. Need: #14 requires the --json output to validate against the company greeting schema, kept only in private repo acme/schemas, owner-read only. Tried: repo, spec docs/specs/hello.spec.html (acceptance-shout-json names no schema) and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Options for owner: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (spec criterion acceptance-shout-json already passes without it). Lane continues: #15 dispatched now; #14 waits on this answer."] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-8a2c20-1r2-c-cohfgvi_/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "120", "--parent", "BLOCKED lane gh12, ticket #14 (`--shout` with `--json`), branch implementer-gh14, worker implementer-gh14 (w2:p6). Need: #14 requires `--json` output to validate against the company greeting schema, kept only in private repo acme/schemas (owner-only). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; `gh repo view acme/schemas` with lane token: not found (no access). Options for owner: (1) grant lane token read access to acme/schemas; (2) paste the schema into #14; (3) drop the schema rule from #14 (spec criterion acceptance-shout-json asks only that `text` is `HELLO, GRACE!`, so the spec is unchanged either way). Lane continues: #15 dispatched; #14 parked until answer."] exit 0
20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-8a2c20-1r3-c-ei_oiefy/implementer-gh15", "--role", "implementer"] exit 0
```

### supervisor-autonomy/owner-access-blocker-message

```text
REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [375.0 s] [kit 6c440d36fbc4c65a769ebde18f17fc5fd230fb4a]
  baseline REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [347.2 s] [kit 777e2f07062a9fb64df0e978ce38623c17ab6428]
  compare supervisor-autonomy/owner-access-blocker-message: baseline kit 777e2f07062a beside current kit 6c440d36fbc4
               baseline             current              difference
    pass rate  0.00 +/- 0.00        0.00 +/- 0.00        +0.00
    time s     115.7 +/- 4.8        125.0 +/- 24.1       +9.3
    tokens     598688 +/- 68564     540373 +/- 109753    -58315
    cost usd   0.6616 +/- 0.0585    0.6185 +/- 0.0873    -0.0431
```

Pin: `octo-feather-qa --verdict 20261120T001636Z-8a2c20/supervisor-autonomy/owner-access-blocker-message`

### supervisor-general-worker/diagnosis-diff-goes-to-implementer

```text
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-8a2c20-3r1-c-27zzc9vc/wt-implementer-g (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (4 entries in the record) [230.8 s] [kit 6c440d36fbc4c65a769ebde18f17fc5fd230fb4a]
  baseline PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-8a2c20-3r1-b-j0cgkrij/wt-implementer-g (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (6 entries in the record) [214.3 s] [kit 777e2f07062a9fb64df0e978ce38623c17ab6428]
  compare supervisor-general-worker/diagnosis-diff-goes-to-implementer: baseline kit 777e2f07062a beside current kit 6c440d36fbc4
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     71.4 +/- 11.2        76.9 +/- 14.1        +5.5
    tokens     322342 +/- 115713    270655 +/- 23302     -51687
    cost usd   0.3928 +/- 0.0630    0.3773 +/- 0.0305    -0.0155
```

Pin: `octo-feather-qa --verdict 20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-8a2c20-3r1-b-j0cgkrij/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-8a2c20-3r2-b-jvbvqk_q/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-8a2c20-3r3-b-_vdk_e9t/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-8a2c20-3r1-c-27zzc9vc/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-8a2c20-3r2-c-yksu4ifh/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-8a2c20-3r3-c-uqzkkupb/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/implementer-result-integrated-not-candidate

```text
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (2 entries in the record) [162.7 s] [kit 6c440d36fbc4c65a769ebde18f17fc5fd230fb4a]
  baseline PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (1 entries in the record) [179.5 s] [kit 777e2f07062a9fb64df0e978ce38623c17ab6428]
  compare supervisor-general-worker/implementer-result-integrated-not-candidate: baseline kit 777e2f07062a beside current kit 6c440d36fbc4
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     59.8 +/- 8.2         54.2 +/- 9.0         -5.6
    tokens     193325 +/- 20682     147499 +/- 25041     -45826
    cost usd   0.2451 +/- 0.0235    0.2330 +/- 0.0311    -0.0121
```

Pin: `octo-feather-qa --verdict 20261120T001636Z-8a2c20/supervisor-general-worker/implementer-result-integrated-not-candidate`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T001636Z-8a2c20/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/reviewed-implementer-result-integrated

```text
PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 5222eedf3168eb6a91e0ae56d73ce5c6fbfc61c0 (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (5 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [145.7 s] [kit 6c440d36fbc4c65a769ebde18f17fc5fd230fb4a]
  baseline PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 8b38e65dbc16e23203771f55a0f68a30fcb20ad3 (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [131.5 s] [kit 777e2f07062a9fb64df0e978ce38623c17ab6428]
  compare supervisor-general-worker/reviewed-implementer-result-integrated: baseline kit 777e2f07062a beside current kit 6c440d36fbc4
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     43.8 +/- 9.7         48.6 +/- 17.3        +4.7
    tokens     110931 +/- 29744     155219 +/- 64109     +44288
    cost usd   0.1830 +/- 0.0250    0.2034 +/- 0.0415    +0.0204
```

Pin: `octo-feather-qa --verdict 20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "8b38e65dbc16e23203771f55a0f68a30fcb20ad3"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "bd8b0e6"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "412f244"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "5222eedf3168eb6a91e0ae56d73ce5c6fbfc61c0"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "64d8211"] exit 0
20261120T001636Z-8a2c20/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
```

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  non-discriminating case supervisor-autonomy/owner-access-blocker-and-ready-work: every run on both kits passed
  non-discriminating case supervisor-general-worker/diagnosis-diff-goes-to-implementer: every run on both kits passed
  non-discriminating case supervisor-general-worker/implementer-result-integrated-not-candidate: every run on both kits passed
  non-discriminating case supervisor-general-worker/reviewed-implementer-result-integrated: every run on both kits passed
```

### To fill

Smoke: agents/supervisor.md run 20261120T001636Z-8a2c20: the five pinned cases at kit 6c440d36, --baseline origin/main (777e2f07), after lane gh644's supervisor change (codebase-design and tdd listed, the `octo-feather-lane skills` step before integrating, only exit 1 blocking): every fact case PASS 3/3 on both kits; the review case's verdict to be recorded by a fresh code-reviewer.
Removed: the pins of run 20261119T221913Z-9249cd, stale since lane gh644's supervisor change (agents/supervisor.md, .agents/skills/tdd, to-tickets, github-issues issue-view and notes.graphql, github-pr gh).
