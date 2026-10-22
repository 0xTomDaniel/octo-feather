# Corrector meaning smoke (issue #71, ticket #72)

Live smoke of the changed corrector (docs/adr/0008): `agents/corrector.md` (meaning question, calls with kind, stop rule, loads principle-encode-lessons-in-structure), the `correct` patch (question before the check rung) and the principle-encode-lessons-in-structure patch (model-invoked, ADR 0012). Owed eval: docs/owed-evals/71.md, "Corrector and director, meaning stays out of checks".

## Setup

- Kit: worktree `gh71-72` (role file and skills as on this branch).
- Target: throwaway clone at `/tmp/gh71-smoke`, branch `smoke` at 40942b2 (before this lane: `scripts/check-owned-rules` with all four phrase-list rules).
- Command, herdr env unset so it cannot message a pane:

```
env -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u HERDR_ENV -u OCTO_FEATHER_PARENT \
  timeout 1500 scripts/pi-role agents/corrector.md --mode json -p "$(cat prompt)"
```

- Prompt: finding class `owned-rule-false-positive` repeats; `scripts/check-owned-rules` is a phrase-list check over prose whose patterns needed three fix rounds (2026-10-19, 2026-10-20); fix the class with `correct`, only the long-wait rule, one commit, `just check-owned-rules` green, no herdr, reply in the run output.

## Run 1 (role before the explicit load line)

rc 0. principle-encode-lessons-in-structure was listed in `<available_skills>` (the ADR 0012 patch makes it model-visible) but the corrector never read it. It still deleted the long-wait rule (commit fe09f7e in the throwaway) and logged:

```
call: instruction+example agents/director.md: don't restate the long-wait rule, point to herdr-comms (Send a message); example "Never hold your turn in a sleep over a minute"
call: instruction+example agents/supervisor.md: same rule and example
call: check scripts/check-owned-rules: long-wait rule deleted (stop rule)
```

Fix: corrector.md now says to load principle-encode-lessons-in-structure with `correct`, before picking a level.

## Run 2 (role as committed)

rc 0. Tool calls, in order (from the json event stream):

```
read  .agents/skills/correct/SKILL.md
read  .agents/skills/principle-encode-lessons-in-structure/SKILL.md
bash  git log -- scripts/check-owned-rules ...
bash  cat scripts/check-owned-rules, tests/check-owned-rules.sh
bash  grep finding lines in $(octo-feather-state)/lanes/*.handoffs.jsonl
...
edit  agents/director.md, agents/supervisor.md
bash  just check-owned-rules && bash tests/check-owned-rules.sh
bash  git commit
```

Commit in the throwaway: b736826 `check-owned-rules: drop the long-wait entry; roles carry it as instruction+example (stop rule, class owned-rule-false-positive)` (4 files, +15 -38).

Reply excerpt:

```
- Level picked: an instruction with an example of the failure.
- Type or check: a script can't tell a restated wait rule from an ordinary process wait without
  reading meaning. That's exactly what failed twice, so under docs/adr/0008 it can't be a check.
- Stop rule: a check whose patterns needed another round of fixes gets deleted, not tuned again.

Calls:
- call: instruction+example agents/director.md: long jobs wait only as herdr-comms (Send a message) says; never restate it (example of the failure quoted)
- call: instruction+example agents/supervisor.md: same rule, for worker briefs and the lane record
```

## Verdict

- Loads principle-encode-lessons-in-structure and `correct` first: yes (run 2).
- Asks the meaning question before the check rung and picks instruction+example: yes, both runs.
- Stop rule: deletes the tuned check in the lane, never proposes a retuned pattern: yes, both runs.
- Each added instruction logged as a call naming its kind: yes, both runs.
- Observation for review: in run 2 the corrector marked its role-file commit `Behaviour-neutral` (it said so in the reply, so check-behavior-smoke would print it for the owner). The trailer rule is docs/adr/0008; this probe does not change it.
