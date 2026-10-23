---
name: eval-cases
description: Writing the factory eval case that ships with a behaviour change. Use when you write or change a skill, a role file's contract or a skill patch and must prove it, or when you write an eval case for `just qa`.
---

# Eval cases

A Pi adaptation of the eval method in Anthropic's `skill-creator` (Apache-2.0, credited in the kit's NOTICE). A behaviour change to a skill, a role or a patch ships with a **case**: a task, a fixture and the **facts** a grader reads from the role's Pi transcript. A case is the proof the change works; prose about it is not.

## Where things live

- `evals/<suite>/suite.json` (`kind`: `skill-trigger` or `role-transcript`), `evals/<suite>/cases.json` (what the agent sees), `evals/<suite>/reference/expectations.json` (the facts, hidden from the agent), `evals/fixtures/<name>/` (a small repo copied and committed on main per run).
- `scripts/check-evals --help` is the source of truth for the shape and the closed fact list; run `scripts/check-evals` after every edit (it runs in `just check`).
- `scripts/octo-feather-qa --help` runs cases (`just qa`), in the qc sandbox, one trial per case.

## 0. Test the rule as owned

A case tests the rule as its **owner** file states it (the role file, the skill), never a stricter one. Copy the rule's own condition into the fact: "`writing-for-agents` before editing a role, skill or patch" (agents/corrector.md) is `skill_read_before writing-for-agents kit_contract_edit`, not `... edit`. Example, lane gh108: `corrector-repeated-class` graded writing-for-agents before *any* edit, failed when the corrector's first edit was a ruff rule in `pyproject.toml`, and was aligned to the owned rule (fact dropped there: that fix touches no role, skill or patch); `corrector-repo-skill-rule` grades it on a fix that must edit a skill. If the rule itself is wrong, change the owner file in its own change, then the case.

## 1. Trigger cases (does a role read a skill when, and only when, the task needs it)

`kind: skill-trigger`, every case with `should_trigger` (bool) and `split` (`train` | `held-out`). The kit suite has `"covers": "role-skills"`: check-evals fails, naming role and skill, unless every skill each role lists (`skills:` in agents/<role>.md) has a should and a should-not case in train and in held-out. Add a skill to a role, add its four cases.

- **Should-trigger** tasks need the skill without naming it, its path or its method words (a task that says "red-green-refactor" tests the word, not the description). Vary the phrasing: formal, casual, terse, with real file names and a little backstory. At most one explicit case.
- **Should-not** tasks are **near misses**: they share the skill's keywords or concepts but need something else. An obviously unrelated task ("write fibonacci") tests nothing.
- Substantive tasks only: a one-step task ("read file X") triggers no skill whatever the description says.
- Facts: `skill_read` (or `skill_read_before`) for should, `skill_not_read` for should-not.
- **Held-out** cases are never tuned against: write them before changing the description, never reword them after a run, and report their score apart from the train cases. A description tuned until every case passes fits the cases, not the role.

## 2. Role transcript cases (does the role do the thing)

`kind: role-transcript`. A fixture holding exactly what the task needs, a task as the role's real brief would phrase it, and facts from the closed list.

- Repo setup fields: `branch` (cut from main, checked out), `head` (`{"fixture", "branch", "message"}`: a second fixture's tree committed over main on its branch), `origin: true` (a bare origin holding main, for `git push`), `fake_gh: true` (a fake gh first on PATH, logging each call). In the task, `{repo}` and `{head}` become the copy's path and HEAD sha.
- The task leaks no graded fact: no skill path, no expectation JSON, no hint of what is counted (`check-evals` refuses the mechanical leaks; the rest is yours).
- The grade comes from what the role did (tool calls and their results), never its self-report.

## 3. What a fact reads

- **Skill read** (a load): the skill's content entered the agent's context. A tool result, from any tool (a Pi `read`, a bash `cat`), holds the SKILL.md's full content as the kit under test holds it (head, or the `--kit-ref` commit), compared after normalizing only what the tool adds (CRLF, trailing newlines). A result Pi truncated never counts, nor an `ls`, a `grep` or a `head` of a part. No command text is read.
- **Before-targets** (`skill_read_before`'s `before`), decided from filesystem snapshots the watcher takes after each tool call, never from command text: `test_write` (a test path changed), `edit` (any file git does not ignore), `git_commit` (HEAD on a new commit), `git_push` (origin's refs; needs `origin`), `gh_call` (the fake gh ran; needs `fake_gh`), `kit_contract_edit` (a role, skill or patch changed, as agents/corrector.md words its rule: `agents/*.md`, `.agents/skills/**`, `.skillfile/patches/**`; `AGENTS.md` is an `edit` only), `final_message` (pi ended on its own with a final message). A target never reached fails the fact, read or not ("target never reached"): write the task so the role reaches it, and list such a FAIL as a finding, never weaken the case.
- **Verdicts as data**: `declared` (the final message's one fenced `json` block, a top-level field one of fixed labels, e.g. `{"rung": "check"}`) and `declared_includes` (that block's top-level list holds given objects, e.g. a reviewer's `{"blocking": [{"test": "tests/test_cli.py::test_x"}]}` or a qc judge's `{"criteria": [{"id": "x", "verdict": "pass"}]}`). The producer emits the block; the task names its shape. Both read only once pi exits on its own, so they never stop a run early. If the role's contract does not yet ask for that block, the case's change adds it to the contract.
- Failure example, class **regex-judging-meaning**: #107's `grade-review.py` inferred "blocks" from the report's prose headings and the spelling of test names. It passed and failed on wording, not on the verdict.
- A fuzzy question no producer field can answer gets a **judgment**: run separately through Pi codemode `models.classify` with one closed question (on this box `openrouter/typesafe/jev-1.14` or `~jev-latest`), labelled a judgment in the result. Uncalibrated, it never gates a case until calibrated against owner labels. No judgment fact exists yet (issue #108 judgment-interface comment): every case grades structured producer facts.

A fact or target the closed list lacks is added in `scripts/check-evals` (shape, `--help`) and graded in `scripts/octo-feather-qa`, with a stub-pi test in `tests/qa.sh`.

## 4. Fails before, passes after

Prove the case catches the change:

1. `scripts/octo-feather-qa --case ID --kit-ref BASE` (BASE: the commit before your change): FAIL.
2. `scripts/octo-feather-qa --case ID` at your head: PASS.

Smoke one case before a batch. Paste both result lines with the run id into `evidence/<date>-<lane>-<topic>.md`, with its `Smoke:` and `Removed:` lines (`scripts/check-behavior-smoke`).
