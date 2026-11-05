# gh503 T8 (#554): the code reviewer judges whether each tagged acceptance test demonstrates its criterion

Change: code-review skill Verdict step (patch + materialized): **Block** gains a test that does not demonstrate the criterion it is tagged with; new **Criterion tests** paragraph owns the judgment (cases selected, assertions, expected values, substitutions), its per-criterion report line and class `criterion-evidence-mismatch`. agents/code-reviewer.md body: Purpose names the judgment; Rules point at **Block** and **Criterion tests**. Spec: quality#quality-reviewer, #acceptance-review-test-adequacy (call: quality.calls.jsonl, lane gh503 `adds`, 2026-11-04T18:40:13Z).

Smoke: agents/code-reviewer.md .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch (reviewer-criterion-test-adequacy below)
Removed: agents/code-reviewer.md Rules "block only on a documented standards breach (cite file and rule) or a named simplification that lists the lines it deletes" (a restatement of the skill's **Block** list; now a pointer to it). Incident: issue #503 consensus item 1 (comment 2026-11-03T19:44:38Z): once a criterion's evidence is its own tagged regression test, no one judged whether that test shows the criterion; the reviewer was scoped to code quality only.

Case: role-transcripts/reviewer-criterion-test-adequacy (fixture python-app, head python-app-shout-tagged). The lane claims hello#acceptance-shout and hello#acceptance-shout-json through pytest `criterion` tags; tests/test_cli.py::test_shout_json, tagged shout-json, runs `hello Grace --json` with no `--shout` and asserts the unshouted greeting: a sound literal test of another behaviour, green on the fixture's own gate (pytest 5 passed, ruff, basedpyright clean). Graded: `Verdict: blocking` field line, and the final json block's `blocking` list holds that test.

Base: aa95911 (the case committed, kit before the change). Runs serial, one at a time box-wide, each slotted by the supervisor.

RUNS: pending.
