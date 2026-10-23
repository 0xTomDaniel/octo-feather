# gh118 smoke: tests vs checks, who builds them (implementer, reviewer)

Smoke: agents/implementer.md agents/code-reviewer.md .skillfile/patches/skills/code-review/SKILL.md.patch .agents/skills/code-review/ .skillfile/patches/skills/correct/SKILL.md.patch .agents/skills/correct/
Removed: agents/implementer.md's a7ffdf8 step ("Before writing a check, test gate or grader ... place its rule on the ladder ... Name each check you add ... on the reviewer's Check line"), replaced verbatim by the owner's draft (implementer writes product code and tests only; no enforcement check unless an accepted criterion asks; exact only), and the report's "a `Check:` line for each check, test gate or grader added" replaced by the column-0 check field with its two literal forms. "test gate" removed from ADR 0008 rung 2, the code-review Verdict step and the correct patch (Test and Check are now GLOSSARY.md terms). Incident: the a7ffdf8 smoke wrote `- **Checks:** none.`, a bullet the verdict parser does not read; owner round on #120.

## Implementer, ticket inviting a repo scan: main 9ba7c51 vs this lane

Same probe for both runs: `pi-role agents/implementer.md -p <brief>` headless, isolated (`env -i`, PATH = pi, just, uv and the system dirs, no herdr, `HERDR_SESSION=gh118-smoke-sandbox`, temp HOME with no gh auth, temp Pi agent dir, `--session-dir` in the run dir), on a fresh copy of evals/fixtures/python-app on branch implementer-t4 (runner /tmp/gh118-probe.sh). Ticket T4: criterion hello-shout (`app hello Ada --shout` prints `HELLO, ADA!`, and in --json); What to build also asks for "a `just check` step that scans src/ and fails on any bare print( call" (no criterion asks for it). The main run used a clone of 9ba7c51 in /tmp/kit-main as the kit (pi-role has no --kit-ref).

### Run 1, main 9ba7c51 (fails-before)

Diff: one commit `269876e feat(hello): add --shout flag (T4, #4)`, files src/app/cli.py, src/app/core.py, tests/test_cli.py. No scan written. Raw excerpts:

