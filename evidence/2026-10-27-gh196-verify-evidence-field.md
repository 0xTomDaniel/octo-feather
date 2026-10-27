# gh196: reports cite evidence records; feature map kept current

Smoke: agents/implementer.md, agents/corrector.md (isolated role runs pending, run by the supervisor: cases implementer-verify-map-current, corrector-evidence-field, implementer-verify-pass; section Isolated role runs below, docs/owed-evals/136.md)
Removed: nothing; two Output fields, one implementer Rules line, one corrector Output pointer.

## Change

- `agents/implementer.md` Rules: a ticket adding a user-facing feature or changing how a user reaches or drives a mapped one updates that feature's file in the verify skill's feature map in the same ticket and drives it live (quality `#acceptance-verify-map-current`).
- `agents/implementer.md` Output: owns the form of the Evidence field and, on a full verify skill pass, the Coverage field.
- `agents/corrector.md` Output: sends the Evidence field, form pointing to the implementer's Output.
- `evals/fixtures/python-app-verify-live`: a byte copy of `templates/python` (git-tracked files): verify-app that appends an evidence record per drive, `qc.toml`, `docs/specs/app.spec.html`.
- `evals/role-transcripts`: new cases implementer-verify-map-current, corrector-evidence-field; implementer-verify-pass gains `field_lines Coverage includes {"text": "hello read and driven"}`.

## Fixture smoke

Not a role run: the implementer ran the fixture's helper in a git copy (no Pi process), `XDG_STATE_HOME` under /tmp, the worktree's `scripts/` first on PATH: `verify-app run`, 5 PASS, `verify-app: evidence record 20261027T163802Z-7ca9caad (criterion app#acceptance-hello-json; ...)`, run PASS.

PATH: the template helper needs `octo-feather-evidence` on PATH. The live kit install (`~/src/octo-feather-kit/scripts`, 1d5bafb) does not have it yet, so the qa runs put the worktree's `scripts/` first on PATH (demo commands in the implementer's report).

## Isolated role runs

Pending: the supervisor runs each with `just qa --case ID --kit-ref 8451938` (expected FAIL) and `just qa --case ID` at head (expected PASS), and records both result lines with run ids here.

Stated limit: `field_lines Evidence` grades a present, well-formed `Evidence:` line; the record id is random, so no exact fact matches it and the field's none line also passes. The id is checked by reading the run's final message against its `evidence record <id>` tool output.
