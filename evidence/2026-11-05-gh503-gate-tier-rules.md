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

### Smoke 2: run 20261105T032810Z-7e85a8 (both sides FAIL, fixture defect)

Same command, current kit 114f682. Wall 146 s, exit 1. The baseline side recorded `just check (exit 1)`; the current side recorded `just check (exit 1)`. The analysis flags the case as non-discriminating.

Diagnosis: in the sandbox, `just` and `uv` on PATH are mise shims, and the fixture had no mise config, so each shim refused with `mise ERROR No version is set for shim`. The `ran` shim runs the next `just` on PATH, which is that mise shim, so every recorded run of `just` exits 1. Both agents then worked around it by absolute path, which the Run record cannot see (schema, Run record, stated limit):
- current (114f682): `/usr/bin/just check` exit 0, then `/usr/bin/just fast` exit 0. The new line did lead it to run `just fast`, but the run went unrecorded.
- baseline (15923eb): `~/.local/share/mise/installs/just/1.21.0/just check` only. It never ran `just fast`.

Fix: the fixture gets a `mise.toml` pinning uv 0.13.1 and just 1.21.0, as templates/python's does. Checked by hand on a copy: `mise which just` and `mise which uv` resolve, `just fast` and `just check` both exit 0.

## Held-out case

evals/role-transcripts `implementer-hands-off-on-fast-heldout`: a different target, fixture `tally-tiers` (a word-count CLI; tests in tests/integration and tests/e2e, as in the template; mise.toml; the template's pre-change gate line), and a different ticket (T3, `--lines`). It is graded on the same single fact, `ran just fast`. I wrote it after smoke 2 and before any run of it; it is never to be tuned on. The schema has no held-out mark for role-transcript cases (`split` is skill-trigger only: eval-cases schema, Case), so this file and the `-heldout` suffix of its id record that it is held out. Report it apart from the train case `implementer-hands-off-on-fast`.

### Smoke 3 (train only, after the mise.toml fix)

Run 20261105T033336Z-e103dd: `scripts/octo-feather-qa --case implementer-hands-off-on-fast --runs 1 --baseline 15923eb`, current kit d6639a0. Wall 85 s, exit 0. The sandbox's proof line shows that the fixture's mise config is now judged: `repo: just@1.21.0 uv@0.13.1`.

```
  baseline run 1/1: FAIL role-transcripts/implementer-hands-off-on-fast: ran just fast: no run of just with these arguments in the sandbox's record (1 entries; runs of just: just check (exit 0)) [stop: exit, 13 tool calls, 50.9 s] [kit 15923eb974571e3cd2342deb8a18430a67d8885d]
  current run 1/1: PASS role-transcripts/implementer-hands-off-on-fast: ran just fast: recorded run just fast (exit 0) [stop: decided, 14 tool calls, 33.3 s] [kit d6639a021505b6abb8b893c3123271072e659847]
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     50.9 +/- 0.0         33.3 +/- 0.0         -17.6
    tokens     219176 +/- 0         107784 +/- 0         -111392
    cost usd   0.2717 +/- 0.0000    0.1781 +/- 0.0000    -0.0936
qa: analysis: no flags
```

The case separates on one run per kit: the before kit runs only `just check`, the after kit runs `just fast`. The held-out case stays unrun until the proof.

## Findings

Filed as issue #575 (outside this lane).

- Schema gap (eval-cases schema, Case): `split` (`train` or `held-out`) exists only for skill-trigger cases, and `check-evals` refuses it on a role-transcript case. So a role-transcript held-out case cannot be marked as data, and `octo-feather-qa` cannot report it apart. Here it is held out by record (this file, the `-heldout` id suffix). The fix belongs to the schema owner: the schema, `scripts/check-evals` and `scripts/octo-feather-qa`, outside this ticket's scope.
- Fixture environment gap: the python-app fixture family (python-app and its copies: python-app-shout, -skill, -verify-*, -yaml-names, -proxy-check and others) has no `mise.toml`. In the qa sandbox, `just` and `uv` on PATH are mise shims that refuse with no version set (smoke 2 above), so any case there that runs `just` sees exit 1, and a `ran just ...` fact can be bypassed by an absolute path. Proven only for python-app-tiers (smoke 2); for the rest it is inferred from the same setup. Not fixed here (outside scope).

### Proof: run 20261105T033535Z-26e5e4 (NOT proven)

`scripts/octo-feather-qa --case implementer-hands-off-on-fast --case implementer-hands-off-on-fast-heldout --runs 3 --baseline 15923eb`, current kit dc85511. Wall 720 s, exit 1, one invocation.

| case | split (by record) | baseline 15923eb | current dc85511 |
|---|---|---|---|
| implementer-hands-off-on-fast | train | 0/3, pass rate 0.00 +/- 0.00 | 2/3, pass rate 0.67 +/- 0.58 |
| implementer-hands-off-on-fast-heldout | held-out | 0/3, pass rate 0.00 +/- 0.00 | 0/3, pass rate 0.00 +/- 0.00 |

```
qa: analysis:
  non-discriminating case role-transcripts/implementer-hands-off-on-fast-heldout: every run on both kits failed
  high variance role-transcripts/implementer-hands-off-on-fast: current kit pass rate 0.67 +/- 0.58
```

Current kit, from the transcripts:
- Held-out run 1 and run 3 never loaded the implement skill. Each ran `just check` once and reported "`just check` passes".
- Held-out run 2 loaded the implement skill in full and still ran only `just check`.
- Train run 1 loaded it and ran `just check`. Its report said "`just fast` is a subset of it": the agent chose the full tier as the safer gate.
- Train runs 2 and 3 ran `just fast`.

Reading: the implement skill line does not reliably change the hand-off. It fails when the skill is not loaded, and the agent overrides it when it judges the full tier safer. The held-out case is not tuned on and not rerun. Any further wording change needs a new held-out case.

## Option (a): the rule moves to the always-loaded role file (director ruling after proof 26e5e4)

Why: proof 26e5e4 showed the implement skill line misses when the skill is not loaded (held-out runs 1 and 3), and the agent overrides it when the full tier looks safer (train run 1: "`just fast` is a subset"). The ruling: one always-loaded site, tried once. If the new held-out case still does not separate, option (b): report the criterion unproven at the merge ask, with no further tuning.

Change:
- agents/implementer.md Rules (body only; frontmatter untouched) gains one line, a trigger plus pointers: "Hand off on green `just fast`; the full `just check` belongs to the lane's checkpoints, not your hand-off: quality spec `#acceptance-gate-green`, issue-lifecycle spec `#lanes-checkpoints`."
- Its Output parenthetical pointer is removed, so the file states this in one place.
- The implement skill line goes back to a plain pointer, so the rule is not stated twice: "the hand-off gate once at the end (quality spec `#acceptance-gate-green`)".

Smoke: agents/implementer.md .agents/skills/implement/ .skillfile/patches/skills/implement/ (the proof run below)
Removed: implement skill "`just fast` once at the end; report when it is green (... which also covers a target with no fast recipe)", now one site in agents/implementer.md; agents/implementer.md Output "(the gate a hand-off needs green: quality spec `#acceptance-gate-green`)".

Held-out cases: `implementer-hands-off-on-fast-heldout` (tally-tiers) is spent: it ran in proof 26e5e4 (0/3 on both kits) and is kept as a recorded, spent case, never tuned on. The new held-out case is `implementer-hands-off-on-fast-heldout-2`: a different target, fixture `slug-tiers` (a slug library and command; an e2e test marked by decorator in tests/test_installed.py; mise.toml; the template's pre-change gate line), and a different ticket (SLG-4, `--max N`). It is graded on the same single fact, `ran just fast`. It was written and committed before any run of it. Held out by record, as before (#575).

### Proof 2

Pending: the eval slot: train plus the new held-out, `--runs 3 --baseline 15923eb`.
