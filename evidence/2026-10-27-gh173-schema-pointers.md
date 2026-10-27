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

## Round 2 (supervisor widened scope)

- .agents/skills/eval-cases/SKILL.md:42: the never-reached pointer now cites schema Facts (was Before targets). Pointer
  only, no behaviour change, so no eval case owed.
- justfile:221: check-evals recipe comment keeps its purpose, rule summary replaced by a schema.md pointer.
- octo-feather-lane refusal literal left as is (supervisor ruling).

## Round 3 (delta review at 2b9fe6f: two missed forms)

Search: evidence/2026-10-27-gh173-schema-restatements.py, new FORMS pass (docstrings naming a data entry's keys; comments on a fact's decision timing), run on 2b9fe6f (before) and the worktree (after). Prints only hits without a schema pointer.

Changed: scripts/octo-feather-qa:861 (yes_no_skipped: keys now 'schema, Judgment model and classifiers'); tests/qa.sh:433 and :440 (skill_not_read's end-of-run decision now 'schema.md, Facts'; :440 a further hit of the same form). Comments only, no code token changed.

Kept, judged: key-set hits name other owners' shapes, not a schema.md entry: octo-feather-lane:49, :339 (code-review Report fields); octo-feather-qa:746, :1021-1022 (bench child command's stdout protocol), :1128 (score return shape); octo-feather-qc:110, qc-sandbox:37 (sandbox mechanism); docs/owed-evals/118.md (dated record). herdr-spawn.sh:99 is a dialog, not a fact.

### Before (2b9fe6f)

```
## Form: entry keys in a docstring  /\{[a-z_]+(, [a-z_]+)+\}/  10 hits, 10 without a schema pointer
docs/owed-evals/118.md:5: - Classifier judge (Pi codemode `models.classify`, `openrouter/typesafe/jev-1.13`, `jev-1.14`, `jev-latest`; working on the box since 2026-10-23, confidence uncalibrated): it gates nothing, runs only 
scripts/octo-feather-lane:49: "Check" {lines: [{path, rule, owner, reads, class}], none, errors} from the check field (errors:
scripts/octo-feather-lane:339: """(Owner lines as {path, rule, restated}, `Owners: none` given, why unusable) (code-review skill, Verdict step)."""
scripts/octo-feather-qa:746: stdout line {"bench": {available, benched, skipped, errors, rows}}, rows [model, case, choice, probabilities in label
scripts/octo-feather-qa:861: """The skipped classifiers classifiers.json lists yes/no only, each with its entry {ruling, error, evidence}."""
scripts/octo-feather-qa:1021: cases: [{id, state}], classifiers: [P/ID] or None}), no agent, within TMO seconds. Returns (bench, run, sandbox record,
scripts/octo-feather-qa:1022: problem): bench the command's {available, benched, skipped, errors, rows}, None with problem naming why. With OUT,
scripts/octo-feather-qa:1128: """{split: {passed, total}} over the cases that have a split; {} when none has one."""
scripts/octo-feather-qc:110: """Fetch this run's GitHub snapshot outside the sandbox; return {dir, line, repo, meta} or {off}."""
scripts/octo-feather-qc-sandbox:37: after the recorder's line {attempts, recorded, gh_misses, gh_miss_log}, each list whole (or {attempts_error} if it ended without one),
## Form: a fact's decision timing  /until the run|run ends|open to the end|stays open|decided (when|once)|end of the run/  4 hits, 3 without a schema pointer
tests/herdr-spawn.sh:99: 2c. The "did not clear" path (a non-Pi dialog that stays open) keeps the same
tests/qa.sh:433: stays open until the run ends
tests/qa.sh:440: fx: open to the end, so all 7 run
```

### After

```
## Form: entry keys in a docstring  /\{[a-z_]+(, [a-z_]+)+\}/  9 hits, 9 without a schema pointer
docs/owed-evals/118.md:5: - Classifier judge (Pi codemode `models.classify`, `openrouter/typesafe/jev-1.13`, `jev-1.14`, `jev-latest`; working on the box since 2026-10-23, confidence uncalibrated): it gates nothing, runs only 
scripts/octo-feather-lane:49: "Check" {lines: [{path, rule, owner, reads, class}], none, errors} from the check field (errors:
scripts/octo-feather-lane:339: """(Owner lines as {path, rule, restated}, `Owners: none` given, why unusable) (code-review skill, Verdict step)."""
scripts/octo-feather-qa:746: stdout line {"bench": {available, benched, skipped, errors, rows}}, rows [model, case, choice, probabilities in label
scripts/octo-feather-qa:1021: cases: [{id, state}], classifiers: [P/ID] or None}), no agent, within TMO seconds. Returns (bench, run, sandbox record,
scripts/octo-feather-qa:1022: problem): bench the command's {available, benched, skipped, errors, rows}, None with problem naming why. With OUT,
scripts/octo-feather-qa:1128: """{split: {passed, total}} over the cases that have a split; {} when none has one."""
scripts/octo-feather-qc:110: """Fetch this run's GitHub snapshot outside the sandbox; return {dir, line, repo, meta} or {off}."""
scripts/octo-feather-qc-sandbox:37: after the recorder's line {attempts, recorded, gh_misses, gh_miss_log}, each list whole (or {attempts_error} if it ended without one),
## Form: a fact's decision timing  /until the run|run ends|open to the end|stays open|decided (when|once)|end of the run/  2 hits, 1 without a schema pointer
tests/herdr-spawn.sh:99: 2c. The "did not clear" path (a non-Pi dialog that stays open) keeps the same
```