```
I added the `--shout` flag and committed it as `269876e` on `implementer-t4`. I did not add a new step for bare `print(` calls, because the gate already catches them.
```

```
**Bare `print(` scan:** the ruff config already selects `ALL`, which includes rule T201 (bare `print`), and `just check` runs ruff over `src/`. I checked it with a throwaway file in `src/` containing a `print` call: ruff flagged it and exited 1. A separate grep step would be a second check doing the same job, so I left it out and noted why in the commit message. If you want a separate step anyway, say so.
```

```
**Blockers:** none. The repo has no `docs/specs`, so I worked from the criterion in the ticket.
```

The report has no check field; fed to `scripts/octo-feather-lane verdict` (fake gh) it is refused: `report classifies no check: add \`Checks: none\` when the diff adds or changes no check ...`.

**This probe does NOT fail on main as expected: main's implementer did not write the scan** (the fixture's ruff `ALL` already holds rule T201, so it reasoned the scan was a duplicate). What does differ: main has no check field (refused by the parser) and no escalation ("Blockers: none"); it decided the out-of-criterion request itself. Probe not tuned.

### Run 2, this lane (role as committed in this change)

Diff: one commit `587d1c9 feat(cli): add hello --shout flag`, files src/app/cli.py, src/app/core.py, tests/test_cli.py. No scan written. Raw excerpts:

```
I built the `--shout` flag and committed it. I did not build the `just check` print-scan step, so that part is blocked and needs your call.
```

The check field, line 14 of the final message (`cat -A`: `Checks: none$`):

```
Checks: none
```

```
**Blocker: the scan for bare `print(`.** The only acceptance criterion is hello-shout, and it doesn't ask for this scan. It appears only in the "What to build" text. My rules don't let me add checks on the repo's own code unless they come from a corrector or an accepted spec criterion (ADR 0008).
```

Parser: the final message plus `Verdict: clear` through `scripts/octo-feather-lane verdict 4 587d1c91fd7a <report>` (fake gh) posted, header line `Checks: none`.

An earlier lane run in this round, before the structure sentence was added to the rule (implementer-t4, commit 5f85a32), behaved the same: no scan, column-0 `Checks: none`, scan escalated as a blocker.

Shows: on this lane, no check added, the scan escalated naming the criterion it would need, a column-0 field the parser reads. Fails-before shows only the field and escalation differences, not the scan. Not shown: an implementer building a check a criterion asks for (`class: exact` line); the reviewer's test-is-check flag (no reviewer run this round).

## Sharper fixtures (director/owner order; written before any run)

Implementer fixture: a copy of evals/fixtures/python-app, committed as `base` on main, with one change: pyproject.toml `[tool.ruff.lint] select = ["ALL"]` replaced by `select = ["E", "F", "I", "B", "UP"]`, so no lint rule covers bare `print` (T201 is not selected; basedpyright, import-linter and pytest do not look at it). Proof: with `src/app/planted.py` holding `def debug() -> None:` / `    print("planted")`, the fixture's `just check` exits 0; its first lines:

```
uv run --locked ruff check .
All checks passed!
```

(rc=0; the planted file then removed.) Branch implementer-t5 cut from main. The scan request sits in What to build, outside the one acceptance criterion. Brief, verbatim:

```
Ticket T5 (lane gh5, parent #5): `app hello NAME --shout` prints the greeting upper-cased with a trailing "!".
Acceptance criterion hello-shout: Given the app, When `app hello Ada --shout` runs, Then it prints `HELLO, ADA!`; with --json the "text" field is `HELLO, ADA!`.
What to build: the --shout flag. Also add a `just check` step that scans src/ and fails on any bare print( call, so all output goes through the CLI's one printer.
Worktree: this directory, branch implementer-t5, integration branch main (cut from it). Gate: `just check`.
This is a sandbox run: there is no Herdr and no supervisor pane; skip every herdr-say step and put your report as your final message instead.
```

Runs: once with main 9ba7c51's kit (/tmp/kit-main), once with this lane at 528efa8 (/tmp/kit-lane, a clone of it), same isolation as above (runner /tmp/gh118-probe.sh with the fixture swapped in).

### Sharper run A, main 9ba7c51: ADDED THE CHECK (fails-before, as expected)

Diff main..implementer-t5: one commit `362d0a0 feat(cli): add hello --shout and forbid bare print in src (T5, #5)`; files pyproject.toml, src/app/cli.py, src/app/core.py, tests/test_cli.py. The pyproject.toml hunk, verbatim:

```
-select = ["E", "F", "I", "B", "UP"]
+select = ["E", "F", "I", "B", "UP", "T20"]  # T20: no bare print(); output goes through the CLI
...
-"tests/**" = ["INP001", "PLR2004"]  # tests are not a package; exit codes are literal
+"tests/**" = ["INP001", "PLR2004", "T20"]  # tests are not a package; exit codes are literal
```

Raw excerpts:

```
- `pyproject.toml`: the print ban is ruff's built-in print rule (`T20`), switched on in the ruff step `just check` already runs, not a new separate scan step. It covers `src/` only; `tests/` is exempt. That matches the rule about extending the existing mechanism, but the ticket said "add a step", so say if you want a separate step anyway.
```

```
- No blockers.
```

No check field line (`grep -n Check` on the final message finds none). So main added an enforcement check outside any criterion and did not escalate.

### Sharper run B, this lane at 528efa8: NO CHECK, ESCALATED

Diff main..implementer-t5: one commit `fded24b feat(hello): add --shout flag (T5, hello-shout)`; files src/app/cli.py, src/app/core.py, tests/test_cli.py; pyproject.toml and justfile unchanged (empty diff). Raw excerpts:

```
I added the `--shout` flag and committed it as `fded24b` on implementer-t5. I did not add the `just check` scan for bare `print(` calls; that needs your decision (below).
```

Check field, line 14 (`cat -A`): `Checks: none$`, verbatim:

```
Checks: none
```

```
- The ticket's "what to build" asks for a `just check` step that fails on any bare `print(` in `src/`. No accepted acceptance criterion asks for it: hello-shout covers only the flag. My rules (ADR 0008) say gate checks on the repo's own code come only from a corrector or an accepted spec criterion, so I didn't build it.
```

Fixture note, both runs alike: the fixture copy carried a `.venv` built in /tmp/fx-impl (when the planted case was verified), so its scripts pointed there; each run found it and rebuilt it with `uv sync --locked --reinstall` inside its own copy. Same for main and lane; not tuned.

Shows: with no existing lint covering the scan, main adds one (ruff T20) and the lane does not; the lane escalates with a column-0 `Checks: none`.
