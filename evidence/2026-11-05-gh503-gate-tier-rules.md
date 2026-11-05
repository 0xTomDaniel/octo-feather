# gh503: the written rules follow the gate's tiers (T6, #537)

Change: every place a worker or supervisor reads the gate rule points at its owner instead of restating "one gate, `just check`": the hand-off gate at quality spec `#acceptance-gate-green`, the tiers at quality spec `#recipes-table` (templates spec `#tpl-gate`, `#tpl-hooks`), when a lane runs the full tier at issue-lifecycle spec `#lanes-checkpoints`, the final full gate's capture at quality spec `#qc-capture`. Sites: AGENTS.md (kit Rules and Layout), templates/python/AGENTS.md and templates/typescript/AGENTS.md Rules, agents/implementer.md (offline gate, Output), agents/corrector.md (commit rule), agents/supervisor.md (Authority order, brief VERIFY field, merge-ask self-check), the implement skill (patch and materialized), implement-spec steps 4, 5, 7 (patch and materialized); widened: the kit justfile and both template justfile headers, the python and typescript skills (local, not vendored).

Smoke: agents/implementer.md .agents/skills/implement/ .skillfile/patches/skills/implement/ (case implementer-hands-off-on-fast, run below)
Smoke: agents/corrector.md agents/supervisor.md .agents/skills/implement-spec/ .skillfile/patches/skills/implement-spec/ (pointer edits; no case yet, owed in docs/owed-evals/503.md)
Smoke: .agents/skills/python/SKILL.md .agents/skills/typescript/SKILL.md (pointer edits, scope widened by the supervisor; the run below names whether its implementer loaded python)
Removed: "`just check` once at the end" (implement), "a red `just check`" and "`just check` is green" (implement-spec steps 5, 7), "`just check` green" (corrector), "`just check` plus exact commands" (supervisor brief VERIFY), "one gate command, `just check`, used identically by agents, git hooks and CI" (kit AGENTS.md), "`just check` is the one gate" (kit justfile:1), "CI runs `just check`, the full tier; agents and .githooks/pre-commit run `just fast`" (both template justfile headers), "`just check` runs them all" (python skill), "The gate is the repo's `just check` ... Run it after a completed development slice and before reporting" (typescript skill): each restated the one-gate rule the owner ruling of 2026-11-04 (issue #503) replaced with two tiers.

## The case

evals/role-transcripts `implementer-hands-off-on-fast`: an implementer on fixture `python-app-tiers` (python-app with `just fast` beside `just check`, an `e2e` marker, the template's pre-change AGENTS.md gate line, no git hook so no hook run of `just fast` is counted) gets a lane ticket; graded `{"fact": "ran", "program": "just", "args": ["fast"]}`. Static shape: `scripts/check-evals` ok.

## Runs

### Smoke 1: run 20261105T032428Z-57dbce (both sides FAIL)

`scripts/octo-feather-qa --case implementer-hands-off-on-fast --runs 1 --baseline 15923eb`, current kit c994fe5. Wall 148 s, exit 1.

```
  baseline FAIL role-transcripts/implementer-hands-off-on-fast: 0/1 runs passed (pass rate 0.00, stddev 0.00); run 1: ran just fast: no run of just with these arguments in the sandbox's record (3 entries; runs of just: just check (exit 1); just check (exit 0); just check (exit 0)) [61.0 s] [kit 15923eb974571e3cd2342deb8a18430a67d8885d]
FAIL role-transcripts/implementer-hands-off-on-fast: 0/1 runs passed (pass rate 0.00, stddev 0.00); run 1: ran just fast: no run of just with these arguments in the sandbox's record (2 entries; runs of just: just check (exit 1); just check (exit 0)) [86.2 s] [kit c994fe57a3588ba2ba6eda52f2953dfdfbf5651f]
qa: analysis: non-discriminating case role-transcripts/implementer-hands-off-on-fast: every run on both kits failed
```

Diagnosis (current/run-1 transcript): the implementer read the implement skill in full (not truncated), along with tdd, python, principle-prove-it-works, blast-radius, commit and code-review. It never opened the quality spec. During the loop it ran `pytest -m "not e2e"`, then ran `just check` at the end and reported "The full gate (just check) passes". At c994fe5 the implement line read "the target's hand-off gate once at the end (`just fast`; which tier: quality spec `#acceptance-gate-green`)". The agent took "hand-off gate" to mean the full gate. A pointer alone did not carry the behaviour: in a target, the kit's spec is out of the agent's sight in practice.

Fix (supervisor-approved wording, the next commit): the implement line names the command and keeps the conditions at the owner: "`just fast` once at the end; report when it is green (the hand-off gate: quality spec `#acceptance-gate-green`, which also covers a target with no fast recipe)."

### Smoke 2

Pending: the next eval slot (director).
