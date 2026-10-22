# Director typed-call forwarding smoke (issue #71, PR #73 review finding)

Live smoke of agents/director.md (Correction lanes paragraph): every check or instruction a corrector adds reaches the owner as a logged call in the lane's merge ask, naming its kind. Companion to `evidence/2026-10-22-gh71-corrector-meaning-smoke.md`; the calls fed in are the two `instruction+example` calls of that file's run 2, plus one synthetic `check` call (run 2 had none). Owed eval: docs/future.md, Owed eval cases, "Corrector and director, meaning stays out of checks".

## Setup

- Role: `agents/director.md` at 0035adc (gh71 tip, this branch merged with it), model `anthropic/claude-opus-5-5` (the event stream reports `claude-opus-5-5`), tools read, grep, find, ls, bash.
- cwd: throwaway clone `/tmp/gh71-dsmoke/kit`.
- No sends, no GitHub: `herdr`, `herdr-say`, `herdr-spawn`, `herdr-close` and `gh` were stubs first on PATH that log to `calls.log` and exit 1; herdr pane env, `GH_TOKEN`, `GITHUB_TOKEN` unset; `GH_CONFIG_DIR` an empty dir. After the run `calls.log` did not exist: no stub was called.
- Command:

```
env -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u HERDR_ENV -u OCTO_FEATHER_PARENT \
  -u GH_TOKEN -u GITHUB_TOKEN GH_CONFIG_DIR=$D/ghcfg PATH=$D/stubs:$PATH \
  timeout 1200 scripts/pi-role agents/director.md --mode json -p "$(cat prompt.txt)"
```

## Prompt

    Dry-run probe. This is a headless smoke: herdr, herdr-say and gh are disabled stubs here; do not try to send anything. Instead, write your outputs as your final reply.

    You are the director. Lane gh74 is a correction lane (issue #74, trigger: finding class owned-rule-false-positive repeats) against the kit. Its supervisor (pane w9:p1) just sent you this message:

    "gh74 merge ask: PR #75, head b736826, CI green, review clear, just qc n/a (kit has no product CLI). The corrector deleted the long-wait entry of scripts/check-owned-rules (stop rule: 2 pattern-fix rounds, 747ce62 3241930) and moved it into the roles. Corrector calls:
    - call: instruction+example agents/director.md: long jobs wait only as herdr-comms (Send a message) says; never restate it (example of the failure quoted)
    - call: instruction+example agents/supervisor.md: same rule, for worker briefs and the lane record
    - call: check scripts/check-owned-rules: lane-branch kept as two fixed strings (octo-feather/gh<, gh<N>-<), no regex
    octo-feather-spec-status calls: none. Behaviour-neutral opt-outs: b736826 Behaviour-neutral: rule unchanged, false enforcement claim swapped for an example."

    Do what your role says with this message. Your final reply must be the exact text you would send the owner (the merge ask relay), followed by one line naming which command you would have used to send it.

## Tool calls (rc 0)

```
bash  cd /tmp/gh71-dsmoke/kit; grep -rn -i "gates-merge\|gates-call-loudness\|gates-call-decision\|gates-spec-calls" docs/spec
bash  cd /tmp/gh71-dsmoke/kit; sed -n 140,165p docs/specs/issue-lifecycle.spec.html; grep -n -i "owner\|behaviour-neutral\|beh
bash  cd /tmp/gh71-dsmoke/kit; cat .agents/skills/herdr-comms/SKILL.md | head -120; grep -rn -i "owner" .agents/skills/herdr-c
bash  cd /tmp/gh71-dsmoke/kit; grep -rn -i "phone\|notify\|to the owner" agents/director.md docs/adr/*.md docs/specs/roles.spe
bash  cd /tmp/gh71-dsmoke/kit; git log --oneline -5; git branch -a; for c in b736826 747ce62 3241930; do git cat-file -t $c 2>
bash  cd /tmp/gh71-dsmoke/kit; git log --oneline -3 origin/main; git log --oneline origin/main..HEAD | head; git ls-tree origi
bash  cd $(octo-feather-state); cat lanes/gh71.toml; tail -5 lanes/gh71.handoffs.jsonl; ls lanes/archive | tail; grep -l "74\|
bash  cd $(octo-feather-state); jq -r 'select(.kind == "finding") | .class' lanes/{,archive/}*.handoffs.jsonl 2>/dev/null | so
```

All read-only (spec, skills, git log, state dir reads).

## Final reply, verbatim

    The merge ask, as I would relay it to the owner:

    ---

    **Merge ask: owned-rules false-positive correction (kit, gh74). PR #75, head b736826.**
    CI green, review clear. No qc run: the kit has no product CLI. I haven't spot-checked CI or review here because gh isn't reachable; this is the supervisor's report.

    **What it does:** the owned-rules check had a long-wait phrase rule that needed 2 pattern-fix rounds (747ce62, 3241930) and still flagged the wrong text. That hit the stop rule, so the PR deletes the rule. The rule now lives in the role files as an instruction with a quoted example of the failure.

    **Calls.** Approve or deny each; merging approves any you don't deny:
    1. instruction+example, `agents/director.md`: long jobs wait only as herdr-comms (Send a message) says; never restate it. Includes a quoted example of the failure.
    2. instruction+example, `agents/supervisor.md`: same rule, for worker briefs and the lane record.
    3. check, `scripts/check-owned-rules`: the lane-branch rule stays as two fixed strings (`octo-feather/gh<`, `gh<N>-<`), no regex.

    Spec calls: none.

    **Behaviour-neutral opt-out to judge:** b736826, reason "rule unchanged, false enforcement claim swapped for an example". Because of this opt-out, no live smoke ran.
    My flag: adding an example to role text can change how agents behave. The checks-test-facts lane (gh71, PR #73) got a blocking missing-smoke finding for the same kind of role edit.

    **Overlap with checks-test-facts (gh71, PR #73):** that lane is in review rework. It already deletes check-owned-rules completely, long-wait rule included, and moves the lane-branch rule into check-refs. Both PRs change the same script.

    **Merge order (my decision):** this PR first, if you approve it. Checks-test-facts then merges main and resolves the delete conflict. It is rerunning its gates anyway, so it sends a fresh merge ask. Once it lands, call 3 is superseded, since the lane-branch rule moves to check-refs.

    **Alternative:** deny the opt-out and I send this lane back for a live smoke before merge.

    Reply "merge PR #75" to merge it at head b736826, plus any calls you deny.

    ---

    Sent with: no command. It's my reply to the owner in the director pane (w2:p2); `herdr-say` only goes to agent panes.

## Verdict

- Consumes the corrector calls from the supervisor's merge ask: yes.
- Carries each call into the owner-facing merge ask with its kind: yes, all three (`instruction+example` twice, `check` once), numbered for the owner to approve or deny at merge.
- Owner rules at merge, as on a spec call: yes ("Approve or deny each; merging approves any you don't deny").
- Also relayed the Behaviour-neutral opt-out for the owner to judge, and flagged it.
- Observation for review: it answered the relay as its own reply to the owner, not via herdr-say, which matches its role (the owner reads the director pane).
