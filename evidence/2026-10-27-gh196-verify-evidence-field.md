# gh196: reports cite evidence records; feature map kept current

Smoke: agents/implementer.md, agents/corrector.md (isolated role runs: cases implementer-verify-map-current, corrector-evidence-field, implementer-verify-pass, each FAIL at --kit-ref 8451938 and PASS at b244085; section Isolated role runs below, docs/owed-evals/136.md)
Removed: nothing; two Output fields, one implementer Rules line, one corrector Output pointer.

## Change

- `agents/implementer.md` Rules: a ticket adding a user-facing feature or changing how a user reaches or drives a mapped one updates that feature's file in the verify skill's feature map in the same ticket and drives it live (quality `#acceptance-verify-map-current`).
- `agents/implementer.md` Output: owns the form of the Evidence field and, on a full verify skill pass, the Coverage field.
- `agents/corrector.md` Output: sends the Evidence field, form pointing to the implementer's Output.
- `evals/fixtures/python-app-verify-live`: a byte copy of `templates/python` (git-tracked files): verify-app that appends an evidence record per drive, `qc.toml`, `docs/specs/app.spec.html`.
- `evals/role-transcripts`: new cases implementer-verify-map-current, corrector-evidence-field; implementer-verify-pass gains `field_lines Coverage includes {"text": "hello read and driven"}`.

## Fixture smoke

Not a role run: the implementer ran the fixture's helper in a git copy (no Pi process), `XDG_STATE_HOME` under /tmp, the worktree's `scripts/` first on PATH: `verify-app run`, 5 PASS, `verify-app: evidence record 20261027T163802Z-7ca9caad (criterion app#acceptance-hello-json; ...)`, run PASS.

PATH: the template helper needs `octo-feather-evidence` on PATH. The live kit install (the box's install clone on PATH, at 1d5bafb) does not have it yet, so the qa runs put the worktree's `scripts/` first on PATH (demo commands in the implementer's report).

## Isolated role runs

Six runs, by the supervisor, one at a time, in the qc sandbox (no live Herdr, no creds): `just qa --case ID --kit-ref 8451938` (before) and `just qa --case ID` at lane head b244085 (after). Tool call numbers are the grader's.

```
$ grep -E '^(PASS|FAIL)' /tmp/gh136-sup/qa196-*.log | cut -c1-160
/tmp/gh136-sup/qa196-corrector-evidence-field-after.log:PASS role-transcripts/corrector-evidence-field: skill_read verify-app: loaded at tool call 9 of 23 (read
/tmp/gh136-sup/qa196-corrector-evidence-field-before.log:FAIL role-transcripts/corrector-evidence-field: field_lines Evidence: no column-0 `Evidence:` line with
/tmp/gh136-sup/qa196-implementer-verify-map-current-after.log:PASS role-transcripts/implementer-verify-map-current: skill_read verify-app: loaded at tool call 2
/tmp/gh136-sup/qa196-implementer-verify-map-current-before.log:FAIL role-transcripts/implementer-verify-map-current: branch_paths: nothing changed under .agents
/tmp/gh136-sup/qa196-implementer-verify-pass-after.log:PASS role-transcripts/implementer-verify-pass: skill_read_before maintain-verification-skill edit: loaded
/tmp/gh136-sup/qa196-implementer-verify-pass-before.log:FAIL role-transcripts/implementer-verify-pass: skill_read_before maintain-verification-skill edit: first
```

implementer-verify-map-current:
- --kit-ref 8451938, FAIL, run 20261027T172851Z-dcb726 (15 calls): changed src/app/cli.py, src/app/core.py, tests/test_cli.py only; no `features/hello.md` change (branch_paths FAIL), no `Evidence:` line (field_lines FAIL).
- b244085, PASS, run 20261027T173004Z-011436 (34 calls): verify-app loaded call 2, commit skill call 26, git commit call 34; changed src/app/ and `.agents/skills/verify-app/features/hello.md` (plus the helper, its SKILL.md, qc.toml, tests); Evidence `hello 20261027T173136Z-cb88eeb4`.

corrector-evidence-field:
- --kit-ref 8451938, FAIL, run 20261027T173148Z-488b7b (30 calls): no `Evidence:` line.
- b244085, PASS, run 20261027T173445Z-94b399 (23 calls): correct loaded call 2, verify-app read call 9; Evidence `hello 20261027T173503Z-050d5c23`.

implementer-verify-pass:
- --kit-ref 8451938, FAIL, run 20261027T173635Z-daee14 (17 calls): first edit call 10 (`features/hello.md`) with no load of maintain-verification-skill; no `Coverage:` line.
- b244085, PASS, run 20261027T173822Z-a923bc (15 calls): maintain-verification-skill loaded call 2, first edit call 7, commit call 13; changed only `.agents/skills/verify-app/`; Coverage `hello read and driven`.

Stated limit: `field_lines Evidence` grades presence only (a present, well-formed `Evidence:` line); the record id is random, so no exact fact matches it and the field's none line would also pass. The two ids above were checked by eye, by the supervisor, against the helper's `evidence record <id>` output in each run's transcript; the implementer rechecked by grep of the run artifacts (011436: 8 hits for `evidence record 20261027T173136Z-cb88eeb4`; 94b399: 14 hits for `evidence record 20261027T173503Z-050d5c23`). Not graded by the case.

Artifacts: $XDG_STATE_HOME/octo-feather/qa/<run id> for each run id above; logs /tmp/gh136-sup/qa196-<case>-{before,after}.log.
