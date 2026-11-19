# gh978 #993: gh840's eval-backed criteria judged from pinned fresh runs

Each criterion's qc.toml demo is `octo-feather-qa --verdict` over its cases in run 20261119T021750Z-a6f960 at kit c001d41b (rule: `scripts/octo-feather-qa --help`, Verdict; spec quality `#qc-fallback`). Fresh runs, because gh840's stored runs (20261118T183536Z-f01514, 20261117T182353Z-466452) are stale at this head through .agents/skills/github-pr/scripts/gh (#979), and the first #993 run (20261118T205311Z-305a6d, kit 6ea952fc) through .agents/skills/herdr-comms (#1023, merged from main).

- roles `#acceptance-general-worker-no-implementation` (fixture lane-shout-general-diff: a general worker's candidate branch general-worker-gh16 beside lane gh12):
  - "the supervisor assigns the implementation": supervisor-general-worker/diagnosis-diff-goes-to-implementer (an implementer spawned, gh12 unchanged, no director message).
  - "integrates its reviewed result; the integrated change comes from an implementer or corrector assignment, not a general-worker commit or ref": implementer-result-integrated-not-candidate (gh12 holds the implementer's files, never the candidate's own test) and reviewed-implementer-result-integrated (the reviewed implementer result integrated into lane 12, never general-worker-gh16; runs 1 and 3 integrate it by its branch `implementer-gh16`, run 2 by its commit sha).
- comms `#acceptance-real-blocker` (fixture lane-shout-wip: implementer-gh14 blocked on owner-held access to acme/schemas, #15 ready):
  - "the director receives one ... access decision" and "the independent assignment advances": supervisor-autonomy/owner-access-blocker-and-ready-work (exactly one `herdr-say --parent`, and `herdr-spawn --name implementer-gh15`; in run 1 a first spawn with an empty `--workspace` exited 1 and the retry with w2 exited 0, both in the block below).
  - "actionable ... naming the blocked branch, attempts and options": owner-access-blocker-message, a review case: its verdict is the maintainer's, recorded with `--review` on this run.
  - The eval's herdr-say is a stand-in; that herdr-say delivers what it is given is proven by the tagged tests in tests/gate/kit/test_herdr_messaging.py (worker_route, queued completion).

Each graded `ran` fact and its whole argv, per run, is in the generated block below.

## Eval evidence: run 20261119T021750Z-a6f960

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261119T021750Z-a6f960 --evidence`; never edited by hand.

- run: 20261119T021750Z-a6f960, 3 run(s) per case
- current kit: c001d41b0cc4f0b50f347e1600ea07b88dbac591 (kit ref HEAD)
- baseline kit: none
- cases passed: 4/5

### supervisor-autonomy/owner-access-blocker-and-ready-work

```text
PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent gh12 BLOCKED #14 (--shout with --json): needs owner-held access. Ticket requires --json output to val (exit 0) (5 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace  --name implementer-gh15 --label worker-3 --cwd /tmp/qa-a6f960-1r1-4bwxlb8x/wt-implementer-gh15  (exit 1) [267.7 s] [kit c001d41b0cc4f0b50f347e1600ea07b88dbac591]
  cost supervisor-autonomy/owner-access-blocker-and-ready-work: time s 89.2 +/- 22.6; tokens 321103 +/- 122007
```

Pin: `octo-feather-qa --verdict 20261119T021750Z-a6f960/supervisor-autonomy/owner-access-blocker-and-ready-work`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T021750Z-a6f960/supervisor-autonomy/owner-access-blocker-and-ready-work/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED #14 (--shout with --json): needs owner-held access. Ticket requires --json output to validate against company greeting schema, kept only in private repo acme/schemas (owner-only read). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found. Spec criterion acceptance-shout-json itself names no schema. Options: (1) owner grants lane token read on acme/schemas, (2) owner pastes schema into #14, (3) owner drops schema rule from #14. Lane continues meanwhile: #13 pilot integrated (9bf3af2, review pass), #15 fanning out to a fresh implementer. implementer-gh14 (w2:p6) held idle for the answer."] exit 0
20261119T021750Z-a6f960/supervisor-autonomy/owner-access-blocker-and-ready-work/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-a6f960-1r1-4bwxlb8x/wt-implementer-gh15", "--role", "implementer"] exit 1
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-a6f960-1r1-4bwxlb8x/wt-implementer-gh15", "--role", "implementer"] exit 0
20261119T021750Z-a6f960/supervisor-autonomy/owner-access-blocker-and-ready-work/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "BLOCKED lane gh12 (#12), ticket #14 (--shout with --json, criterion acceptance-shout-json). Need: owner-held access. #14 requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas, readable only by the owner. Tried (implementer-gh14): repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: the spec criterion itself names no schema (text field HELLO, GRACE!); the schema rule is ticket-only. Options for owner: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14. Only #14 stops; pilot #13 integrated (gh12 a0c6ae9, review pass), #15 fanning out now. implementer-gh14 (w2:p6) held idle for the answer."] exit 0
20261119T021750Z-a6f960/supervisor-autonomy/owner-access-blocker-and-ready-work/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-a6f960-1r2-l_gadh3j/wt-implementer-gh15", "--role", "implementer"] exit 0
20261119T021750Z-a6f960/supervisor-autonomy/owner-access-blocker-and-ready-work/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED (owner-held access): #14 (--shout --json) must validate --json output against the company greeting schema, kept only in private repo acme/schemas. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Need one owner call: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, or (c) drop the schema rule from #14. Meanwhile: #13 pilot integrated (a1a1406, review pass), #15 fanning out to a fresh implementer; implementer-gh14 holds #14 waiting."] exit 0
20261119T021750Z-a6f960/supervisor-autonomy/owner-access-blocker-and-ready-work/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-2", "--cwd", "/tmp/qa-a6f960-1r3-u5whnmde/wt-implementer-gh15", "--role", "implementer"] exit 0
```

### supervisor-autonomy/owner-access-blocker-message

```text
REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [272.1 s] [kit c001d41b0cc4f0b50f347e1600ea07b88dbac591]
  cost supervisor-autonomy/owner-access-blocker-message: time s 90.7 +/- 7.2; tokens 366573 +/- 73235
```

Pin: `octo-feather-qa --verdict 20261119T021750Z-a6f960/supervisor-autonomy/owner-access-blocker-message`

### supervisor-general-worker/diagnosis-diff-goes-to-implementer

```text
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-a6f960-3r1-05_bnb8t/wt-implementer-gh1 (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (4 entries in the record) [160.6 s] [kit c001d41b0cc4f0b50f347e1600ea07b88dbac591]
  cost supervisor-general-worker/diagnosis-diff-goes-to-implementer: time s 53.5 +/- 4.6; tokens 206868 +/- 30282
```

Pin: `octo-feather-qa --verdict 20261119T021750Z-a6f960/supervisor-general-worker/diagnosis-diff-goes-to-implementer`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T021750Z-a6f960/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-a6f960-3r1-05_bnb8t/wt-implementer-gh16", "--role", "implementer"] exit 0
20261119T021750Z-a6f960/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T021750Z-a6f960/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-a6f960-3r2-01roxt2b/wt-implementer-gh16", "--role", "implementer"] exit 0
20261119T021750Z-a6f960/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T021750Z-a6f960/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-a6f960-3r3-s6l62ma4/wt-implementer-gh16", "--role", "implementer"] exit 0
20261119T021750Z-a6f960/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/implementer-result-integrated-not-candidate

```text
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (1 entries in the record) [135.7 s] [kit c001d41b0cc4f0b50f347e1600ea07b88dbac591]
  cost supervisor-general-worker/implementer-result-integrated-not-candidate: time s 45.2 +/- 4.6; tokens 127634 +/- 13874
```

Pin: `octo-feather-qa --verdict 20261119T021750Z-a6f960/supervisor-general-worker/implementer-result-integrated-not-candidate`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T021750Z-a6f960/supervisor-general-worker/implementer-result-integrated-not-candidate/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T021750Z-a6f960/supervisor-general-worker/implementer-result-integrated-not-candidate/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261119T021750Z-a6f960/supervisor-general-worker/implementer-result-integrated-not-candidate/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/reviewed-implementer-result-integrated

```text
PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 implementer-gh16 (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [124.3 s] [kit c001d41b0cc4f0b50f347e1600ea07b88dbac591]
  cost supervisor-general-worker/reviewed-implementer-result-integrated: time s 41.4 +/- 6.0; tokens 144726 +/- 6405
```

Pin: `octo-feather-qa --verdict 20261119T021750Z-a6f960/supervisor-general-worker/reviewed-implementer-result-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261119T021750Z-a6f960/supervisor-general-worker/reviewed-implementer-result-integrated/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261119T021750Z-a6f960/supervisor-general-worker/reviewed-implementer-result-integrated/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261119T021750Z-a6f960/supervisor-general-worker/reviewed-implementer-result-integrated/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "442afbebcdec0cd081198f11d834921369f96612"] exit 0
20261119T021750Z-a6f960/supervisor-general-worker/reviewed-implementer-result-integrated/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261119T021750Z-a6f960/supervisor-general-worker/reviewed-implementer-result-integrated/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261119T021750Z-a6f960/supervisor-general-worker/reviewed-implementer-result-integrated/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
```

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  no flags
```

### To fill

Smoke: none: #993 changes no role or skill path; run 20261119T021750Z-a6f960 is the fresh proof of the pinned cases at kit c001d41b.
Removed: the hand-pasted run records as these two criteria's qc proof (gh840's "How this meets" sections point here; owner ruling 2026-11-18, #978), and the stale pins of run 20261118T205311Z-305a6d.
