# gh122 (ticket #133): ladder cases, code reviewer names every restatement of an owned rule

Smoke: evals/ladder/ (cases reviewer-owner-lines, reviewer-owner-pointers, reviewer-owner-none; role agents/code-reviewer.md and the code-review skill unchanged), evals/fixtures/docs-rules/, evals/fixtures/docs-rules-restated/, evals/fixtures/docs-rules-pointers/, evals/fixtures/docs-rules-count/
Removed: the "Code reviewer, restatements of an owned rule" entry from docs/owed-evals/124.md (ticket #134): the supervisor's live run below shows reviewer-owner-lines FAIL at `--kit-ref 6567cc7` and PASS at lane head 5b5a5c9, so the case separates and the owed eval is paid; held-out 2/2 at head, scored apart. The file keeps its header (no convention deletes an owed-evals file; docs/owed-evals/115.md keeps one with no entry).

Owned rule: the `code-review` skill's Verdict step (for every rule the diff writes or changes where it is owned, one column-0 `Owner: <path>: <rule> | restated: none|<path>:<line>[, ...]`, the whole repo searched, unchanged files included, or `Owners: none`) and agents/code-reviewer.md Output (send the `Owner:` lines or `Owners: none`). Design: docs/owed-evals/124.md; smoke and fixture: evidence/2026-10-23-gh124-owner-lines-smoke.md.

Fixtures (base `docs-rules` on main, rebuilt from the smoke's fixture: AGENTS.md with the one-place rule, docs/adr/0001-cli-only.md, README.md saying "the error should tell the user which command fixes it", agents/worker.md, src/app.py, tests/test_app.py, a justfile whose `check` runs the tests; each head a full tree committed over main as the qa harness does):

- `docs-rules-restated`: adds docs/adr/0002-errors-name-the-fix.md (every error names its fix command; usage errors exit 2), restates it in AGENTS.md:10 and agents/worker.md:8, src/app.py's missing-file error names `app init`, two tests; README.md unchanged (README.md:11 restates it).
- `docs-rules-pointers`: the same ADR, src and tests; AGENTS.md, agents/worker.md and README.md (line 11 replaced) only point to docs/adr/0002-errors-name-the-fix.md.
- `docs-rules-count`: `app count` in src/app.py and one test; no doc, no rule.

`just check` exits 0 in each of the four fixture dirs.

Cases (role code-reviewer, fixture docs-rules; the brief names the ticket and the diff `main...<branch>` and asks for the verdict report as the final message, sandbox like the other reviewer cases; it never names owners, restatements, paths to list or fields):

- `reviewer-owner-lines` (train), head docs-rules-restated, branch implementer-t5. Expects `field_lines` Owner includes `{path: docs/adr/0002-errors-name-the-fix.md, restated: X}` for each X of AGENTS.md, agents/worker.md, README.md (each object matches any line, so the union across the ADR's lines counts; `:<line>` stripped).
- `reviewer-owner-pointers` (held-out), head docs-rules-pointers, branch implementer-t7, same ticket text. Expects Owner includes `{path: docs/adr/0002-errors-name-the-fix.md}` and every Owner line `restated: none` (`every {restated: []}`). The includes follows the owned rule (one `Owner:` line per owned rule the diff writes), so `Owners: none` fails here.
- `reviewer-owner-none` (held-out), head docs-rules-count, branch implementer-t8. Expects `Owners: none`.

So listing every touched file passes no pointer or none case.

Not graded: `Verdict:` lines and finding prose (the verdict label is not owned by this change).

Harness smoke, no model: the three cases copied to a scratch evals dir with tests/qa.sh's stub pi (STUB-STEPS: `git diff --stat main...<branch>`, `git status --short; git branch --show-current`, then a canned report), `scripts/octo-feather-qa --evals <scratch>` in the qc sandbox (run 20261024T034110Z-2be0ad, 4/10 as designed). Each case repo is set up on its branch with the expected diff stat (restated: AGENTS.md, agents/worker.md, the ADR, src, tests; pointers: also README.md; count: src and tests only). Reports and results:

- train: all three paths PASS; README.md missing FAIL; `Owners: none` FAIL; a bullet `- **Owner:** ...` FAIL (`report names no owned rule`); every touched file listed (plus src/app.py) PASS (extra paths allowed by design).
- pointers: `restated: none` PASS; every touched file listed FAIL; `Owners: none` FAIL.
- none: `Owners: none` PASS; an ADR `Owner:` line FAIL.

Cases written and committed before any run; held-out never reworded after one. No live run here (lane quota: the supervisor runs every live case).

## Fails-before, `--kit-ref 6567cc7`

Supervisor's live run, 2026-10-24:

```
FAIL ladder/reviewer-owner-lines: field_lines Owner: report names no owned rule: add `Owners: none`, or one `Owner:` line per owned rule the diff writes or changes [stop: exit, 17 tool calls, 55.8 s] [kit 6567cc7b30ccd90936fa75a1f3146181d046ddae]
qa: 0/1 passed (run 20261024T040855Z-87d169)
```

## Head

Supervisor's live run, 2026-10-24, lane head 5b5a5c9:

```
PASS ladder/reviewer-owner-lines: field_lines Owner: 3 line(s) [{"path": "docs/adr/0002-errors-name-the-fix.md", "rule": "every error names its corrective command", "restated": ["AGENTS.md", "agents/worker.md", "README.md"]}, {"path": "docs/adr/0002-errors-name-the-fix.md", "rule": "usage errors exit 2", "restated": ["AGENTS.md", "agents/worker.md"]}, {"path": ; holds {"path": "docs/adr/0002-errors-name-the-fix.md", "restated": "AGENTS.md"}; {"path": "docs/adr/0002-errors-name-the-fix.md", "restated": "agents/worker.md"}; {"path": "docs/adr/0002-errors-name-the-fix.md", "restated": "README.md"} [stop: exit, 17 tool calls, 72.2 s] [kit 5b5a5c96d6523ee1a3ba779e875418baff6ad345]
qa: 1/1 passed (run 20261024T041151Z-d2b580)
```

Separates: FAIL at 6567cc7 (no Owner field), PASS at head.

## Held-out (scored apart)

Supervisor's live run, 2026-10-24, lane head 5b5a5c9 only (not run at 6567cc7): 2/2 PASS. No held-out FAIL, so no finding.

```
PASS ladder/reviewer-owner-pointers: field_lines Owner: 3 line(s) [{"path": "docs/adr/0002-errors-name-the-fix.md", "rule": "every error names its fixing command", "restated": []}, {"path": "docs/adr/0002-errors-name-the-fix.md", "rule": "usage errors exit 2", "restated": []}, {"path": "docs/adr/0002-errors-name-the-fix.md", "rule": "other errors exit 1", "restate; holds {"path": "docs/adr/0002-errors-name-the-fix.md"}; every line in {"restated": []} [stop: exit, 23 tool calls, 61.1 s] [kit 5b5a5c96d6523ee1a3ba779e875418baff6ad345]
qa: 1/1 passed (run 20261024T041304Z-1fb1b4)
PASS ladder/reviewer-owner-none: field_lines Owner: `Owners: none` [stop: exit, 19 tool calls, 46.0 s] [kit 5b5a5c96d6523ee1a3ba779e875418baff6ad345]
qa: 1/1 passed (run 20261024T041405Z-01259f)
```

Lines as the qa printer wrote them (it cuts the long field lists), from the supervisor's run output.
