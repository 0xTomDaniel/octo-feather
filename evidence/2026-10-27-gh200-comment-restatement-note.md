# gh200: a restatement in a code or test comment is a note, not a block (ticket #238)

Change: where a restatement blocks and where it is a note, now owned by code-review skill step 4, `Owner:` paragraphs (patch + materialized; owner ruling 2026-10-27, #200). Cases: evals/ladder reviewer-comment-restatement-note (head fixture docs-rules-comment-restated) and reviewer-skill-restatement-blocks (head fixture docs-rules-skill-restated, guard), base fixture docs-rules-skill.

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch (code-reviewer runs below load the code-review skill at base 1d5bafb and head 303b51e)
Removed: the patch deleted "each blocks" for every restatement site (step 4 `Owner:` paragraphs): a comment or docstring restatement no longer blocks on its own. Incident: PR #174 took 4 review rounds on comment and docstring restatements with no functional issue; same class in #197, #158, #159, #162.

Base: 1d5bafb (`--kit-ref 1d5bafb`). One reviewer run per case per commit; single samples, no variance claim.

Runs (`scripts/octo-feather-qa --suite ladder --case <id>`, with `--kit-ref 1d5bafb` for base). Artifacts under the qa state dir, by run id.

Round 3, head 303b51e (the result):

1. reviewer-comment-restatement-note, base, run 20261027T192711Z-1ec514:
   `FAIL ladder/reviewer-comment-restatement-note: field_lines Verdict: no line with {"text": "clear"} in [{"text": "blocking"}] [stop: exit, 42 tool calls, 73.6 s] [kit 1d5bafb33b25a01fffa4022bd9419766247ef654]`
   Base blocked on the comment restatements (duplicated-rule).
2. reviewer-comment-restatement-note, head, run 20261027T192825Z-b4bdd5:
   `PASS ladder/reviewer-comment-restatement-note: field_lines Verdict: 1 line(s) [{"text": "clear"}]; holds {"text": "clear"}; field_lines Owner: 1 line(s) [{"path": "docs/adr/0002-list-numbers-notes.md", "rule": "list prefixes each note with its 1-based position, a period and a space", "restated": ["src/app.py", "tests/test_app.py"]}]; holds ... "src/app.py"; ... "tests/test_app.py" [stop: exit, 31 tool calls, 58.5 s] [kit 303b51eeec08ba2ee5681cfc019e5312e951f71b]`
   Verdict clear, Owner line still lists both comment sites.
3. reviewer-skill-restatement-blocks (guard), base, run 20261027T192924Z-dfe4bd:
   `PASS ladder/reviewer-skill-restatement-blocks: field_lines Verdict: 1 line(s) [{"text": "blocking"}]; holds {"text": "blocking"}; field_lines Owner: 1 line(s) [{"path": "docs/adr/0002-list-numbers-notes.md", "rule": "one-based numbering with period and space", "restated": [".agents/skills/notes-cli/SKILL.md", "src/app.py", "tests/test_app.py"]}]; holds ... ".agents/skills/notes-cli/SKILL.md" [stop: exit, 33 tool calls, 68.7 s] [kit 1d5bafb33b25a01fffa4022bd9419766247ef654]`
4. reviewer-skill-restatement-blocks (guard), head, run 20261027T193033Z-bd8fcb:
   `PASS ladder/reviewer-skill-restatement-blocks: field_lines Verdict: 1 line(s) [{"text": "blocking"}]; holds {"text": "blocking"}; field_lines Owner: 1 line(s) [{"path": "docs/adr/0002-list-numbers-notes.md", "rule": "list numbers each note from 1 with period and space", "restated": [".agents/skills/notes-cli/SKILL.md", "src/app.py", "tests/test_app.py"]}]; holds ... ".agents/skills/notes-cli/SKILL.md" [stop: exit, 31 tool calls, 76.2 s] [kit 303b51eeec08ba2ee5681cfc019e5312e951f71b]`
   A skill restatement still blocks at head: the scope did not widen. The guard passes at both commits, so it does not separate on its own.

Result: note case separates, base FAIL, head PASS; guard PASS at both.

Rounds 1 and 2 (fixtures before the re-cut), note case FAIL at head too:

- Round 1, head 6252f72: base run 20261027T183926Z-28a316 FAIL (Verdict blocking), head run 20261027T184100Z-47ad0d FAIL (Verdict blocking); guard PASS at base (20261027T184227Z-0b1a21) and head (20261027T184348Z-5c1a6c).
- Round 2, head e30d2fe: base run 20261027T190427Z-e3df5e FAIL, head run 20261027T190535Z-1c045b FAIL; guard PASS at base (20261027T190645Z-31eb40) and head (20261027T190802Z-98154f).
- In both head FAILs the reviewer already wrote the comment restatement as a non-blocking note, but blocked on unrelated gaps of the fixture's broad errors ADR ("every error names its fix"): an argparse usage error (round 1), then a directory named notes.json raising IsADirectoryError (round 2). The fixtures were re-cut to a narrow rule they implement fully (ADR 0002, `app list` numbers notes from 1), commit 303b51e; round 3 above is the result. Expectations unchanged across rounds; not a held-out case.
