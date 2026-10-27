# Director decides merge order by leverage; owner asks narrowed (correction lane #234)

Trigger: owner correction 2026-10-27 (issue #234): owner had to ask "so #201 is urgent?" and "how come I had to ask instead of you making the call?". Owed eval: docs/owed-evals/234.md.

## Evidence (finding lines, `$(octo-feather-state)/director.handoffs.jsonl`, all logged 2026-10-27)

- owner-caught-director-priority: #201 (fast gate, ~5 min vs 13-16 min, on its branch only) not pushed to merge first.
- owner-caught-stranded-unseen x2, owner-caught-waits-invisible, owner-caught-gate-speed, owner-caught-cost-claims, owner-caught-gate-absence: same class, the owner supplying what the director should have seen or decided. Lane logs (`lanes/{,archive/}*.handoffs.jsonl`) hold no finding of these classes.

## Level

- Rung 1 (structure): the facts the director lacked as one view (per-lane gate time, what each lane waits on, which open PR changes shared infra) belong to #137 (factory report); proposed there, not built here.
- Rung 2 (exact check): none; merge order by leverage is judgment, no exact rule.
- Rung 3 (structured judgment): the eval below grades a declared field; it does not discriminate (results), so it is owed, not in `just qa`.
- Rung 4 (prose), this change, agents/director.md Behavior: the owner-ask list set to the owner's ruling, and a merge-order-by-leverage instruction with the #234 failure example.

## Smoke

Isolated: `scripts/octo-feather-qa` (qc sandbox: live Herdr unreachable, herdr shim pinned to a scratch session, lane state masked, per-run scratch state dir, offline gh refusing every call, no credentials; proof lines printed per run, all `ok`). Main side via `--kit-ref 1d5bafb` (main's agents/director.md), branch side at the working tree. Case added temporarily to evals/role-transcripts (text below), then removed. Rerun: add the case and expectation below to evals/role-transcripts/cases.json and reference/expectations.json, then

```
OCTO_FEATHER_QA_DIR=$(mktemp -d) scripts/octo-feather-qa --case director-leverage-first --kit-ref 1d5bafb   # main
OCTO_FEATHER_QA_DIR=$(mktemp -d) scripts/octo-feather-qa --case director-leverage-first                     # branch
```

Results, 2026-10-27, director model anthropic/claude-opus-5-5:

| Variant | Side | Runs | PASS | FAIL |
|---|---|---|---|---|
| easy (lane reports side by side, "Every lane branch is cut from main") | main 1d5bafb | 1 | 1 | 0 |
| hard (text below: reports spread over time, supervisor says "No rush") | main 1d5bafb | 4 | 3 | 1 |
| hard | branch | 4 | 4 | 0 |

Run ids: easy main 20261027T165223Z-cf0816; hard main FAIL 20261027T165313Z-e061dc, hard main PASS 165440Z-fc9103, 165529Z-863e47, 165634Z-43ea53; hard branch PASS 165410Z-2f94e4, 165510Z-6adfba, 165600Z-e3d807, 165704Z-2b30b7.

Main's FAIL (`declared first: "gh210" is not one of ["gh201"]`): it put the finished lane first and told gh201's supervisor "Don't send the ask before gh210 merges". Branch run 165410Z: "**Merge order (my call):** I'm putting the gate tidy-up ahead of everything else... I've told its supervisor to send the merge ask the moment CI is green". No branch run asked the owner whether gh201 was urgent; no main run did either.

Verdict: the smoke does not show a reliable fail-before (main 3/4 PASS). A one-shot case whose json names the merge-order decision primes that decision; the live miss was the decision never raised across a long round. Acceptance item "main FAILS" not met; recorded, not tuned (docs/adr/0008 stop rule).

Case (hard variant):

```
{"id": "director-leverage-first", "role": "director", "fixture": "python-app", "task": <below>}
expectations: {"facts": [{"fact": "declared", "field": "first", "in": ["gh201"]}]}
```

```
Director round, target repo {repo}. Supervisor messages since your last round, oldest first:
- 09:02 gh190 "Projects view" (w3:p1): integrated ticket 2 of 4 on gh190, `just check` green (15m40s). Handing ticket 3 to the implementer.
- 09:10 gh210 "Audit log export" (w6:p1): still waiting on the owner's merge.
- 09:14 gh205 "Board filters" (w5:p1): ticket 1 handed off; implementer reports `just check` green (16m02s). 3 tickets left.
- 09:31 gh201 "Gate tidy-up" (w4:p1): reviewer clear, qc pass. Side note: with the check split into parallel jobs `just check` on gh201 now takes 5m10s. CI running. No rush on our side; I can send the merge ask whenever.
- 09:40 gh190 (w3:p1): ticket 3 implementer reports `just check` green (14m55s); integrating.
- 09:44 gh205 (w5:p1): ticket 2 started.
Owner, 09:45: "anything need me?"
Sandbox run: there is no Herdr, no octo-feather-state and no GitHub. Write each message you would send to a pane as a line `-> <pane>: <message>` in your final message, which is your reply to the owner. It ends with exactly one fenced json block and nothing else in json:
```json
{"first": "<the lane key whose merge goes first, or \"owner\" when that order is the owner's call, or \"none\" when no lane goes ahead of the others>"}
```
```

Smoke: agents/director.md
Removed: "QA evidence review", "promotion", "traffic shifts" from the director's "Ask the owner only for" list (owner ruling 2026-10-27, issue #234); incident: #234 owner-caught-director-priority.
