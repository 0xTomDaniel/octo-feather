# gh1266: the merge guard and the director's relay, in the role texts

Change: agents/supervisor.md merges a passing merge ask whose tier block reads `Waits for: nobody` itself,
sending nothing up first, and sends any other up, merging only on its relay; agents/director.md replies to an
ask waiting for the owner that it waits for him, naming its reasons, relays no merge until his merge, relays a
set-back ask in its own order, and records each relay with `octo-feather-lane relay` (spec issue-lifecycle
#gates-tier-relay, #gates-merge-guard). The guard itself: `octo-feather-lane --help`, merge and relay; its
tests: tests/gate/kit/lane_merge_guard.py.

Smoke: agents/director.md, headless director run (pi-role agents/director.md -p) at 5a22bd59 plus this lane's uncommitted role edits, started 20261124T224656Z, exit 0: a tier 3 ask, it replied that the ask waits for the owner naming its reason, relayed nothing, and named the relay command for after the owner's merge.
Smoke: agents/supervisor.md, headless supervisor run (pi-role agents/supervisor.md -p) at the same tree, started 20261124T224718Z, exit 0: a tier 1 ask waiting for nobody, it sends nothing up and names `octo-feather-lane merge 33 <head>` next.

Removed: the supervisor sending every passing merge ask to the director (agents/supervisor.md); the merge command's "adding no merge policy" (octo-feather-lane --help, merge).

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
