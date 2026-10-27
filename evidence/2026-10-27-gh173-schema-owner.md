# gh173: the eval-cases skill owns every eval and bench schema (lane gh167)

Ticket #173. The 14 owner-gap rows of the #165 sweep (r07 to r16, r42, r47, r59, r60) and this lane's new data (classifiers.json, test_write, attempt_blocked) now have one owner: `.agents/skills/eval-cases/references/schema.md`. `scripts/check-evals --help` and `scripts/octo-feather-qa --help` keep usage and name its sections. No behaviour changed: only docstrings, comments and skill text.

## Demo

`evidence/gh173-schema-owner/demo.sh`, run from the kit root at this commit; output in `evidence/gh173-schema-owner/demo.txt` (exit 0).

- Both `--help` texts name `.agents/skills/eval-cases/references/schema.md` as the schema owner.
- A tmp copy of `evals/` passes (`evals: ok (8 suites, 273 cases)`), then 32 copies, each with one field broken, at least one per schema section (Suite, Case, Case setup, Facts, Before targets, Attempt record, Final JSON, Field lines, Branch paths, Leaks, Coverage, Judgment suite, Calibration, Judgment model, Classifiers): each exits 1 naming a field, and the script checks that field is stated in the schema (backticked or quoted). 0 misses.
- Every field name check-evals' error strings carry (55, from the code) grepped in the schema: all stated.

Smoke: .agents/skills/eval-cases/SKILL.md .agents/skills/eval-cases/references/schema.md: the demo above reads the schema the skill points to; `scripts/check-evals` on the kit: `evals: ok (8 suites, 273 cases)`, as before the change.
Smoke: .agents/skills/to-tickets/SKILL.md .skillfile/patches/skills/to-tickets/SKILL.md.patch: `just check-vendored` ok (18 skills equal pin plus patches); the pointed owner prints the ticket rules (`scripts/octo-feather-lane --help`, `ticket` section), and a draft ending on no demo, piped to `scripts/octo-feather-lane ticket -`, fails `class: layer-only-ticket` with its fix, exit 1.
Removed: to-tickets step 5's restatement of the ticket check's rules (criterion anchor, demo through the repo's own surface, the Expand-contract waiver), now a pointer to `octo-feather-lane --help`; the restatement had already drifted (no `rule: <rule> (<owner>)` alternative, no recipe exclusions). Also removed: check-evals' 150-line schema docstring and octo-feather-qa's restated fact and bench rules, and eval-cases section 3's fact definitions (its `test_write (a test path changed)` was the path proxy #170 replaced; its classifier example named `~jev-latest`, a listed moving alias).

## No behaviour change

Both scripts' ASTs, every docstring blanked (comments are not in the AST), compared between gh167 `fa322b2` and this change: `scripts/check-evals` identical, `scripts/octo-feather-qa` identical. The only reader of either docstring is its own `--help` (`print(__doc__)`); tests/check-gate-free.sh asserts `octo-feather-qa [--suite NAME]`, the unchanged first line. `just check` green twice.

## Not changed (out of this ticket's scope), still pointing at `check-evals --help`, which now names the owner

AGENTS.md:28, scripts/check-evals FIX message (runtime text: "check-evals --help lists the shape"), scripts/octo-feather-lane:631,659,662 (runtime messages), scripts/octo-feather-qc-sandbox:24,212,271,291 (comments), tests/qa.sh:367,407,659,724,811,827,832 (comments). Restatements left in files this ticket may not write: tests/qa.sh:795-796 (calibration schema), evals/role-transcripts/suite.json:4 and evals/isolation/suite.json:4 (fact semantics in descriptions).
