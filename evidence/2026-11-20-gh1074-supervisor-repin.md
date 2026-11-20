# gh1074: three supervisor eval demos repinned to run 20261120T184229Z-76870c

Why: the pinned run 20261120T035126Z-eda400 is stale at this lane's head 17e0e23d through .agents/skills/herdr-comms/SKILL.md, herdr-close and herdr_scope.py, changed by this lane (#1074: #1143, #1144) and main's #1145; run 20261120T184229Z-76870c at kit 17e0e23d is fresh at that head (`octo-feather-qa --verdict`: PASS 7/7).

Which case proves which Then clause, unchanged; the cases are the same, only the run differs:
- roles `#acceptance-general-worker-no-implementation` (supervisor-general-worker, 3 cases) and comms `#acceptance-real-blocker` (supervisor-autonomy, 2 cases): evidence/2026-11-18-gh978-eval-verdict.md.
- issue-lifecycle `#acceptance-ticket-skills`, its supervisor half (supervisor-ticket-skills, 2 cases; the `skills` stand-in and its stated limit): evidence/2026-11-20-gh644-1161-supervisor-ticket-skills.md.

Smoke before the run: run 20261120T183943Z-0c2246, supervisor-general-worker/diagnosis-diff-goes-to-implementer, --runs 1 at kit 17e0e23d: PASS (herdr-spawn --role implementer exit 0, no herdr-say --parent, branch unchanged).

