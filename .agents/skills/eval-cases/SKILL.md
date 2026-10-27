---
name: eval-cases
description: Writing the factory eval case that ships with a behaviour change. Use when you write or change a skill, a role file's contract or a skill patch and must prove it, or when you write an eval case for `just qa`.
---

# Eval cases

A Pi adaptation of the eval method in Anthropic's `skill-creator` (Apache-2.0, credited in the kit's NOTICE). A behaviour change to a skill, a role or a patch ships with a **case**: a task, a fixture and the **facts** a grader reads from the role's Pi transcript. A case is the proof the change works; prose about it is not.

## Where things live

- `evals/<suite>/suite.json`, `evals/<suite>/cases.json` (what the agent sees), `evals/<suite>/reference/expectations.json` (the facts, hidden from the agent), `evals/fixtures/<name>/` (a small repo copied and committed on main per run).
- [`references/schema.md`](references/schema.md) (below: schema, by section) owns every eval and bench schema and policy: suite, case and setup fields, the closed fact list and how each fact is graded, judgment suites, calibration, `classifiers.json` and the bench's ranking, threshold and FAIL rule. Read it before writing or changing a case; run `scripts/check-evals` after every edit (it runs in `just check`).
- `scripts/octo-feather-qa --help` runs cases (`just qa`), in the qc sandbox, one trial per case.

## 0. Test the rule as owned

A case tests the rule as its **owner** file states it (the role file, the skill), never a stricter one. Copy the rule's own condition into the fact: "`writing-for-agents` before editing a role, skill or patch" (agents/corrector.md) is `skill_read_before writing-for-agents kit_contract_edit`, not `... edit`. Example, lane gh108: `corrector-repeated-class` graded writing-for-agents before *any* edit, failed when the corrector's first edit was a ruff rule in `pyproject.toml`, and was aligned to the owned rule (fact dropped there: that fix touches no role, skill or patch); `corrector-repo-skill-rule` grades it on a fix that must edit a skill. If the rule itself is wrong, change the owner file in its own change, then the case.

## 1. Trigger cases (does a role read a skill when, and only when, the task needs it)

`kind: skill-trigger`. The kit suite has `"covers": "role-skills"` (schema: Coverage): add a skill to a role, add its four cases.

- **Should-trigger** tasks need the skill without naming it, its path or its method words (a task that says "red-green-refactor" tests the word, not the description). Vary the phrasing: formal, casual, terse, with real file names and a little backstory. At most one explicit case.
- **Should-not** tasks are **near misses**: they share the skill's keywords or concepts but need something else. An obviously unrelated task ("write fibonacci") tests nothing.
- Substantive tasks only: a one-step task ("read file X") triggers no skill whatever the description says.
- **Held-out** cases are never tuned against: write them before changing the description, never reword them after a run, and report their score apart from the train cases. A description tuned until every case passes fits the cases, not the role.

## 2. Role transcript cases (does the role do the thing)

`kind: role-transcript`. A fixture holding exactly what the task needs, a task as the role's real brief would phrase it, and facts from the closed list.

- Repo setup (`branch`, `head`, `origin`, `fake_gh`) and `{repo}`, `{head}` in the task: schema, Case.
- The task leaks no graded fact: no hint of what is counted (`check-evals` refuses the mechanical leaks, schema: Leaks; the rest is yours).
- The grade comes from what the role did (tool calls and their results), never its self-report.

## 3. What a fact reads

Each fact, its parameters and exactly what it reads: schema, Facts. Writing a case against them:

- A skill read is a **load** (schema: Skill load), never a mention.
- A target never reached fails its `skill_read_before` (schema: Facts): write the task so the role reaches it, and list such a FAIL as a finding, never weaken the case.
- **Verdicts as data** (schema: Final JSON), e.g. `{"rung": "check"}`, a reviewer's `{"blocking": [{"test": "tests/test_cli.py::test_x"}]}`, a qc judge's `{"criteria": [{"id": "x", "verdict": "pass"}]}`. If the role's contract does not yet ask for that block, the case's change adds it to the contract.
- Why a fact reads a declared field and never prose, and what a judgment may gate: docs/adr/0008 (rung 2 exact check, rung 3 structured judgment, Who builds what). Who fixes what, where: docs/adr/0020 (Where the fix goes).
- No judgment fact exists yet (issue #108 judgment-interface comment): one would run separately through Pi codemode `models.classify` with one closed question and the kit's judgment model (`evals/judgment-model.json`), labelled a judgment in the result.

A fact or target the closed list lacks is added to the schema, refused in `scripts/check-evals` and graded in `scripts/octo-feather-qa`, with a stub-pi test in `tests/qa.sh`.

## 4. Fails before, passes after

Prove the case catches the change:

1. `scripts/octo-feather-qa --case ID --kit-ref BASE` (BASE: the commit before your change): FAIL.
2. `scripts/octo-feather-qa --case ID` at your head: PASS.

Smoke one case before a batch. Paste both result lines with the run id into `evidence/<date>-<lane>-<topic>.md`, with its `Smoke:` and `Removed:` lines (`scripts/check-behavior-smoke`).
