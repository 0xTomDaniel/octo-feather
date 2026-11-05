# gh503: the written rules follow the gate's tiers (T6, #537)

Change: every place a worker or supervisor reads the gate rule points at its owner instead of restating "one gate, `just check`": the hand-off gate at quality spec `#acceptance-gate-green`, the tiers at quality spec `#recipes-table` (templates spec `#tpl-gate`, `#tpl-hooks`), when a lane runs the full tier at issue-lifecycle spec `#lanes-checkpoints`, the final full gate's capture at quality spec `#qc-capture`. Sites: AGENTS.md (kit Rules and Layout), templates/python/AGENTS.md and templates/typescript/AGENTS.md Rules, agents/implementer.md (offline gate, Output), agents/corrector.md (commit rule), agents/supervisor.md (Authority order, brief VERIFY field, merge-ask self-check), the implement skill (patch and materialized), implement-spec steps 4, 5, 7 (patch and materialized).

Smoke: agents/implementer.md .agents/skills/implement/ .skillfile/patches/skills/implement/ (case implementer-hands-off-on-fast, run below)
Smoke: agents/corrector.md agents/supervisor.md .agents/skills/implement-spec/ .skillfile/patches/skills/implement-spec/ (pointer edits; no case yet, owed in docs/owed-evals/503.md)
Removed: "`just check` once at the end" (implement), "a red `just check`" and "`just check` is green" (implement-spec steps 5, 7), "`just check` green" (corrector), "`just check` plus exact commands" (supervisor brief VERIFY), "one gate command, `just check`, used identically by agents, git hooks and CI" (kit AGENTS.md): each restated the one-gate rule the owner ruling of 2026-11-04 (issue #503) replaced with two tiers.

## The case

evals/role-transcripts `implementer-hands-off-on-fast`: an implementer on fixture `python-app-tiers` (python-app with `just fast` beside `just check`, an `e2e` marker, the template's pre-change AGENTS.md gate line, no git hook so no hook run of `just fast` is counted) gets a lane ticket; graded `{"fact": "ran", "program": "just", "args": ["fast"]}`. Static shape: `scripts/check-evals` ok.

## Runs

Pending: the qa slot (director). Before: `--kit-ref 15923eb` (or `--baseline 15923eb`); after: this branch's head.
