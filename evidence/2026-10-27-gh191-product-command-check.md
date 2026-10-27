# gh191: reviewer classifies a product command's refusal (ADR 0008 Who builds what)

Change: docs/adr/0008 "Who builds what", reviewer sentence corrected in place: exact vs proxy classifies every decision that passes or refuses from facts, product commands included (owner ruling 2026-10-26). code-review skill step 4 Report fields (patch + materialized): the Check paragraph points to that paragraph; `<path>` names a product command's decision file. Case: evals/ladder reviewer-product-command-check, head fixture evals/fixtures/python-app-config-check (`app config-check FILE`, refusal in src/app/cli.py, key reading in src/app/config.py; fixture `just check` green, 5 tests).

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch (code-reviewer runs below load the code-review skill at head d863f0d and 2e976c3)
Smoke: agents/code-reviewer.md (the code-reviewer role ran in every run below; its line 34 was pointed at docs/adr/0008 Who builds what after these runs, a wording-to-pointer change on the supervisor's ruling, no rerun)
Removed: agents/code-reviewer.md:34 and scripts/octo-feather-lane:39, :244 lost their narrower restatement ("every check" / "no check") of what a Check line classifies; each now points to docs/adr/0008 Who builds what.
Removed: nothing removed; incident class check-unclassified x2 (#159, #180): reviewers gave no Check line for a product command's fact-based refusal (owner ruling 2026-10-26).

Base: 218b43ce8b4f025f6ee238815169525886a8b589 (gh167 after #173). One reviewer run each, base run 1 doubling as the smoke.

Runs (`scripts/octo-feather-qa --suite ladder --case reviewer-product-command-check`, with `--kit-ref 218b43c...` for base):

1. Smoke, base, run 20261027T031603Z-6045dd, expectation then `src/app/config.py`:
   `FAIL ladder/reviewer-product-command-check: field_lines Check: no line with {"path": "src/app/config.py", "class": "exact"} in [] [stop: exit, 30 tool calls, 99.8 s] [kit 218b43ce8b4f025f6ee238815169525886a8b589]`
   Report ended `Verdict: clear` / `Checks: none`: the refusal went unclassified.
2. Head d863f0d, run 20261027T031749Z-96e505:
   `FAIL ... no line with {"path": "src/app/config.py", "class": "exact"} in [{"path": "src/app/cli.py", ... "reads": "parsed TOML top-level keys", "class": "exact"}]`
   Behaviour changed (exact Check line); the path was mine wrong: the exit-2 decision lives in src/app/cli.py, config.py only reads keys. Expectation aligned to src/app/cli.py (commit 2e976c3), as the skill's `<path>` wording says (the file holding its decision). Not a held-out case.
3. Head 2e976c3, run 20261027T032007Z-041a6c:
   `PASS ladder/reviewer-product-command-check: field_lines Check: 1 line(s) [{"path": "src/app/cli.py", "rule": "refuse TOML missing name or greeting, naming every missing key", "owner": "T7 config-keys", "reads": "parsed top-level TOML keys via app.config.missing_keys", "class": "exact"}]; holds {"path": "src/app/cli.py", "class": "exact"} [stop: exit, 31 tool calls, 134.1 s] [kit 2e976c341ecd27c7bff3d65699e30d58abc1aeb1]`
4. Base, final case, run 20261027T032226Z-47b744:
   `FAIL ladder/reviewer-product-command-check: field_lines Check: no line with {"path": "src/app/cli.py", "class": "exact"} in [{"path": "tests/test_cli.py", ... "class": "exact"}] [stop: exit, 33 tool calls, 134.1 s] [kit 218b43ce8b4f025f6ee238815169525886a8b589]`
   Base reviewer classified the test file, not the command.

Result: separates, base 0/2, head 1/1 on the final expectation. Single trials; no variance claim.

Blast radius (wider Check scope must not add Check lines where no decision refuses): head a877916, run 20261027T033818Z-1cf166:
`PASS ladder/reviewer-no-check: field_lines Check: `Checks: none` [stop: exit, 26 tool calls, 56.1 s] [kit a87791629672aed1b895d6983ae6a03a304490b4]`
