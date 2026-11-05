# gh503 T8 (#554): the code reviewer judges whether each tagged acceptance test demonstrates its criterion

Change: code-review skill Verdict step (patch + materialized): **Block** gains a test that does not demonstrate the criterion it is tagged with; new **Criterion tests** paragraph owns the judgment (cases selected, assertions, expected values, substitutions), its per-criterion report line and class `criterion-evidence-mismatch`. agents/code-reviewer.md body: Purpose names the judgment; Rules point at **Block** and **Criterion tests**. Spec: quality#quality-reviewer, #acceptance-review-test-adequacy (call: quality.calls.jsonl, lane gh503 `adds`, 2026-11-04T18:40:13Z).

Smoke: agents/code-reviewer.md .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch (reviewer-criterion-test-adequacy below)
Removed: agents/code-reviewer.md Rules "block only on a documented standards breach (cite file and rule) or a named simplification that lists the lines it deletes" (a restatement of the skill's **Block** list; now a pointer to it). Incident: issue #503 consensus item 1 (comment 2026-11-03T19:44:38Z): once a criterion's evidence is its own tagged regression test, no one judged whether that test shows the criterion; the reviewer was scoped to code quality only.

Case: role-transcripts/reviewer-criterion-test-adequacy (fixture python-app-spec: python-app plus docs/specs/hello.spec.html holding the criteria; head python-app-shout-tagged). The lane claims hello#acceptance-shout and hello#acceptance-shout-json through pytest `criterion` tags; tests/test_cli.py::test_shout_json, tagged shout-json, runs `hello Grace --json` with no `--shout` and asserts the unshouted greeting: a sound literal test of another behaviour, green on the fixture's own gate (pytest 5 passed, ruff, basedpyright clean). Graded: `Verdict: blocking` field line, and the final json block's `blocking` list holds that test.

Base: aa95911 (the case committed, kit before the change). Runs serial, one at a time box-wide, each slotted by the supervisor.

1. First wording (task pasted both criteria texts; fixture python-app, no spec), base aa95911, run 20261105T031403Z-d9e911, wall 63 s:
   `PASS role-transcripts/reviewer-criterion-test-adequacy: field_lines Verdict: 1 line(s) [{"text": "blocking"}]; holds {"text": "blocking"}; declared_includes blocking: holds {"test": "tests/test_cli.py::test_shout_json"} [stop: exit, 26 tool calls, 61.2 s] [kit aa959113cf09f963ccc4bd71b8e72eb74f1d91b5]`
   Not a fails-before: with the criterion text in its brief, the old reviewer compared test to text (class acceptance-scenario-mismatch, citing the fixture AGENTS.md "one or two tests per acceptance criterion" and tdd).

Case change (commit 0760a86): criterion text moved out of the task into the target's spec on main (base fixture python-app-spec, docs/specs/hello.spec.html); the task names criterion ids only. Evidence that a real review brief names ids, not text: this lane's /tmp/gh503/brief-reviewB2.md line 9, `  - Each of the 4 pilot B criteria (quality#acceptance-one-execution, -one-execution-incomplete; comms#acceptance-report-gate-budget; issue-lifecycle#acceptance-merge-ask-gate-budget): does its captured demo at f72d060 demonstrate it.` (The same line also asks the reviewer outright for the demonstrate judgment, by brief.)

2. Second wording, base aa95911, run 20261105T031631Z-372653, wall 65 s:
   `PASS role-transcripts/reviewer-criterion-test-adequacy: field_lines Verdict: 1 line(s) [{"text": "blocking"}]; holds {"text": "blocking"}; declared_includes blocking: holds {"test": "tests/test_cli.py::test_shout_json"} [stop: exit, 25 tool calls, 64.1 s] [kit aa959113cf09f963ccc4bd71b8e72eb74f1d91b5]`
   The old reviewer read docs/specs/hello.spec.html unprompted (read call after code-review and tdd loads) and blocked test_shout_json (class criterion-not-exercised, citing hello.spec.html:10).

Result: no fails-before. The kit before the change (aa95911) already blocks a tagged test that does not demonstrate its criterion, on both wordings, 2 of 2 runs (single samples). Stop rule (director): no further tuning; no after-run made. The role and skill lines are to be judged on need (quality#acceptance-qa-fails-before not shown by this case).
