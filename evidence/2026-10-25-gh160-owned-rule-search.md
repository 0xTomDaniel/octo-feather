# gh160: writers and reviewers run one owned-rule search

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch agents/implementer.md (writer case implementer-owned-rule, base vs head, below)
Smoke: agents/code-reviewer.md .agents/skills/code-review/ (reviewer-owner-lines, base vs head, below)
Smoke: agents/corrector.md (one corrector run, base vs head, below)
Removed: nothing deleted. Incident: class `duplicated-rule`, 8 finding lines after #124 closed (lanes/archive gh121.handoffs.jsonl x3, gh152 x2, gh157 x3; issue #160): writers restated an owned rule the lane wrote, fix rounds pointed only the listed sites, and each next review found more.

## Change (ladder, docs/adr/0008)

- Rung 1 (structure) already holds the rule's owner (docs/adr/0008 rung 1); nothing structural stops prose in a comment or help text from restating it.
- Rung 2 not taken: telling a restatement from a pointer is a text-similarity stand-in, a proxy (brief; docs/adr/0008 rung 2).
- Rung 3, structured judgment, both sides: writer side added to the code-review skill's Verdict step (step 4, `Owner:` paragraphs); agents/implementer.md and agents/corrector.md point there, docs/adr/0008 rung 3 names the field (corrected in place). The reader (`octo-feather-lane fields`) already parses it; no new check.
- Rung 4, instruction with failure examples (gh157; gh121, gh152, gh157): the same step 4 `Owner:` paragraphs. agents/code-reviewer.md Required inputs points there for a delta review.

## Runs

Results below, one run at a time, `just qa --suite ladder --case <id> --kit-ref <ref>`.

Base = `--kit-ref a9b6472` (main), head = `--kit-ref d9da376` (this change). Cases and grader are the head's (a85d2d2, committed before any run).

### implementer-owned-rule (writer): base 0/3, head 3/3

- base FAIL 20261025T143957Z-ca8933, 20261025T144043Z-61cf38, 20261025T144136Z-1b260d: each "report names no owned rule" (no `Owner:` field). branch_paths passed in all 3.
- head PASS 20261025T145218Z-fe6a6f, 20261025T145308Z-787e5d, 20261025T145418Z-df7030: one `Owner:` line for docs/adr/0002-errors-name-the-fix.md, `restated: none`; branch_paths pass.

Read from the transcripts, not graded: base and head alike pointed README.md to the ADR and rewrote a first-draft docstring that restated the rule into a pointer (base 2 of 3 runs wrote such a docstring, head 2 of 3), so on this small fixture (its AGENTS.md already carries the rule, its repo has 8 files) the pointing behaviour held before the change. The case separates on the declared field only; the field's truth stays with review. Head run df7030 left README.md "Errors name the command that fixes them: docs/adr/0002-errors-name-the-fix.md.", a partial restatement beside its pointer, while reporting `restated: none`. A fixture where the restatement sits far from the diff is owed (docs/owed-evals/160.md).

### reviewer-owner-lines (reviewer): base 3/3, head 3/3

- base PASS 20261025T142855Z-61e58e, 20261025T143057Z-c11727, 20261025T143225Z-8ec268.
- head PASS 20261025T145523Z-569504, 20261025T145636Z-a56989, 20261025T145811Z-0842e8.

Does not separate: the 8-file fixture holds every restatement in 3 files a one-phrase grep finds. The rounds in #160 were on the kit repo itself; a separating reviewer case is owed (docs/owed-evals/160.md).

### agents/corrector.md smoke: corrector-fact-lesson, one run each

Graded fact (declared `rung`) PASS both sides; the smoke is read from the final message with `octo-feather-lane fields -`, not graded:

- head 20261025T151947Z-5c9312: code-review/SKILL.md in 10 transcript events; final message holds `Owner: AGENTS.md: every tracked file under .githooks/ or starting with #! is committed as mode 100755 | restated: none` (Owner errors: none).
- base 20261025T152109Z-aa49d5: code-review/SKILL.md in 0 events; Owner errors: "report names no owned rule".

## Review round 1 (head 63bae88, class duplicated-rule)

Removed: agents/corrector.md and agents/code-reviewer.md clauses that restated code-review step 4 `Owner:` paragraphs (writer search on its own diff, point every hit; whole-repo scope), and this file's summaries of them; each now points to step 4, `Owner:` paragraphs. Role wiring (when to read step 4, where it lives) kept. No rerun: the instruction each role reaches is the same step 4 text the head runs above read (corrector 5c9312 read code-review/SKILL.md), so the edit is pointer-only.
