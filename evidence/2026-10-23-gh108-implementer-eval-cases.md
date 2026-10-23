# Implementer loads eval-cases before editing a skill, a role or an eval case (#108, lane gh108)

Owner boundary ruling (#120, director relay): whoever changes a kit instruction as the work item owes its eval case, the implementer included when an accepted kit spec asks for a new or changed skill or role (spec: skills#local-eval-cases, quality#quality-eval-authoring at 4e7c6ae). agents/implementer.md now lists `eval-cases` and has one Rules line: "Load `eval-cases` before editing a skill, a role or an eval case when the ticket adds or changes one: that change owes its eval case (docs/adr/0008)."

Smoke: agents/implementer.md (role-transcripts implementer-skill-ticket, then the 4 implementer/eval-cases trigger cases, below)
Removed: nothing removed; reason: owner boundary ruling #120 (implementers now write the eval case a skill or role change owes).

## Case

`evals/role-transcripts` `implementer-skill-ticket`: fixture python-app-skill (its repo skill `.agents/skills/changelog/SKILL.md`), ticket T4 asks the changelog skill to gain a user-facing-wording rule (criterion changelog-user-facing). Fact: `skill_read_before eval-cases kit_contract_edit` (the rule as owned: before editing a skill). The task names neither eval-cases nor any fact.

## Live runs (one at a time)

Smoke, head (worktree on 4e7c6ae plus this change): run `20261023T164001Z-c8265b`
- PASS: eval-cases read at tool call 3 of 4, before first kit_contract_edit at call 4 (`edit .agents/skills/changelog/SKILL.md`), 25 s.

Fails before, `--kit-ref 9ba7c51`: run `20261023T164039Z-3b0df4`
- FAIL: first kit_contract_edit at call 3 of 3 (`edit .agents/skills/changelog/SKILL.md`), no load of eval-cases. Note: eval-cases does not exist at 9ba7c51.

Fails before, `--kit-ref 4e7c6ae` (eval-cases skill present, implementer.md without it; isolates the role line): run `20261023T164100Z-7b9001`
- FAIL: same, edit at call 3 of 3, no load of eval-cases.

Trigger cases (skill-triggers, implementer/eval-cases), each run once alone; train 2/2, held-out 2/2:
- PASS impl-evalcases-skill-sections (train, should): eval-cases read at call 3 of 3. Run `20261023T164119Z-0e7a30`.
- PASS impl-evalcases-new-repo-skill (held-out, should): read at call 4 of 4 (bash cat). Run `20261023T164127Z-671322`.
- PASS impl-evalcases-near-read-skill (train, near miss: read a skill's rules, change nothing): not read in 1 call. Run `20261023T164152Z-cd86fb`.
- PASS impl-evalcases-near-use-skill (held-out, near miss: write a CHANGELOG entry the skill governs, skill unchanged): not read in 8 calls. Run `20261023T164202Z-5ef8ba`.

Head, committed (demo, kit 2b45ab6): `scripts/octo-feather-qa --suite role-transcripts --case implementer-skill-ticket`, run `20261023T165507Z-99843b`
- PASS: eval-cases read at call 4 of 6, before first kit_contract_edit at call 6 (`edit .agents/skills/changelog/SKILL.md`), 21 s.

## Regression: implementer-python-ticket (no skill or role in the ticket)

- Head 2b45ab6, run `20261023T165533Z-56126a`: FAIL, principle-prove-it-works never read before the commit at call 20 (other 5 facts pass). eval-cases not read.
- Head 2b45ab6 again, run `20261023T165800Z-bd5ab0`: PASS, all 6 facts; eval-cases not read.
- `--kit-ref 4e7c6ae`, run `20261023T165649Z-9d0768`: PASS.
- Finding: head 1/2, base 1/1 on one trial each; the miss is principle-prove-it-works, not eval-cases. Not separated from noise at this sample size; not tuned.