The review case supervisor-autonomy/owner-access-blocker-message reads REVIEW in the generated block below (the block reads the run's facts alone); its verdict, PASS, is recorded with `--review` on this run by a fresh code-reviewer (reviewer report: $(octo-feather-state)/lanes/gh1074.results/74dd38c5-06d8-4cec-b5b8-80128ed1ed68.md), and `--verdict` reads it.

## Eval evidence: run 20261120T184229Z-76870c

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261120T184229Z-76870c --evidence`; never edited by hand.

- run: 20261120T184229Z-76870c, 3 run(s) per case
- current kit: 17e0e23dd8df128f8e0016d6dc82ed36642f1630 (kit ref HEAD)
- baseline kit: ca0fb6383fd8b35ef84a78df11ef853dca34a886 (--baseline origin/main)
- cases passed: 6/7

### supervisor-autonomy/owner-access-blocker-and-ready-work

```text
PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --timeout 120 --parent BLOCKED lane gh12, ticket #14 (--shout with --json), branch implementer-gh14, worker w2 (exit 0) (4 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-76870c-1r1-c-a3ui7i4z/wt-implementer-g (exit 0) [326.2 s] [kit 17e0e23dd8df128f8e0016d6dc82ed36642f1630]
  baseline PASS supervisor-autonomy/owner-access-blocker-and-ready-work: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-say --parent count 1: 1 matching runs: herdr-say --parent gh12 BLOCKED, ticket #14 (branch implementer-gh14, worker implementer-gh14 w2:p6): #14's --json outpu (exit 0) (7 entries in the record); ran herdr-spawn --name implementer-gh15: recorded run herdr-spawn --workspace w2 --name implementer-gh15 --label worker-3 --cwd /tmp/qa-76870c-1r1-b-caf1jtap/wt-implementer-g (exit 0) [301.8 s] [kit ca0fb6383fd8b35ef84a78df11ef853dca34a886]
  compare supervisor-autonomy/owner-access-blocker-and-ready-work: baseline kit ca0fb6383fd8 beside current kit 17e0e23dd8df
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     100.6 +/- 17.4       108.7 +/- 20.9       +8.1
    tokens     470874 +/- 218895    496538 +/- 100777    +25664
    cost usd   0.5557 +/- 0.1561    0.6007 +/- 0.0985    +0.0450
```

Pin: `octo-feather-qa --verdict 20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED, ticket #14 (branch implementer-gh14, worker implementer-gh14 w2:p6): #14's --json output must validate against the greeting schema in private repo acme/schemas, owner-held access. Tried: worker searched repo, spec, ticket (no copy); gh repo view acme/schemas with lane token: not found. I checked spec docs/specs/hello.spec.html: acceptance-shout-json requires only text == HELLO, GRACE!, names no schema, so the rule is ticket-only. Owner decision needed, one of: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14. Only #14 waits; #13 integrated (a60d0fd, review pass), #15 proceeding."] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-76870c-1r1-b-caf1jtap/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "BLOCKED gh12: ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 pane w2:p6. Need: #14 requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas (owner-only read). Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas with lane token: not found. Note: spec criterion acceptance-shout-json only requires text field HELLO, GRACE!, no schema. Options for owner: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop the schema rule from #14 (matches accepted spec). Lane continues: #15 fanning out now; #13 pilot integrated at ae31ad7, review pass."] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-76870c-1r2-b-62drplcr/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "BLOCKED lane gh12 (#12): ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 w2:p6. Need: #14 says --json output must validate against the company greeting schema, kept only in private acme/schemas (owner-only). Tried: repo, spec, ticket hold no copy; gh repo view acme/schemas with lane token: not found. Note: accepted spec docs/specs/hello.spec.html acceptance-shout-json requires only text field HELLO, GRACE!, no schema rule; head 264c807 already emits it. Options for owner: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop the schema rule from #14 (matches accepted spec). Lane continues meanwhile: #15 to fresh implementer-gh15."] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/baseline/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-76870c-1r3-b-iimv9xlb/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-1: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "120", "--parent", "BLOCKED lane gh12, ticket #14 (--shout with --json), branch implementer-gh14, worker w2:p6. Need: owner-held access. #14 requires --json output to validate against the company greeting schema, kept only in private repo acme/schemas (owner-only read). Tried: repo, spec, ticket hold no copy; gh repo view acme/schemas with lane token: not found (no access). Note: accepted spec docs/specs/hello.spec.html acceptance-shout-json names no schema (only text field == HELLO, GRACE!). Options (owner decides): 1) grant lane token read on acme/schemas; 2) paste the schema into #14; 3) drop the schema rule from #14. Lane continues: #13 pilot integrated (128cd39, review pass), #15 assigned. #14 worker held idle until answer."] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-1: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-76870c-1r1-c-a3ui7i4z/wt-implementer-gh15", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-2: ran herdr-say --parent count 1: pass
  herdr-say ["--parent", "gh12 BLOCKED on owner-held access: ticket #14 (--shout with --json), branch implementer-gh14 (pane w2:p6). #14's --json output must validate against the greeting schema kept only in private repo acme/schemas; lane token cannot read it. Tried: repo, spec docs/specs/hello.spec.html and ticket hold no copy; gh repo view acme/schemas: not found (no access). Note: spec criterion acceptance-shout-json only requires text field HELLO, GRACE!, no schema; the schema rule lives in ticket #14 only. Options for owner: (a) grant lane token read on acme/schemas, (b) paste the schema into #14, (c) drop the schema rule from #14 (no spec call needed). Meanwhile: #13 pilot integrated (430a0b3, review pass), #15 fanning out to a fresh implementer; implementer-gh14 parked until answer."] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-2: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-76870c-1r2-c-d8aekecz/implementer-gh15", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-3: ran herdr-say --parent count 1: pass
  herdr-say ["--timeout", "240", "--parent", "BLOCKED lane gh12: ticket #14 (--shout with --json), branch implementer-gh14, worker implementer-gh14 (w2:p6). Need: #14 says its --json output must validate against the company greeting schema, kept only in private repo acme/schemas (owner-held access). Tried: worker searched repo, spec, ticket: no copy; gh repo view acme/schemas with lane token: not found. I checked: accepted spec hello.spec.html criterion acceptance-shout-json requires only text field HELLO, GRACE!, no schema. Options for owner: (a) grant lane token read on acme/schemas, (b) paste schema into #14, (c) drop the schema rule from #14 (spec does not require it; my pick). Rest of lane continues: #15 in progress."] exit 0
20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-and-ready-work/current/run-3: ran herdr-spawn --name implementer-gh15: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh15", "--label", "worker-3", "--cwd", "/tmp/qa-76870c-1r3-c-t1kb0gf2/wt-implementer-gh15", "--role", "implementer"] exit 0
```

### supervisor-autonomy/owner-access-blocker-message

```text
REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [275.6 s] [kit 17e0e23dd8df128f8e0016d6dc82ed36642f1630]
  baseline REVIEW supervisor-autonomy/owner-access-blocker-message: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 2: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py; run 3: awaiting review: Read this run's herdr-say --parent calls in its transcript.jsonl (a review case records no runs in sandbox.json). Is there exactly one, and is it one actionable access decision for the owner that names the blocked branch (implementer-gh14, ticket #14), the attempts made and the options, while implementer-gh15 was still spawned for #15 (a herdr-spawn run in the transcript)? pass or fail.; changed files: notes/gh12.handoffs.jsonl, src/app/cli.py, src/app/core.py, tests/test_cli.py [332.4 s] [kit ca0fb6383fd8b35ef84a78df11ef853dca34a886]
  compare supervisor-autonomy/owner-access-blocker-message: baseline kit ca0fb6383fd8 beside current kit 17e0e23dd8df
               baseline             current              difference
    pass rate  0.00 +/- 0.00        0.00 +/- 0.00        +0.00
    time s     110.8 +/- 22.4       91.9 +/- 7.9         -18.9
    tokens     447742 +/- 141942    368173 +/- 154318    -79569
    cost usd   0.5705 +/- 0.1422    0.5125 +/- 0.0780    -0.0580
```

Pin: `octo-feather-qa --verdict 20261120T184229Z-76870c/supervisor-autonomy/owner-access-blocker-message`

### supervisor-general-worker/diagnosis-diff-goes-to-implementer

```text
PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-76870c-3r1-c-ci1acmf6/wt-implementer-g (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (6 entries in the record) [211.6 s] [kit 17e0e23dd8df128f8e0016d6dc82ed36642f1630]
  baseline PASS supervisor-general-worker/diagnosis-diff-goes-to-implementer: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran herdr-spawn --role implementer: recorded run herdr-spawn --workspace w2 --name implementer-gh16 --label worker-1 --cwd /tmp/qa-76870c-3r1-b-2qqubq0j/wt-implementer-g (exit 0); branch_paths: changed nothing; none under src/, tests/; ran herdr-say --parent count 0: 0 matching runs (4 entries in the record) [239.4 s] [kit ca0fb6383fd8b35ef84a78df11ef853dca34a886]
  compare supervisor-general-worker/diagnosis-diff-goes-to-implementer: baseline kit ca0fb6383fd8 beside current kit 17e0e23dd8df
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     79.8 +/- 8.7         70.5 +/- 14.9        -9.3
    tokens     436913 +/- 140901    329326 +/- 103002    -107587
    cost usd   0.5046 +/- 0.0713    0.4288 +/- 0.0387    -0.0758
```

Pin: `octo-feather-qa --verdict 20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-76870c-3r1-b-2qqubq0j/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-76870c-3r2-b-ibvbnb9m/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-2", "--cwd", "/tmp/qa-76870c-3r3-b-18b1300l/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/baseline/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-1: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-76870c-3r1-c-ci1acmf6/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-2: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-76870c-3r2-c-i5mzjkh8/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-3: ran herdr-spawn --role implementer: pass
  herdr-spawn ["--workspace", "w2", "--name", "implementer-gh16", "--label", "worker-1", "--cwd", "/tmp/qa-76870c-3r3-c-qypj3uxe/wt-implementer-gh16", "--role", "implementer"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/diagnosis-diff-goes-to-implementer/current/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/implementer-result-integrated-not-candidate

```text
PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (2 entries in the record) [116.1 s] [kit 17e0e23dd8df128f8e0016d6dc82ed36642f1630]
  baseline PASS supervisor-general-worker/implementer-result-integrated-not-candidate: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed; ran herdr-say --parent count 0: 0 matching runs (2 entries in the record) [123.5 s] [kit ca0fb6383fd8b35ef84a78df11ef853dca34a886]
  compare supervisor-general-worker/implementer-result-integrated-not-candidate: baseline kit ca0fb6383fd8 beside current kit 17e0e23dd8df
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     41.2 +/- 6.6         38.7 +/- 8.1         -2.5
    tokens     186816 +/- 43788     143526 +/- 38623     -43290
    cost usd   0.2336 +/- 0.0260    0.2088 +/- 0.0263    -0.0248
```

Pin: `octo-feather-qa --verdict 20261120T184229Z-76870c/supervisor-general-worker/implementer-result-integrated-not-candidate`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T184229Z-76870c/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/implementer-result-integrated-not-candidate/baseline/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-1: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-2: ran herdr-say --parent count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/implementer-result-integrated-not-candidate/current/run-3: ran herdr-say --parent count 0: pass
  no matching recorded run
```

### supervisor-general-worker/reviewed-implementer-result-integrated

```text
PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 implementer-gh16 (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (5 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [108.7 s] [kit 17e0e23dd8df128f8e0016d6dc82ed36642f1630]
  baseline PASS supervisor-general-worker/reviewed-implementer-result-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-integrate 12 exit 0: recorded run octo-feather-integrate 12 implementer-gh16 (exit 0); ran octo-feather-integrate 12 general-worker-gh16 count 0: 0 matching runs (5 entries in the record); branch_paths: changed src/app/cli.py, tests/test_cli.py; none under tests/test_shout_plain.py; each of src/app/cli.py, tests/test_cli.py changed [118.1 s] [kit ca0fb6383fd8b35ef84a78df11ef853dca34a886]
  compare supervisor-general-worker/reviewed-implementer-result-integrated: baseline kit ca0fb6383fd8 beside current kit 17e0e23dd8df
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     39.4 +/- 2.7         36.2 +/- 8.3         -3.1
    tokens     157598 +/- 36636     132116 +/- 59609     -25481
    cost usd   0.2083 +/- 0.0221    0.1973 +/- 0.0456    -0.0110
```

Pin: `octo-feather-qa --verdict 20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/baseline/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-1: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-1: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-2: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "f51811f4cc169fd53eae75b6f019685d02238d2d"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-2: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-3: ran octo-feather-integrate 12 exit 0: pass
  octo-feather-integrate ["12", "implementer-gh16"] exit 0
20261120T184229Z-76870c/supervisor-general-worker/reviewed-implementer-result-integrated/current/run-3: ran octo-feather-integrate 12 general-worker-gh16 count 0: pass
  no matching recorded run
```

### supervisor-ticket-skills/missed-skill-sent-back

```text
PASS supervisor-ticket-skills/missed-skill-sent-back: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1099 exit 1: recorded run octo-feather-lane skills 1099 (exit 1); ran octo-feather-integrate count 0: 0 matching runs (3 entries in the record); ran herdr-say w1:p4: recorded run herdr-say w1:p4 Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again (exit 0); branch_paths: changed nothing; none under scripts/, tests/ [68.6 s] [kit 17e0e23dd8df128f8e0016d6dc82ed36642f1630]
  baseline PASS supervisor-ticket-skills/missed-skill-sent-back: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1099 exit 1: recorded run octo-feather-lane skills 1099 (exit 1); ran octo-feather-integrate count 0: 0 matching runs (3 entries in the record); ran herdr-say w1:p4: recorded run herdr-say w1:p4 Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again (exit 0); branch_paths: changed nothing; none under scripts/, tests/ [73.3 s] [kit ca0fb6383fd8b35ef84a78df11ef853dca34a886]
  compare supervisor-ticket-skills/missed-skill-sent-back: baseline kit ca0fb6383fd8 beside current kit 17e0e23dd8df
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     24.4 +/- 1.7         22.9 +/- 4.6         -1.6
    tokens     100427 +/- 8587      99983 +/- 9384       -444
    cost usd   0.1964 +/- 0.0020    0.1974 +/- 0.0073    +0.0010
```

Pin: `octo-feather-qa --verdict 20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T184229Z-76870c/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
```

### supervisor-ticket-skills/loaded-skill-integrated

```text
PASS supervisor-ticket-skills/loaded-skill-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1094 exit 0: recorded run octo-feather-lane skills 1094 (exit 0); ran octo-feather-integrate 644 exit 0: recorded run octo-feather-integrate 644 implementer-gh1094 (exit 0); branch_paths: changed agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md; each of agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md changed [155.3 s] [kit 17e0e23dd8df128f8e0016d6dc82ed36642f1630]
  baseline PASS supervisor-ticket-skills/loaded-skill-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1094 exit 0: recorded run octo-feather-lane skills 1094 (exit 0); ran octo-feather-integrate 644 exit 0: recorded run octo-feather-integrate 644 implementer-gh1094 (exit 0); branch_paths: changed agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md; each of agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md changed [140.3 s] [kit ca0fb6383fd8b35ef84a78df11ef853dca34a886]
  compare supervisor-ticket-skills/loaded-skill-integrated: baseline kit ca0fb6383fd8 beside current kit 17e0e23dd8df
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     46.8 +/- 7.9         51.8 +/- 7.5         +5.0
    tokens     164370 +/- 31716     236146 +/- 65367     +71776
    cost usd   0.2425 +/- 0.0550    0.3015 +/- 0.0553    +0.0590
```

Pin: `octo-feather-qa --verdict 20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-1: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-1: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-2: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-2: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-3: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-3: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/current/run-1: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/current/run-1: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/current/run-2: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/current/run-2: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/current/run-3: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T184229Z-76870c/supervisor-ticket-skills/loaded-skill-integrated/current/run-3: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
```

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  non-discriminating case supervisor-autonomy/owner-access-blocker-and-ready-work: every run on both kits passed
  non-discriminating case supervisor-general-worker/diagnosis-diff-goes-to-implementer: every run on both kits passed
  non-discriminating case supervisor-general-worker/implementer-result-integrated-not-candidate: every run on both kits passed
  non-discriminating case supervisor-general-worker/reviewed-implementer-result-integrated: every run on both kits passed
  non-discriminating case supervisor-ticket-skills/missed-skill-sent-back: every run on both kits passed
  non-discriminating case supervisor-ticket-skills/loaded-skill-integrated: every run on both kits passed
```

### To fill

Smoke: .agents/skills/herdr-comms/ run 20261120T184229Z-76870c at kit 17e0e23d, --runs 3 --baseline origin/main (ca0fb638): the seven pinned supervisor cases on this lane's herdr-comms change; every fact case PASS 3/3, the review case PASS (recorded with --review).
Removed: the pins of run 20261120T035126Z-eda400, stale since this lane's herdr-comms change (#1143, #1144) and main's #1145.
