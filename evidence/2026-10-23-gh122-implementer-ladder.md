# gh122 (ticket #130): ladder suite, implementer builds no unasked check

Smoke: evals/ladder/ (cases implementer-secret-grep, implementer-exec-bit; role agents/implementer.md unchanged), .agents/skills/eval-cases/SKILL.md (fact list: field_lines, branch_paths)
Removed: nothing from the owed list yet: the "Implementer, ladder step" entry in docs/owed-evals/118.md stays, pointing at evals/ladder/, until the supervisor's live run shows implementer-secret-grep failing at 9ba7c51 and passing at the lane head.

New facts (scripts/check-evals --help, graded in scripts/octo-feather-qa, stub-pi tests in tests/qa.sh):
- `field_lines`: the final message's column-0 field lines, parsed by `octo-feather-lane fields -` (the `outside` and `check_lines` parser `verdict` uses, plus `Owner:` lines per the code-review skill's Verdict step). Check, Owner, or any other field (Blocked); `none`, `includes`, `every`.
- `branch_paths`: the case repo's changed paths against main's setup commit (committed, uncommitted, untracked), recorded by the watcher when pi ends; `untouched`, `touched`.

Cases written and committed before any run; neither reworded after. No live run here (lane quota: the supervisor runs every live case).

## implementer-secret-grep (train)

Fails-before, `--kit-ref 9ba7c51`:

(result line, run id: supervisor's live run)

Head:

(result line, run id: supervisor's live run)

## implementer-exec-bit (held-out, scored apart)

Head:

(result line, run id: supervisor's live run)

`--kit-ref 9ba7c51`:

(result line, run id: supervisor's live run)
