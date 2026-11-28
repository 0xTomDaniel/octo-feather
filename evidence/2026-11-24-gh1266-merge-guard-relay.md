# gh1266: the merge guard and the director's relay, in the role texts

Change: agents/supervisor.md merges a passing merge ask whose tier block reads `Waits for: nobody` itself,
sending nothing up first, and sends any other up, merging only on its relay; agents/director.md replies to an
ask waiting for the owner that it waits for him, naming its reasons, relays no merge until his merge, relays a
set-back ask in its own order, and records each relay with `octo-feather-lane relay` (spec issue-lifecycle
#gates-tier-relay, #gates-merge-guard). The guard itself: `octo-feather-lane --help`, merge and relay; its
tests: tests/gate/kit/lane_merge_guard.py.

Smoke: agents/director.md .agents/skills/github-pr/SKILL.md, headless director run (pi-role agents/director.md -p) at 945d331f plus this lane's uncommitted review-6 rework, started 20261125T043827Z, exit 0: a tier 3 ask gets the reply naming its reason and no relay; a set-back ask it decides to merge, it relays with `octo-feather-lane relay 40 bd4fccb637aa` then tells the supervisor, the how read from github-pr's Merge And Issue Sync (Rework, review round 6, below).
Smoke: agents/supervisor.md .agents/skills/github-pr/SKILL.md, headless supervisor run (pi-role agents/supervisor.md -p) at the same tree, started 20261125T043827Z, exit 0: after merge-ask passes it runs `octo-feather-lane merge 40 <head>` first, no message; on the refusal it sends the merge-ask section up with herdr-say --parent and reruns the merge on the relay, the how read from github-pr's Merge And Issue Sync.
Earlier smokes (round 1, below): director run started 20261124T224656Z, supervisor run 20261124T224718Z, both at 5a22bd59 plus that round's edits.

Removed: the supervisor sending every passing merge ask to the director (agents/supervisor.md); the merge command's "adding no merge policy" (octo-feather-lane --help, merge); review round 6: the relay command steps from agents/director.md and the supervisor's dispatch on `Waits for:` from agents/supervisor.md (both now in github-pr's Merge And Issue Sync, merge deciding itself), and director.md's restated carry rule.

Both runs had a scratch state dir (XDG_STATE_HOME=/tmp/gh1266smoke/xdg, its commit identity `smoke`) and no
route to any pane (-p); the briefs forbid every write, merge and relay.

## Director run

Brief (verbatim):

```
Smoke check, read-only. Do not edit any file, commit, spawn, close or message any agent or pane, run no merge and no relay command.
The supervisor of lane gh1255-1266-owner (pane zs1:p1) just sent you this merge ask for PR #36 of 0xTomDaniel/octo-feather-realcase:

## Merge ask

Head: d44992873d63
Built: none
Failed:
- demo#acceptance-c: repair ticket #99 (recorded case)

Tier: 3
- failed criterion demo#acceptance-c: repair ticket #99 (recorded case)
Waits for: the owner

From your role file only, answer in at most 6 lines:
1. The exact reply you send the supervisor (text only; do not send it).
2. Do you relay this merge now? If you ever relay it, the exact command you would run, and when.
3. Whom you take the ask to.
```

Result (stdout, verbatim):

```
1. Reply: "PR #36 at head d44992873d63 waits for the owner. Tier 3 reason: failed criterion demo#acceptance-c, repair ticket #99 (recorded case). I'm taking it to him and will relay no merge until he tells me to merge. Your ask gives no CI result; send it."
2. No, I don't relay now. I relay only after the owner explicitly tells me to merge PR #36, which accepts head d44992873d63. Then I run from my pane `octo-feather-lane relay 36 d44992873d63 --link <where his word is written>` and tell the supervisor (zs1:p1).
3. The owner. I tell him what's blocked (the failed acceptance-c criterion, which needs a repair ticket), what was tried and the options, naming the lane by what it does.
```

## Supervisor run

Brief (verbatim):

```
Smoke check, read-only. Do not edit any file, commit, spawn, close or message any agent or pane, and run no merge.
You supervise lane gh1255-1266-self, PR #33 of 0xTomDaniel/octo-feather-realcase. `octo-feather-lane merge-ask 33` just passed and printed, after its section:

Tier: 1
Waits for: nobody

From your role file only, answer in at most 4 lines:
1. Do you send this merge ask to the director first? yes or no, and why in one line.
2. The exact command you run next (do not run it).
```

Result (stdout, verbatim):

```
1. No. The tier block reads `Waits for: nobody`, so my role file says I merge it myself and send nothing up first.
2. `octo-feather-lane merge 33 <head>`. `<head>` is the commit the PR's `## Merge ask` section named; I haven't looked it up, since you asked me to answer from the role file only.
```

## The guard, live on the realcase

Each run from a scratch world (tests/gate/kit/lane_merge_guard.py's World: scratch state dir, lane record and
director.toml, scratch kit install, Herdr's stand-in), real gh recorded into
tests/gate/kit/testkit/recordings/merge-guard-1266.json: PR #36 (tier 3) and #34 (tier 1, waiting for the
director's order, #35 conflicting) refused, open; #36 refused at its fix 7f7e09c5147b against the relay of
d44992873d63, then merged at 16dc9236b3d0, the relay of 7f7e09c5147b carried over a clean merge of the base;
#39 (tier 2, a clarifying spec call, waiting for nobody) merged at 7c8fd62a66ad with no relay; #40 (tier 2,
waiting for the director's order, #41 conflicting) refused, then merged at bd4fccb637aa on the director's relay.
(#33 and #34 were merged on tier 1 asks before the tier 2 reasons of #1258 reached the branch.)

## Rework, review round 6 (2026-11-25)

Review https://github.com/0xTomDaniel/octo-feather/pull/1269#issuecomment-7146094294 blocked the mechanical relay
steps in agents/director.md and the supervisor's dispatch on `Waits for:` in agents/supervisor.md (ADR 0008,
Duties). The how moved to .agents/skills/github-pr/SKILL.md, Merge And Issue Sync; merge-ask's pass names
`next: octo-feather-lane merge <PR> <head>` on stderr, and merge's refusal names sending the merge-ask section up.
The roles keep the director's reply, the owner and the merge order, and name the skill.

Director brief (verbatim):

```
Smoke check, read-only. Do not edit any file, commit, spawn, close or message any agent or pane, and run no merge and no relay command.
Two merge asks reach you from supervisors.
(A) Lane gh1255-1266-owner (supervisor pane zs1:p1), PR #36 of 0xTomDaniel/octo-feather-realcase, head d44992873d63, its tier block:
Tier: 3
- failed criterion demo#acceptance-c: repair ticket #99 (recorded case)
Waits for: the owner
(B) Lane gh1255-1266-order2 (supervisor pane zs2:p1), PR #40, head bd4fccb637aa, its tier block:
Tier: 2
- spec call demo 2026-11-24T03:00:00Z clarifies acceptance-a
Waits for: the director's order (PR #41: its head conflicts with this head in app.py)
You decide B may merge now. Load the skills your role file names for this step, then answer in at most 8 lines:
1. Your exact reply to A's supervisor (text only; do not send it), and whether you relay A now.
2. For B: each exact command you would run, in order (do not run them).
3. Which file told you how to relay.
```

Director result (stdout, verbatim):

```
1. Reply to A's supervisor (zs1:p1), not sent: "PR #36 at d44992873d63 is Tier 3, so it waits for the owner. Reason: failed criterion demo#acceptance-c, repair ticket #99 (recorded case). I am taking it to the owner. Hold until I relay." I do not relay A now. A tier 3 ask waits for the owner's merge (spec `#gates-tier-relay`).
2. For B, run these two from the director pane, in this order:
   `octo-feather-lane relay 40 bd4fccb637aa`
   `herdr-say zs2:p1 "Relayed PR #40 at bd4fccb637aa. Run octo-feather-lane merge 40 bd4fccb637aa now. PR #41 rebases after."`
   After B merges, PR #41 has to merge main in, because its head conflicts with #40 in app.py.
3. `.agents/skills/github-pr/SKILL.md`, section "Merge And Issue Sync". The director role prompt points there and to spec `#gates-merge`. `octo-feather-lane` `relay` usage in `scripts/` confirms the relay syntax.

I loaded the `github-pr` and `herdr-comms` skills and ran nothing that changes state.
```

Supervisor brief (verbatim):

```
Smoke check, read-only. Do not edit any file, commit, spawn, close or message any agent or pane, and run no merge.
You supervise lane gh1255-1266-order2, PR #40 of 0xTomDaniel/octo-feather-realcase. `octo-feather-lane merge-ask 40 --status docs/specs/demo.status.json` just passed; its stdout ended with the tier block
Tier: 2
- spec call demo 2026-11-24T03:00:00Z clarifies acceptance-a
Waits for: the director's order (PR #41: its head conflicts with this head in app.py)
and its stderr said: next: octo-feather-lane merge 40 bd4fccb637aa804ac5b053e27e23287519920efa (it merges, or names whom the merge waits for)
Assume you then ran that merge and it refused: "its merge waits for the director's order (...), and no relay of its merge is on record (...): nothing merged, PR #40 stays open; send up the section `octo-feather-lane merge-ask 40` prints, as printed (herdr-say --parent), then rerun this merge once the director says it relayed it".
Load the skills your role file names for this step, then answer in at most 6 lines:
1. After merge-ask passed, what did you run first: a message to the director, or a command? Give it exactly.
2. After the refusal: what you send, to whom, with which command (do not send it).
3. What you do when the director says it relayed. 4. Which file told you.
```

Supervisor result (stdout, verbatim):

```
1. A command, with no message first: `octo-feather-lane merge 40 bd4fccb637aa804ac5b053e27e23287519920efa`. Once merge-ask passes, the merge decides whether it goes.
2. I would send the director the section merge-ask printed, word for word: the `Tier: 2` block with its spec-call line and `Waits for: the director's order (PR #41: its head conflicts with this head in app.py)`. Command: `herdr-say --parent "<that section>"`. Not sent. While I wait, the lane record's `waiting_on` is `"director"`.
3. When the director says it relayed, I set `waiting_on` back to `""` and rerun the same merge: `octo-feather-lane merge 40 bd4fccb637aa804ac5b053e27e23287519920efa`. If it merges, I tear down and run `octo-feather-lane archive`. If it refuses again, I do the fix it names and rerun.
4. `.agents/skills/github-pr/SKILL.md`, section "Merge And Issue Sync". My role file (Supervisor, Delivery) named it as the skill to load before the merge, and `herdr-comms` before any message. Both are loaded.
```
