# gh173 final-review fix: schema rules point to schema.md (lane gh167, base 51350a5)

Owner: .agents/skills/eval-cases/references/schema.md, every section.

Search: `python3 evidence/2026-10-27-gh173-schema-restatements.py` from the repo root, one block per schema.md
section, each block its regex of that section's normative terms (field names, enums, bounds, refusal words), over
the prose of scripts/*, tests/*.sh (comments), evals/*/suite.json descriptions, .agents/skills/**/*.md
(schema.md itself excluded), agents/, AGENTS.md, justfile comments, docs/ (not docs/specs). Every hit read by hand.

- Before (51350a5, `git archive` copy as the script's root arg): `2026-10-27-gh173-search-before.txt` (662 lines).
- After: `2026-10-27-gh173-search-after.txt` (617 lines); `2026-10-27-gh173-search.diff` (line numbers shift).

## Pointed (restatement replaced by `schema.md, <section>`)

- The four cited: tests/qa.sh:602 (Leaks), :780 (Judgment suite), :788-789 (Calibration), :800 (Suite).
- tests/qa.sh, more: header :8 (shape check), :135 (Leaks), :190-192 (Before targets stated limit), :231 (Layout),
  :267, :280-281 (Coverage), :346-347, :386 (Attempt record), :412 (Facts), :415-416 (Case, Skill load, Before
  targets, Final JSON), :446-447 (Skill load), :452 (tracker: scripts/pi-role --help, its owner), :467-469 (Before
  targets, Facts), :476-477 (Before targets), :581 (by section), :613 (Leaks), :614 (Case, Facts), :649 (Judgment
  suite, Bench), :686, :694, :696, :735, :758-759 (Bench; three wrongly pointed at octo-feather-qa --help), :771
  (Judgment suite).
- scripts/check-evals: constants :26 (Field lines), :30 (Before targets), :31 (Case), :35, :39 (Judgment suite),
  :40-42 (Calibration), :43, :45, :47 (Judgment model and classifiers), :48 (Suite); docstrings :193 (Suite), :330
  (Judgment suite), :410 (Case), :459, :478 (Coverage).
- scripts/octo-feather-qa: --help :19-20 (Before targets), :22-24 (Attempt record), :29-30 (Facts), :61-62 (Bench);
  comments/docstrings :86, :178-179, :367, :440 (Before targets), :109-111 (Attempt record), :132, :142-143, :153-154,
  :338-340 (Skill load), :510 (Branch paths), :743-748, :761-762 (bench extension source comment), :814-815, :860,
  :875-876, :1016 (Bench), :847 (Judgment model and classifiers).
- scripts/octo-feather-qc-sandbox:358 (Attempt record).
- evals/judgment-*/suite.json (4) descriptions (Bench); evals/skill-triggers/suite.json (Coverage, Facts);
  evals/role-transcripts/suite.json (dropped the skill_read_before restatement; Facts pointer kept).

## Read and kept (pointer, setup, mechanism, or another owner's rule)

- Already pointing: tests/qa.sh :373-374, :395, :419, :537, :670, :746, :749, :806, :821, :837, :842; check-evals
  :68, :202, :217, :279, :298, :446, :556; octo-feather-qa :171, :198, :223, :237, :270-272, :315, :386-387, :472, :537,
  :698, :851-870; evals/isolation, evals/ladder (Field lines owner: code-review skill).
- Test setup naming fields: tests/qa.sh stub comments :29-48, :55, :110, :120, :142, :160, :436, :442, :658, :667,
  :717; tests/lane-judge.sh (judge comment format, spec judgment#rule-calibration, not a schema rule).
- Other owners: octo-feather-qa --help run bounds, defaults, --sample, score lines (its usage); octo-feather-lane
  judge help and calibration() (spec judgment#rule-calibration, #rule-advisory); scripts/pi-role ({tracker});
  qc-sandbox header and recorder comments (the sandbox's own mechanism; its "what counts" already points).
- Error text and assertion literals (behaviour, unchanged): check-evals messages, BEST_RULE, lane's
  "(shape: scripts/check-evals --help)" refusal text.
- Out of write scope, judged: .agents/skills/eval-cases/SKILL.md (points by section; :42 "target never reached"
  cites Before targets where the rule sits under Facts); justfile:221 (loose summary of check-evals); AGENTS.md:28
  (points to check-evals --help, which points to schema.md); docs/owed-evals/* (dated records). Reported to the
  supervisor, not changed.

## Validation

- Diff is comment, docstring, help and description only (`git diff -U0 scripts/` non-comment lines: none).
- `just check`: ok. `bash tests/qa.sh`: qa: ok.
