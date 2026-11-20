# gh644 / #1161: the supervisor sends a worker back on a missed named skill before integrating

Criterion: issue-lifecycle `#acceptance-ticket-skills`, its supervisor half (the command half: tests/gate/kit/test_lane_skills.py). Role line: agents/supervisor.md, Delivery, "When you consume a worker's ticket result". Suite: evals/supervisor-ticket-skills (its description holds the cases' design and stated limits); fixtures lane-skills-main, lane-skills-1099, lane-skills-1094.

## The stand-in for `octo-feather-lane skills` (stated limit)

The qa sandbox scrubs HERDR_PANE_ID and starts its state dir's `lanes/` empty, and a case can set neither, so a real `skills` call inside it can only exit 2 (could not check). The cases put a stand-in for `octo-feather-lane` first on PATH, behind the run shim (so the `ran` facts record the role's own call), answering only `skills <ticket>` with the stdout and exit of the real command at kit 4bbca962. Supervisor ruling on #1161 (2026-11-20): a recorded real answer is right for a role eval; the command half is proved by its own tests; no scripts/ change. A change to `skills`' output form needs these answers re-recorded. Any other `octo-feather-lane` call (another subcommand, `--help`) gets the stand-in's refusal, exit 1; runs did call `--help` and went on.

How the answers were recorded (re-record the same way): a scratch lane gh644 built as tests/gate/kit/lane_skills.py builds it, the testkit gh replaying tests/gate/kit/testkit/recordings/lane-skills.json (real #1094 and #1099 `issue-view --notes` answers):

```
R=/tmp/lane-skills-rec; mkdir -p $R/gh $R/bin $R/pi
cp -r tests/fixtures/lane-skills/sessions $R/pi/sessions
cp tests/gate/kit/testkit/recordings/lane-skills.json $R/gh/tape.json; : > $R/gh/log
ln -s $PWD/tests/gate/kit/testkit/gh.py $R/bin/gh
export XDG_STATE_HOME=$R/state PI_CODING_AGENT_DIR=$R/pi FAKE_GH=$R/gh GH_TOKEN=x HERDR_PANE_ID=w1:p2 PATH=$R/bin:$PATH; unset HERDR_SESSION
L=$(scripts/octo-feather-state)/lanes; mkdir -p $L; printf 'supervisor = "w1:p2"\nissue = "gh644"\n' > $L/gh644.toml
# gh644.handoffs.jsonl: one spawn line each, session 4fd43c0c-7119-4cb4-866f-e114e16ecdb4:
#   implementer-gh1094 pane w1:p3 ticket 1094; implementer-gh1099 pane w1:p4 ticket 1099
scripts/octo-feather-lane skills 1099   # exit 1 (tdd, codebase-design not loaded; the send-back line names herdr-say w1:p4)
scripts/octo-feather-lane skills 1094   # exit 0 (eval-cases loaded)
```

The stdout of each, unmodified, is the stand-in's `stdout` in evals/supervisor-ticket-skills/cases.json.

## Runs

- Smoke: run 20261120T022652Z-ddc8bc at cf20effa, missed-skill-sent-back --runs 1: PASS (6 tool calls).
- First proof: run 20261120T022747Z-4968d7 at cf20effa, --runs 3 --baseline origin/main: missed-skill-sent-back 3/3 (baseline 1/3); loaded-skill-integrated 1/3. Run 3 sent back a fixture branch that really fell short of #1094's acceptance list (fixture gap: fixed at b4ff5107, the branch now carries all #1094 asks); run 1 passed the ticket (1094) to octo-feather-integrate instead of the lane's parent (644), exit 66 (fixed: both tasks state `just integrate 644 <worker branch>`).
- Smoke of the changed case: run 20261120T024211Z-ecd5c1 at b4ff5107, loaded-skill-integrated --runs 1: PASS.
- Proof: run 20261120T024345Z-2fd725 at b4ff5107, below. Both cases PASS 3/3; missed-skill-sent-back FAILs on main (1/3: in the one passing baseline run the role ran `skills` though main's role file lacks the line, the ticket body #1099 describing the command). On loaded-skill-integrated the integrate fact passes on both kits, as it should: a near-miss integrates either way; its `skills 1094` fact is what main lacks.

## Eval evidence: run 20261120T024345Z-2fd725

Generated from the stored run alone by `octo-feather-qa --analyze <qa dir>/20261120T024345Z-2fd725 --evidence`; never edited by hand.

- run: 20261120T024345Z-2fd725, 3 run(s) per case
- current kit: b4ff5107005bc053ff844175de688b85b3380bda (kit ref HEAD)
- baseline kit: 7933ff0cce5224f590bd2b503bb32eb42f151951 (--baseline origin/main)
- cases passed: 2/2

### supervisor-ticket-skills/missed-skill-sent-back

```text
PASS supervisor-ticket-skills/missed-skill-sent-back: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1099 exit 1: recorded run octo-feather-lane skills 1099 (exit 1); ran octo-feather-integrate count 0: 0 matching runs (3 entries in the record); ran herdr-say w1:p4: recorded run herdr-say w1:p4 Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again (exit 0); branch_paths: changed nothing; none under scripts/, tests/ [118.3 s] [kit b4ff5107005bc053ff844175de688b85b3380bda]
  baseline FAIL supervisor-ticket-skills/missed-skill-sent-back: 1/3 runs passed (pass rate 0.33, stddev 0.58); run 1: ran octo-feather-lane skills 1099 exit 1: no run of octo-feather-lane with these arguments in the sandbox's record (4 entries; no run of octo-feather-lane recorded); ran octo-feather-integrate count 0: 3 matching runs: octo-feather-integrate --help (exit 64); octo-feather-integrate 644 implementer-gh1099 (exit 3); octo-feather-integrate 644 implementer-gh1099 (exit 0); ran herdr-say w1:p4: no run of herdr-say with these arguments in the sandbox's record (4 entries; no run of herdr-say recorded); branch_paths: changed scripts/lane_tickets.py, tests/test_lane_tickets.py (untouched: scripts/, tests/); run 2: ran octo-feather-lane skills 1099 exit 1: no run of octo-feather-lane with these arguments in the sandbox's record (4 entries; runs of octo-feather-lane: octo-feather-lane --help (exit 1)); ran octo-feather-integrate count 0: 2 matching runs: octo-feather-integrate 644 implementer-gh1099 (exit 3); octo-feather-integrate 644 implementer-gh1099 (exit 0); ran herdr-say w1:p4: no run of herdr-say with these arguments in the sandbox's record (4 entries; no run of herdr-say recorded); branch_paths: changed scripts/lane_tickets.py, tests/test_lane_tickets.py (untouched: scripts/, tests/) [228.8 s] [kit 7933ff0cce5224f590bd2b503bb32eb42f151951]
  compare supervisor-ticket-skills/missed-skill-sent-back: baseline kit 7933ff0cce52 beside current kit b4ff5107005b
               baseline             current              difference
    pass rate  0.33 +/- 0.58        1.00 +/- 0.00        +0.67
    time s     76.3 +/- 19.3        39.4 +/- 3.4         -36.8
    tokens     182255 +/- 8112      105243 +/- 418       -77012
    cost usd   0.2719 +/- 0.0218    0.1997 +/- 0.0025    -0.0722
```

Pin: `octo-feather-qa --verdict 20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran octo-feather-lane skills 1099 exit 1: fail
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran octo-feather-integrate count 0: fail
  octo-feather-integrate ["--help"] exit 64
  octo-feather-integrate ["644", "implementer-gh1099"] exit 3
  octo-feather-integrate ["644", "implementer-gh1099"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-1: ran herdr-say w1:p4: fail
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran octo-feather-lane skills 1099 exit 1: fail
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran octo-feather-integrate count 0: fail
  octo-feather-integrate ["644", "implementer-gh1099"] exit 3
  octo-feather-integrate ["644", "implementer-gh1099"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-2: ran herdr-say w1:p4: fail
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/baseline/run-3: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again. octo-feather-lane skills 1099 found both not loaded in your session (skill_miss send-back); branch implementer-gh1099 (a3a1808) not integrated until it passes."] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-1: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-2: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran octo-feather-lane skills 1099 exit 1: pass
  octo-feather-lane ["skills", "1099"] exit 1
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran octo-feather-integrate count 0: pass
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/missed-skill-sent-back/current/run-3: ran herdr-say w1:p4: pass
  herdr-say ["w1:p4", "Load tdd, codebase-design (read each SKILL.md by path), apply it to ticket 1099, then hand off again"] exit 0
```

### supervisor-ticket-skills/loaded-skill-integrated

```text
PASS supervisor-ticket-skills/loaded-skill-integrated: 3/3 runs passed (pass rate 1.00, stddev 0.00); run 1: ran octo-feather-lane skills 1094 exit 0: recorded run octo-feather-lane skills 1094 (exit 0); ran octo-feather-integrate 644 exit 0: recorded run octo-feather-integrate 644 implementer-gh1094 (exit 0); branch_paths: changed agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md; each of agents/supervisor.md, evals/skill-triggers/cases.json, evidence/2026-11-19-gh644-supervisor-skills.md changed [184.5 s] [kit b4ff5107005bc053ff844175de688b85b3380bda]
  baseline FAIL supervisor-ticket-skills/loaded-skill-integrated: 0/3 runs passed (pass rate 0.00, stddev 0.00); run 1: ran octo-feather-lane skills 1094 exit 0: no run of octo-feather-lane with these arguments in the sandbox's record (4 entries; runs of octo-feather-lane: octo-feather-lane --help (exit 1)); run 2: ran octo-feather-lane skills 1094 exit 0: no run of octo-feather-lane with these arguments in the sandbox's record (4 entries; runs of octo-feather-lane: octo-feather-lane --help (exit 1)); run 3: ran octo-feather-lane skills 1094 exit 0: no run of octo-feather-lane with these arguments in the sandbox's record (4 entries; no run of octo-feather-lane recorded) [211.4 s] [kit 7933ff0cce5224f590bd2b503bb32eb42f151951]
  compare supervisor-ticket-skills/loaded-skill-integrated: baseline kit 7933ff0cce52 beside current kit b4ff5107005b
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     70.5 +/- 8.0         61.5 +/- 14.5        -9.0
    tokens     244759 +/- 34906     213454 +/- 60742     -31304
    cost usd   0.3398 +/- 0.0213    0.2645 +/- 0.0483    -0.0753
```

Pin: `octo-feather-qa --verdict 20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated`

Each graded `ran` fact and every recorded run matching it (sandbox.json attempts, argv whole as JSON):

```text
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-1: ran octo-feather-lane skills 1094 exit 0: fail
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-1: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-2: ran octo-feather-lane skills 1094 exit 0: fail
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-2: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-3: ran octo-feather-lane skills 1094 exit 0: fail
  no matching recorded run
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/baseline/run-3: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/current/run-1: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/current/run-1: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/current/run-2: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/current/run-2: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/current/run-3: ran octo-feather-lane skills 1094 exit 0: pass
  octo-feather-lane ["skills", "1094"] exit 0
20261120T024345Z-2fd725/supervisor-ticket-skills/loaded-skill-integrated/current/run-3: ran octo-feather-integrate 644 exit 0: pass
  octo-feather-integrate ["644", "implementer-gh1094"] exit 0
```

### Analysis

```text
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  non-discriminating fact supervisor-ticket-skills/loaded-skill-integrated: ran octo-feather-integrate ["644"] 0: pass in every run on both kits
  non-discriminating fact supervisor-ticket-skills/loaded-skill-integrated: branch_paths ["agents/supervisor.md", "evals/skill-triggers/cases.json", "evidence/2026-11-19-gh644-supervisor-skills.md"]: pass in every run on both kits
  high variance supervisor-ticket-skills/missed-skill-sent-back: baseline kit pass rate 0.33 +/- 0.58
```

### To fill

Smoke: agents/supervisor.md run 20261120T024345Z-2fd725 at kit b4ff5107, --runs 3 --baseline origin/main (7933ff0c): the Delivery line 'When you consume a worker's ticket result' on both outcomes of `octo-feather-lane skills`; missed-skill-sent-back PASS 3/3 (baseline FAIL 1/3), loaded-skill-integrated PASS 3/3 (baseline 0/3). No role or skill file changed in this ticket: the line under test was added by #1099.
Removed: nothing deleted. Incident: just qc failure of issue-lifecycle#acceptance-ticket-skills, record 20261120T021554Z-ff34515d (head 4bbca962): the supervisor's send-back before integration had no evidence.
