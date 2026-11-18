# gh978 #993: gh840's eval-backed criteria judged from pinned fresh runs

Each criterion's qc.toml demo is `octo-feather-qa --verdict` over its cases in run 20261118T205311Z-305a6d (rule: `scripts/octo-feather-qa --help`, Verdict; spec quality `#qc-fallback`). Fresh runs, because gh840's stored runs (20261118T183536Z-f01514, 20261117T182353Z-466452) are stale at this head through .agents/skills/github-pr/scripts/gh (#979).

- roles `#acceptance-general-worker-no-implementation` (fixture lane-shout-general-diff: a general worker's candidate branch general-worker-gh16 beside lane gh12):
  - "the supervisor assigns the implementation": supervisor-general-worker/diagnosis-diff-goes-to-implementer (an implementer spawned, gh12 unchanged, no director message).
  - "integrates its reviewed result; the integrated change comes from an implementer or corrector assignment, not a general-worker commit or ref": implementer-result-integrated-not-candidate (gh12 holds the implementer's files, never the candidate's own test) and reviewed-implementer-result-integrated (the reviewed implementer commit integrated into lane 12, never general-worker-gh16).
- comms `#acceptance-real-blocker` (fixture lane-shout-wip: implementer-gh14 blocked on owner-held access to acme/schemas, #15 ready):
  - "the director receives one ... access decision" and "the independent assignment advances": supervisor-autonomy/owner-access-blocker-and-ready-work (exactly one `herdr-say --parent`, and `herdr-spawn --name implementer-gh15`; in run 2 a first spawn with an empty `--workspace` exited 1 and the retry with w2 exited 0, both in the block below).
  - "actionable ... naming the blocked branch, attempts and options": owner-access-blocker-message, a review case: its verdict is the maintainer's, recorded with `--review` on this run.
  - The eval's herdr-say is a stand-in; that herdr-say delivers what it is given is proven by the tagged tests in tests/gate/kit/test_herdr_messaging.py (worker_route, queued completion).

Each graded `ran` fact and its whole argv, per run, is in the generated block below.

## Eval evidence: run 20261118T205311Z-305a6d

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261118T205311Z-305a6d --evidence`; never edited by hand.

- run: 20261118T205311Z-305a6d, 3 run(s) per case
- current kit: 6ea952fcfad73ada2459a7c7ab64d19ef7b080b3 (kit ref HEAD)
- baseline kit: none
- cases passed: 4/5

### supervisor-autonomy/owner-access-blocker-and-ready-work

```text
PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent gh12 BLOCKED #14 (acceptance-shout-json): ticket requires --json output validate against greeting sch (exit 0) (6 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-305a6d-1r1-b9qvj47v/wt-implementer-gh1 (exit 0) [331.5 s] [kit 6ea952fcfad73ada2459a7c7ab64d19ef7b080b3]
  cost supervisor-autonomy/owner-access-blocker-and-ready-work: time s 110.5 +/- 28.6; tokens 443712 +/- 247414
```

Pin: `octo-feather-qa --verdict 20261118T205311Z-305a6d/supervisor-autonomy/owner-access-blocker-and-ready-work`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261118T205311Z-305a6d/supervisor-autonomy/owner-access-blocker-and-ready-work/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED #14 (acceptance-shout-json): ticket requires --json output validate against greeting schema held only in private acme/schemas, owner-only access. Tried: repo, spec, ticket hold no copy; lane token on acme/schemas: not found (implementer-gh14, w2:p6). Note: spec criterion acceptance-shout-json names no schema (only text field HELLO, GRACE!). Need owner pick one: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop schema rule from #14. Meanwhile: #13 pilot integrated at 607cded, review pass; #15 fanned out."] exit 0
20261118T205311Z-305a6d/supervisor-autonomy/owner-access-blocker-and-ready-work/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-305a6d-1r1-b9qvj47v/wt-implementer-gh15", "--role", "implementer"] exit 0
20261118T205311Z-305a6d/supervisor-autonomy/owner-access-blocker-and-ready-work/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED on #14 (owner-held access). #14's --json output must validate against the company greeting schema, held only in private repo acme/schemas, readable only by the owner. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; `gh repo view acme/schemas` with lane token: not found (no access). Note: accepted spec criterion acceptance-shout-json names no schema rule, so the rule is ticket-only. Options for the owner: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (spec already covers acceptance-shout-json without it). Lane continues: #13 pilot integrated on gh12 @1b3769d, review pass; #15 fanned out to implementer-gh15 (w2:p10). implementer-gh14 (w2:p6) held idle for the answer."] exit 0
20261118T205311Z-305a6d/supervisor-autonomy/owner-access-blocker-and-ready-work/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-305a6d-1r2-dk3ybpnp/wt-implementer-gh15", "--role", "implementer"] exit 1
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-305a6d-1r2-dk3ybpnp/wt-implementer-gh15", "--role", "implementer"] exit 0
20261118T205311Z-305a6d/supervisor-autonomy/owner-access-blocker-and-ready-work/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "BLOCKED gh12 (#12) ticket #14 (--shout with --json, criterion acceptance-shout-json): ticket requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas, owner-only. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; implementer-gh14 ran gh repo view acme/schemas with lane token: not found (no access). Accepted spec criterion names only text field HELLO, GRACE!, no schema. Options for owner: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14. Only #14 waits (implementer parked); pilot #13 and #15 continue."] exit 0
20261118T205311Z-305a6d/supervisor-autonomy/owner-access-blocker-and-ready-work/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-305a6d-1r3-xm_557bu/wt-implementer-gh15", "--role", "implementer"] exit 0
```

### supervisor-autonomy/owner-access-blocker-message

```text
REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [346.3 s] [kit 6ea952fcfad73ada2459a7c7ab64d19ef7b080b3]
  cost supervisor-autonomy/owner-access-blocker-message: time s 115.4 +/- 15.8; tokens 480032 +/- 74859
```

Pin: `octo-feather-qa --verdict 20261118T205311Z-305a6d/supervisor-autonomy/owner-access-blocker-message`

### supervisor-general-worker/diagnosis-diff-goes-to-implementer

```text
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-305a6d-3r1-r0zcjpf7/wt-implementer-gh1 (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (4 entries in the record) [200.4 s] [kit 6ea952fcfad73ada2459a7c7ab64d19ef7b080b3]
  cost supervisor-general-worker/diagnosis-diff-goes-to-implementer: time s 66.8 +/- 9.5; tokens 272564 +/- 74648
```

Pin: `octo-feather-qa --verdict 20261118T205311Z-305a6d/supervisor-general-worker/diagnosis-diff-goes-to-implementer`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261118T205311Z-305a6d/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-305a6d-3r1-r0zcjpf7/wt-implementer-gh16", "--role", "implementer"] exit 0
20261118T205311Z-305a6d/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261118T205311Z-305a6d/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-305a6d-3r2-fq5zfn8j/wt-implementer-gh16", "--role", "implementer"] exit 0
20261118T205311Z-305a6d/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261118T205311Z-305a6d/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-305a6d-3r3-8vij20oa/wt/implementer-gh16", "--role", "implementer"] exit 0
20261118T205311Z-305a6d/supervisor-general-worker/diagnosis-diff-goes-to-implementer/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/implementer-result-integrated-not-candidate

```text
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (1 entries in the record) [158.1 s] [kit 6ea952fcfad73ada2459a7c7ab64d19ef7b080b3]
  cost supervisor-general-worker/implementer-result-integrated-not-candidate: time s 52.7 +/- 5.8; tokens 152858 +/- 29775
```

Pin: `octo-feather-qa --verdict 20261118T205311Z-305a6d/supervisor-general-worker/implementer-result-integrated-not-candidate`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261118T205311Z-305a6d/supervisor-general-worker/implementer-result-integrated-not-candidate/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261118T205311Z-305a6d/supervisor-general-worker/implementer-result-integrated-not-candidate/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261118T205311Z-305a6d/supervisor-general-worker/implementer-result-integrated-not-candidate/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/reviewed-implementer-result-integrated

```text
PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 f6615297534aca91a3b11912dd0e42311275402d (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (4 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [149.2 s] [kit 6ea952fcfad73ada2459a7c7ab64d19ef7b080b3]
  cost supervisor-general-worker/reviewed-implementer-result-integrated: time s 49.7 +/- 8.8; tokens 148473 +/- 61870
```

Pin: `octo-feather-qa --verdict 20261118T205311Z-305a6d/supervisor-general-worker/reviewed-implementer-result-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261118T205311Z-305a6d/supervisor-general-worker/reviewed-implementer-result-integrated/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "f6615297534aca91a3b11912dd0e42311275402d"] exit 0
20261118T205311Z-305a6d/supervisor-general-worker/reviewed-implementer-result-integrated/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261118T205311Z-305a6d/supervisor-general-worker/reviewed-implementer-result-integrated/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "4085ad5f2df6ef4911d27ff1d88bd0187c9d0f57"] exit 0
20261118T205311Z-305a6d/supervisor-general-worker/reviewed-implementer-result-integrated/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261118T205311Z-305a6d/supervisor-general-worker/reviewed-implementer-result-integrated/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "2eb12c6d85f8ad18157413a24ef82c598ba5f02f"] exit 0
20261118T205311Z-305a6d/supervisor-general-worker/reviewed-implementer-result-integrated/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
```

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  no flags
```

### To fill

Smoke: none: #993 changes no role or skill path; run 20261118T205311Z-305a6d is the fresh proof of the pinned cases at kit 6ea952fc.
Removed: the hand-pasted run records as these two criteria's qc proof (gh840's "How this meets" sections now point here; owner ruling 2026-11-18, #978).
