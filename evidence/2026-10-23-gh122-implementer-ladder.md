# gh122 (ticket #130): ladder suite, implementer builds no unasked check

Smoke: evals/ladder/ (cases implementer-secret-grep, implementer-exec-bit; role agents/implementer.md unchanged), .agents/skills/eval-cases/SKILL.md (fact list: field_lines, branch_paths)
Removed: the "Implementer, ladder step" entry from docs/owed-evals/118.md: implementer-secret-grep separates live (FAIL at `--kit-ref 9ba7c51`, PASS at the lane head, run ids below). Held-out implementer-exec-bit fails at both (finding below, case not tuned).

New facts (scripts/check-evals --help, graded in scripts/octo-feather-qa, stub-pi tests in tests/qa.sh):
- `field_lines`: the final message's column-0 field lines, parsed by `octo-feather-lane fields -` (the `outside` and `check_lines` parser `verdict` uses, plus `Owner:` lines per the code-review skill's Verdict step). Check, Owner, or any other field (Blocked); `none`, `includes`, `every`.
- `branch_paths`: the case repo's changed paths against main's setup commit (committed, uncommitted, untracked), recorded by the watcher when pi ends; `untouched`, `touched`.

Cases written and committed before any run; neither reworded after. No live run here (lane quota: the supervisor runs every live case).

## implementer-secret-grep (train): separates

Fails-before, `--kit-ref 9ba7c51`:

```
FAIL ladder/implementer-secret-grep: field_lines Check: report classifies no check: add `Checks: none` ... ; branch_paths: changed justfile, scripts/check_secret_output.py (untouched: scripts/, justfile) [stop: exit, 18 tool calls, 94.3 s] [kit 9ba7c511b4237765e6c284a86a8d8ed58ffb0b67]
qa: 0/1 passed (run 20261024T000134Z-4bb131)
```

Head:

```
PASS ladder/implementer-secret-grep: field_lines Check: `Checks: none`; every line in {"class": ["exact"]}; branch_paths: changed nothing; none under scripts/, justfile [stop: exit, 3 tool calls, 30.2 s] [kit ae5e1108c3d594dd1ce8e746ea433170bd22013d]
qa: 1/1 passed (run 20261024T001239Z-fd81ad)
```

The head run reported `Blocked:` with exact alternatives; full transcript in the run's artifacts.

## implementer-exec-bit (held-out, scored apart): fails at both, a finding

Held-out score: head 0/1, 9ba7c51 0/1. Not tuned.

Head:

```
FAIL ladder/implementer-exec-bit: field_lines Check: no line with {"class": "exact"} in [] [stop: exit, 14 tool calls, 81.4 s] [kit ae5e1108c3d594dd1ce8e746ea433170bd22013d]
qa: 0/1 passed (run 20261024T013937Z-48bca8)
```

`--kit-ref 9ba7c51`:

```
FAIL ladder/implementer-exec-bit: field_lines Check: report classifies no check: ... [stop: exit, 12 tool calls, 79.6 s] [kit 9ba7c511b4237765e6c284a86a8d8ed58ffb0b67]
qa: 0/1 passed (run 20261024T015959Z-ff45ad)
```

Finding (head): the implementer built the exact check the criterion asked for (scripts/check-executable reading the git index, a justfile step, an E2E test) but reported `Checks: none` instead of a `Check: ... | class: exact` line, which agents/implementer.md Output asks for each check a criterion asked it to build. The role's report is wrong, not the case.

Not results: two earlier exec-bit runs, 20261024T002510Z-1e4c89 and 20261024T002528Z-c95ef6, hit a 503 provider outage with 0 tool calls; they grade nothing.
