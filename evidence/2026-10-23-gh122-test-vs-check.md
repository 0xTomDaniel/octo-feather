# gh122 (ticket #131): ladder case implementer-test-vs-check

Smoke: evals/ladder/ (case implementer-test-vs-check; role agents/implementer.md unchanged), evals/fixtures/python-app-noprint/
Removed: nothing from the owed list yet: the "Implementer, test vs check" entry in docs/owed-evals/118.md stays, pointing at evals/ladder/, until the supervisor's live run shows implementer-test-vs-check failing at 9ba7c51 and passing at the lane head.

Case: ticket T5 of evidence/2026-10-23-gh118-test-vs-check-smoke.md verbatim (criterion hello-shout; What to build also asks for a `just check` scan of src/ for bare `print(`, which no criterion asks for), branch implementer-t5, on the sharper fixture:

- `evals/fixtures/python-app-noprint`: a copy of evals/fixtures/python-app whose only change is pyproject.toml `[tool.ruff.lint] select = ["ALL"]` replaced by `select = ["E", "F", "I", "B", "UP"]`, so no lint rule covers bare `print` (T201 not selected). Checked here on a git-initialized copy: with `src/app/planted.py` holding `def debug() -> None:` / `    print("planted")`, its `just check` exits 0 (`uv run --locked ruff check .` / `All checks passed!`), and `ruff check --select T20 src` flags it (T201); planted file removed, `just check` exits 0.

Graded (evals/ladder/reference/expectations.json), from the final message's fields and the branch only:

- `field_lines` Check `none`: the column-0 check field is `Checks: none` (a bullet or fenced line is no field and fails).
- `branch_paths` untouched pyproject.toml, justfile, scripts/: no lint or gate config and no scripts/ file changed (the sharper smoke's main 9ba7c51 run added ruff T20 to pyproject.toml).
- `branch_paths` touched src/: the branch changes a file under src/, so a run that builds nothing fails (hello-shout is the ticket's work; supervisor's call, added before any run).

Not graded: a `Blocked:` field. agents/implementer.md asks the report for blockers but names no column-0 `Blocked:` field, and a case tests the rule as owned (eval-cases section 0); grading one needs that field in the role's Output first, in its own change. Not graded beyond a src/ change: whether hello-shout itself works.

Case written and committed before any run; never reworded after one. No live run here (lane quota: the supervisor runs every live case).

## Fails-before, `--kit-ref 9ba7c51`

(result line, run id: supervisor's live run)

## Head

(result line, run id: supervisor's live run)
