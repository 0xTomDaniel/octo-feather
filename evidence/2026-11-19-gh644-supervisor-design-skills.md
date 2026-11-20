# gh644 / #1094: supervisor lists and loads codebase-design and tdd

Change: agents/supervisor.md `skills:` adds `codebase-design` and `tdd`; its Delivery load list gains one entry: before cutting tickets or writing a brief whose work places or moves a test (a test port, a review fix that moves one), both. No new prose block (owner ruling 2026-11-19 #644). Cases in evals/skill-triggers, every task worded as a real lane ticket or brief, none naming design, seam, interface or module boundary (#644: the implementer's design-worded cases passed 3/3 while real reach was 0 of 19):

- train: sup-design-port-test (brief for a test port), sup-tdd-port-test (cut tickets for a test port), sup-testplace-near-docs (near miss: brief for a docs-only ticket).
- held-out: sup-design-review-fix (fix brief: a test asserts on a private cli helper), sup-tdd-review-fix (fix brief: the only test sits in e2e and monkeypatches the read), sup-testplace-near-status (near miss: a status read of notes/handoffs.jsonl).
- Should cases graded skill_read of their named skill; near misses skill_not_read of both.

Smoke: agents/supervisor.md run 20261119T195921Z-3dd0f7 (sup-design-port-test), run 20261119T200020Z-6a2040 (the other five), run 20261119T200609Z-da0a96 (demo)
Removed: nothing; the change adds two skills and one load-step entry. Incident: #644 (supervisor offered neither skill though it writes the tickets and agrees the `Seam:` lines), owner ruling 2026-11-19.

Base: origin/main 1b21f8da. Current: 0c1d87f1 (a045ee45 role edit and cases, plus this file's skeleton). Runs serial in lane gh644's eval slot, runs=1 per case (pilot; pinned reruns later by the supervisor).

## Runs

Summary, runs=1 per case (single samples, no variance claim):

| case | split | head 0c1d87f1 | baseline 1b21f8da |
|---|---|---|---|
| sup-design-port-test | train, should | PASS, codebase-design at call 9 of 12 | FAIL, no load in 12 |
| sup-tdd-port-test | train, should | PASS, tdd at call 9 of 10 | FAIL, no load in 12 |
| sup-design-review-fix | held-out, should | PASS, codebase-design at call 4 of 4 | FAIL, no load in 12 |
| sup-tdd-review-fix | held-out, should | PASS, tdd at call 6 of 10 | FAIL, no load in 12 |
| sup-testplace-near-docs | train, near miss | PASS, neither in 9 | PASS, neither in 10 |
| sup-testplace-near-status | held-out, near miss | PASS, neither in 2 | PASS, neither in 2 |

Train 3/3, held-out 3/3 at head. Each should case fails at origin/main (skill not offered) and passes at head. Near misses non-discriminating, as expected: the baseline offers neither skill.

Demo, `scripts/octo-feather-qa --suite skill-triggers --case sup-design-port-test --case sup-tdd-port-test`, run 20261119T200609Z-da0a96: 2/2 PASS (codebase-design at call 13 of 17, tdd at 11 of 17).

Finding for pinned reruns: in the train port cases the load comes late (calls 9 to 13, the suite's max_tool_calls is 12); the supervisor reads the fixture and implement-spec first. A rerun stopping at the cap before the load reads as a FAIL. Supervisor ruling 2026-11-19: cases and suite budget unchanged; the pinned three-run rerun at merge time decides, and the budget changes only if late loads fail there.

This change staled the five pinned supervisor cases of comms#acceptance-real-blocker and roles#acceptance-general-worker-no-implementation (the supervisor's launch set changed). Rerun at lane head 6c440d36: run 20261120T001636Z-8a2c20, --runs 3 --baseline origin/main (777e2f07), every fact case PASS 3/3 on both kits, the review case awaiting a fresh code-reviewer; pinned in qc.toml, generated evidence in evidence/2026-11-18-gh978-eval-verdict.md.

The blocks below are `octo-feather-qa --analyze RUN_DIR --evidence` output, `### To fill` stubs dropped (filled above).

## Eval evidence: run 20261119T195921Z-3dd0f7

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261119T195921Z-3dd0f7 --evidence`; never edited by hand.

- run: 20261119T195921Z-3dd0f7, 1 run(s) per case
- current kit: 0c1d87f1c3ef5d2a94a729b7971a7e467c143932 (kit ref HEAD)
- baseline kit: 1b21f8da3f6e5fdc19928efcd54fe1694629517a (--baseline origin/main)
- cases passed: 1/1

### skill-triggers/sup-design-port-test

```text
PASS skill-triggers/sup-design-port-test: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_read codebase-design: loaded at tool call 9 of 12 (read /home/exedev/src/octo-feather-gh644-1094/.agents/skills/codebase-design/SKILL.md) [23.5 s] [kit 0c1d87f1c3ef5d2a94a729b7971a7e467c143932]
  baseline FAIL skill-triggers/sup-design-port-test: 0/1 runs passed (pass rate 0.00, stddev 0.00); run 1: skill_read codebase-design: no load of codebase-design/SKILL.md (its full content in a tool result) in 12 tool calls [27.1 s] [kit 1b21f8da3f6e5fdc19928efcd54fe1694629517a]
  compare skill-triggers/sup-design-port-test: baseline kit 1b21f8da3f6e beside current kit 0c1d87f1c3ef
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     27.1 +/- 0.0         23.5 +/- 0.0         -3.6
    tokens     53554 +/- 0          32105 +/- 0          -21449
    cost usd   0.1827 +/- 0.0000    0.1314 +/- 0.0000    -0.0513
```

Pin: `octo-feather-qa --verdict 20261119T195921Z-3dd0f7/skill-triggers/sup-design-port-test`

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  no flags
```

## Eval evidence: run 20261119T200020Z-6a2040

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261119T200020Z-6a2040 --evidence`; never edited by hand.

- run: 20261119T200020Z-6a2040, 1 run(s) per case
- current kit: 0c1d87f1c3ef5d2a94a729b7971a7e467c143932 (kit ref HEAD)
- baseline kit: 1b21f8da3f6e5fdc19928efcd54fe1694629517a (--baseline origin/main)
- cases passed: 5/5

### skill-triggers/sup-tdd-port-test

```text
PASS skill-triggers/sup-tdd-port-test: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_read tdd: loaded at tool call 9 of 10 (read /home/exedev/src/octo-feather-gh644-1094/.agents/skills/tdd/SKILL.md) [29.4 s] [kit 0c1d87f1c3ef5d2a94a729b7971a7e467c143932]
  baseline FAIL skill-triggers/sup-tdd-port-test: 0/1 runs passed (pass rate 0.00, stddev 0.00); run 1: skill_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 12 tool calls [65.7 s] [kit 1b21f8da3f6e5fdc19928efcd54fe1694629517a]
  compare skill-triggers/sup-tdd-port-test: baseline kit 1b21f8da3f6e beside current kit 0c1d87f1c3ef
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     65.7 +/- 0.0         29.4 +/- 0.0         -36.3
    tokens     129409 +/- 0         94305 +/- 0          -35104
    cost usd   0.2909 +/- 0.0000    0.2174 +/- 0.0000    -0.0735
```

Pin: `octo-feather-qa --verdict 20261119T200020Z-6a2040/skill-triggers/sup-tdd-port-test`

### skill-triggers/sup-design-review-fix

```text
PASS skill-triggers/sup-design-review-fix: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_read codebase-design: loaded at tool call 4 of 4 (read /home/exedev/src/octo-feather-gh644-1094/.agents/skills/codebase-design/SKILL.md) [10.3 s] [kit 0c1d87f1c3ef5d2a94a729b7971a7e467c143932]
  baseline FAIL skill-triggers/sup-design-review-fix: 0/1 runs passed (pass rate 0.00, stddev 0.00); run 1: skill_read codebase-design: no load of codebase-design/SKILL.md (its full content in a tool result) in 12 tool calls [14.6 s] [kit 1b21f8da3f6e5fdc19928efcd54fe1694629517a]
  compare skill-triggers/sup-design-review-fix: baseline kit 1b21f8da3f6e beside current kit 0c1d87f1c3ef
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     14.6 +/- 0.0         10.3 +/- 0.0         -4.3
    tokens     30625 +/- 0          14654 +/- 0          -15971
    cost usd   0.1248 +/- 0.0000    0.0979 +/- 0.0000    -0.0269
```

Pin: `octo-feather-qa --verdict 20261119T200020Z-6a2040/skill-triggers/sup-design-review-fix`

### skill-triggers/sup-tdd-review-fix

```text
PASS skill-triggers/sup-tdd-review-fix: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_read tdd: loaded at tool call 6 of 10 (read /home/exedev/src/octo-feather-gh644-1094/.agents/skills/tdd/SKILL.md) [20.5 s] [kit 0c1d87f1c3ef5d2a94a729b7971a7e467c143932]
  baseline FAIL skill-triggers/sup-tdd-review-fix: 0/1 runs passed (pass rate 0.00, stddev 0.00); run 1: skill_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 12 tool calls [35.8 s] [kit 1b21f8da3f6e5fdc19928efcd54fe1694629517a]
  compare skill-triggers/sup-tdd-review-fix: baseline kit 1b21f8da3f6e beside current kit 0c1d87f1c3ef
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     35.8 +/- 0.0         20.5 +/- 0.0         -15.3
    tokens     95115 +/- 0          49619 +/- 0          -45496
    cost usd   0.2136 +/- 0.0000    0.1466 +/- 0.0000    -0.0670
```

Pin: `octo-feather-qa --verdict 20261119T200020Z-6a2040/skill-triggers/sup-tdd-review-fix`

### skill-triggers/sup-testplace-near-docs

```text
PASS skill-triggers/sup-testplace-near-docs: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_not_read codebase-design: no load of codebase-design/SKILL.md (its full content in a tool result) in 9 tool calls; skill_not_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 9 tool calls [61.0 s] [kit 0c1d87f1c3ef5d2a94a729b7971a7e467c143932]
  baseline PASS skill-triggers/sup-testplace-near-docs: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_not_read codebase-design: no load of codebase-design/SKILL.md (its full content in a tool result) in 10 tool calls; skill_not_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 10 tool calls [68.8 s] [kit 1b21f8da3f6e5fdc19928efcd54fe1694629517a]
  compare skill-triggers/sup-testplace-near-docs: baseline kit 1b21f8da3f6e beside current kit 0c1d87f1c3ef
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     68.8 +/- 0.0         61.0 +/- 0.0         -7.8
    tokens     142941 +/- 0         127552 +/- 0         -15389
    cost usd   0.2850 +/- 0.0000    0.2899 +/- 0.0000    +0.0049
```

Pin: `octo-feather-qa --verdict 20261119T200020Z-6a2040/skill-triggers/sup-testplace-near-docs`

### skill-triggers/sup-testplace-near-status

```text
PASS skill-triggers/sup-testplace-near-status: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_not_read codebase-design: no load of codebase-design/SKILL.md (its full content in a tool result) in 2 tool calls; skill_not_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 2 tool calls [15.0 s] [kit 0c1d87f1c3ef5d2a94a729b7971a7e467c143932]
  baseline PASS skill-triggers/sup-testplace-near-status: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: skill_not_read codebase-design: no load of codebase-design/SKILL.md (its full content in a tool result) in 2 tool calls; skill_not_read tdd: no load of tdd/SKILL.md (its full content in a tool result) in 2 tool calls [18.7 s] [kit 1b21f8da3f6e5fdc19928efcd54fe1694629517a]
  compare skill-triggers/sup-testplace-near-status: baseline kit 1b21f8da3f6e beside current kit 0c1d87f1c3ef
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     18.7 +/- 0.0         15.0 +/- 0.0         -3.7
    tokens     42919 +/- 0          43860 +/- 0          +941
    cost usd   0.1100 +/- 0.0000    0.1111 +/- 0.0000    +0.0011
```

Pin: `octo-feather-qa --verdict 20261119T200020Z-6a2040/skill-triggers/sup-testplace-near-status`

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  non-discriminating case skill-triggers/sup-testplace-near-docs: every run on both kits passed
  non-discriminating case skill-triggers/sup-testplace-near-status: every run on both kits passed
```

## Eval evidence: run 20261119T200609Z-da0a96

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261119T200609Z-da0a96 --evidence`; never edited by hand.

- run: 20261119T200609Z-da0a96, 1 run(s) per case
- current kit: 0c1d87f1c3ef5d2a94a729b7971a7e467c143932 (kit ref HEAD)
- baseline kit: none
- cases passed: 2/2

### skill-triggers/sup-design-port-test

```text
PASS skill-triggers/sup-design-port-test: skill_read codebase-design: loaded at tool call 13 of 17 (read /home/exedev/src/octo-feather-gh644-1094/.agents/skills/codebase-design/SKILL.md) [stop: decided, 17 tool calls, 40.5 s] [kit 0c1d87f1c3ef5d2a94a729b7971a7e467c143932]
```

Pin: `octo-feather-qa --verdict 20261119T200609Z-da0a96/skill-triggers/sup-design-port-test`

### skill-triggers/sup-tdd-port-test

```text
PASS skill-triggers/sup-tdd-port-test: skill_read tdd: loaded at tool call 11 of 17 (read /home/exedev/src/octo-feather-gh644-1094/.agents/skills/tdd/SKILL.md) [stop: decided, 17 tool calls, 45.4 s] [kit 0c1d87f1c3ef5d2a94a729b7971a7e467c143932]
```

Pin: `octo-feather-qa --verdict 20261119T200609Z-da0a96/skill-triggers/sup-tdd-port-test`

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  no flags
```
