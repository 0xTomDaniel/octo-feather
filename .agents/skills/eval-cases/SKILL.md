---
name: eval-cases
description: Writing the factory eval case that ships with a behaviour change. Use when you write or change a skill, a role file's contract or a skill patch and must prove it, or when you write an eval case for `just qa`.
---

# Eval cases

A Pi adaptation of the eval method in Anthropic's `skill-creator` (Apache-2.0, credited in the kit's NOTICE). A behaviour change to a skill, a role or a patch ships with a **case**: a task, a fixture and the **facts** a grader reads from the role's Pi transcript. A case is the proof the change works; prose about it is not.

## Where things live

- `evals/<suite>/suite.json` (`kind`: `skill-trigger` or `role-transcript`), `evals/<suite>/cases.json` (what the agent sees), `evals/<suite>/reference/expectations.json` (the facts, hidden from the agent), `evals/fixtures/<name>/` (a small repo copied and git-initialized per run).
- `scripts/check-evals --help` is the source of truth for the shape and the closed fact list; run `scripts/check-evals` after every edit (it runs in `just check`).
- `scripts/octo-feather-qa --help` runs cases (`just qa`), in the qc sandbox, one trial per case.

## 1. Trigger cases (does a role read a skill when, and only when, the task needs it)

For each role-skill pair, in the `skill-trigger` suite: at least 2 should-trigger and 2 should-not cases, `split` one of each `held-out`, the rest `train`.

- **Should-trigger** tasks need the skill without naming it, its path or its method words (a task that says "red-green-refactor" tests the word, not the description). Vary the phrasing: formal, casual, terse, with real file names and a little backstory. At most one explicit case.
- **Should-not** tasks are **near misses**: they share the skill's keywords or concepts but need something else. An obviously unrelated task ("write fibonacci") tests nothing.
- Substantive tasks only: a one-step task ("read file X") triggers no skill whatever the description says.
- Facts: `skill_read` (or `skill_read_before`) for should, `skill_not_read` for should-not.
- **Held-out** cases are never tuned against: write them before changing the description, never reword them after a run, and report their score apart from the train cases. A description tuned until every case passes fits the cases, not the role.

## 2. Role transcript cases (does the role do the thing)

`kind: role-transcript`. A fixture holding exactly what the task needs, a task as the role's real brief would phrase it, and facts from the closed list.

- The task leaks no graded fact: no skill path, no expectation JSON, no hint of what is counted (`check-evals` refuses the mechanical leaks; the rest is yours).
- The grade comes from what the role did (tool calls and their results), never its self-report.

## 3. Facts read structured data, never prose

Graders and checks read **structured** facts. Where a case needs a verdict (a reviewer's blocks, a pass/fail call, a corrector's chosen rung), the producer emits it as **data** and a fact reads the field:

- The `declared` fact: the role's final message holds exactly one fenced `json` block, e.g. `{"blocks": ["tests/test_cli.py::test_x"]}` or `{"rung": "check"}`, and the fact checks one top-level field against a fixed label list. If the role's contract does not yet ask for that block, the case's change adds it to the contract.
- Failure example, class **regex-judging-meaning**: #107's `grade-review.py` inferred "blocks" from the report's prose headings and the spelling of test names. It passed and failed on wording, not on the verdict.
- A fuzzy question no producer field can answer gets a **judgment**: run separately through Pi codemode `models.classify` with one closed question (on this box `openrouter/typesafe/jev-1.14` or `~jev-latest`), labelled a judgment in the result. Uncalibrated, it never gates a case until calibrated against owner labels. No judgment fact exists yet (issue #108 judgment-interface comment): every case grades structured producer facts.

A fact the closed list lacks is added in `scripts/check-evals` (shape) and graded in `scripts/octo-feather-qa`, with a stub-pi test in `tests/qa.sh`.

## 4. Fails before, passes after

Prove the case catches the change:

1. `scripts/octo-feather-qa --case ID --kit-ref BASE` (BASE: the commit before your change): FAIL.
2. `scripts/octo-feather-qa --case ID` at your head: PASS.

Smoke one case before a batch. Paste both result lines with the run id into `evidence/<date>-<lane>-<topic>.md`, with its `Smoke:` and `Removed:` lines (`scripts/check-behavior-smoke`).
