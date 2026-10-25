# gh160: writers and reviewers run one owned-rule search

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch agents/implementer.md (writer case implementer-owned-rule, base vs head, below)
Smoke: agents/code-reviewer.md .agents/skills/code-review/ (reviewer-owner-lines, base vs head, below)
Smoke: agents/corrector.md (one corrector run, base vs head, below)
Removed: nothing deleted. Incident: class `duplicated-rule`, 8 finding lines after #124 closed (lanes/archive gh121.handoffs.jsonl x3, gh152 x2, gh157 x3; issue #160): writers restated an owned rule the lane wrote, fix rounds pointed only the listed sites, and each next review found more.

## Change (ladder, docs/adr/0008)

- Rung 1 (structure) already holds the rule's owner (docs/adr/0008 rung 1); nothing structural stops prose in a comment or help text from restating it.
- Rung 2 not taken: telling a restatement from a pointer is a text-similarity stand-in, a proxy (brief; docs/adr/0008 rung 2).
- Rung 3, structured judgment, both sides: the code-review skill's Verdict step (step 4, `Owner:` paragraphs) now has writers (implementer, corrector) run the reviewer's owned-rule search on their own diff before commit and report the same `Owner:` field; agents/implementer.md and agents/corrector.md point there, docs/adr/0008 rung 3 names the field (corrected in place). The reader (`octo-feather-lane fields`) already parses it; no new check.
- Rung 4, instruction with failure example: search once per part of the rule (gh157 rounds), and a fix round searches again (gh121, gh152, gh157). agents/code-reviewer.md: a delta review's owned-rule search still spans the whole repo.

## Runs

Results below, one run at a time, `just qa --suite ladder --case <id> --kit-ref <ref>`.
