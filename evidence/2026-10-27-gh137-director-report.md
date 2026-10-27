# Director answers status from the factory report and logs owner-caught findings (lane gh137, ticket #251)

Trigger: owner ruling 2026-10-27 (issue #137): the director answers status from `octo-feather-lane report` and logs each thing the owner caught that the factory should have as a finding line. Rule owner: docs/specs/comms.spec.html `#report-what`, `#handoff-director-finding`, `#report-owner-caught`. Owed eval: docs/owed-evals/137.md.

## Evidence (finding lines, `$(octo-feather-state)/director.handoffs.jsonl`, 2026-10-27)

owner-caught-stranded-unseen x2, owner-caught-waits-invisible, owner-caught-gate-speed, owner-caught-cost-claims, owner-caught-gate-absence, owner-caught-director-priority: the owner supplying lane state the director should have seen. agents/director.md listed only prod and note moments for the director log, so such findings had no stated moment, and no status answer read the report.

## Level

- Rung 1 (structure): the report (`octo-feather-lane report`, built in this lane) is the one view of lane state and counts owner-caught classes (`#report-owner-caught`). This change points the director at it; the rule stays in the spec (pointers, no restatement).
- Rung 2 (exact check): none; when an answer is a status answer, and what the owner caught, are judgment.
- Rung 3 (structured judgment): the case below; the closed fact list has no fact for a command run, so the discriminator was read from the transcripts by hand and the case is owed, not in `just qa`.
- Rung 4 (prose), this change, agents/director.md: Behavior, "Before each status answer to the owner, run `octo-feather-lane report` (comms spec `#report-what`) and answer from it."; Write surface, the director-log sentence gains the finding moment by pointer to `#handoff-director-finding`.

## Smoke

Isolated: `scripts/octo-feather-qa` (qc sandbox, proof lines all `ok`, per-run scratch state dir, no Herdr, offline gh). Main side via `--kit-ref 8255ab90dfd1` (main's agents/director.md; main's `octo-feather-lane` has no `report`), branch side at the working tree (kit label a34639c, lane tip). Case added temporarily to evals/role-transcripts (text below), then removed. Rerun: add the case and expectation below, then

```
OCTO_FEATHER_QA_DIR=$(mktemp -d) scripts/octo-feather-qa --case director-status-report --kit-ref 8255ab90dfd1ccaea29bc97653e1db35128b4e31   # main
OCTO_FEATHER_QA_DIR=$(mktemp -d) scripts/octo-feather-qa --case director-status-report                                                   # branch
```

Then read each transcript: bash calls running `octo-feather-lane report`, and the lines appended to `director.handoffs.jsonl`.

Results, 2026-10-27, director model anthropic/claude-opus-5-5:

| Side | Run | qa line | `octo-feather-lane report` calls | director-log lines written |
|---|---|---|---|---|
| main 8255ab9 | 20261027T230429Z-104770 | PASS (attention gh205) | 0 | prod, note |
| main 8255ab9 | 20261027T230725Z-7c5bde | PASS (attention gh205) | 0 | prod, prod, note |
| branch | 20261027T230557Z-600c21 | PASS (attention gh205) | 1 | finding `owner-caught-ci-red-unsurfaced` (issue gh205), prod, prod |
| branch | 20261027T230818Z-cb582a | PASS (attention gh205) | 2 | finding `owner-caught-ci-red-unseen`, prod, prod, prod |

Main run 104770 answered from the messages ("All of the above comes from supervisor reports and what you told me") and logged the miss as a note. Branch run 600c21 ran the report in its first call ("my status report showed \"no open lane\"") and "logged the miss as an owner-caught finding against Board filters".

Verdict: the transcripts differ on both rules, 2/2 per side; the case's one fact (`declared attention`) passes on both sides and does not discriminate.

Demo: the finding line branch run 600c21 wrote, in a scratch state dir, through the lane tip's report:

```
$ XDG_STATE_HOME=$(mktemp -d) ...; octo-feather-lane report
report at 2026-10-27T23:07:17Z (/tmp/tmp.YJWRyAwSMV/octo-feather/lanes)
no open lane
owner queue: none
owner-caught (director.handoffs.jsonl):
  class owner-caught-ci-red-unsurfaced: count 1, last seen 2026-10-27T23:06:46Z (0m ago)
unread: none
```

Live box report, same day (director log on the box):

```
owner-caught (director.handoffs.jsonl):
  class owner-caught-cost-claims: count 1, last seen 2026-10-27T16:08:01Z (6h55m ago)
  class owner-caught-director-priority: count 1, last seen 2026-10-27T16:22:02Z (6h41m ago)
  class owner-caught-gate-absence: count 1, last seen 2026-10-27T16:08:01Z (6h55m ago)
  class owner-caught-gate-speed: count 1, last seen 2026-10-27T16:08:01Z (6h55m ago)
  class owner-caught-stranded-unseen: count 2, last seen 2026-10-27T16:08:01Z (6h55m ago)
  class owner-caught-waits-invisible: count 1, last seen 2026-10-27T16:08:01Z (6h55m ago)
```

Case:

```
{"id": "director-status-report", "role": "director", "fixture": "python-app", "task": <below>}
expectations: {"facts": [{"fact": "declared", "field": "attention", "in": ["gh205"]}]}
```

```
Director round, target repo {repo}. Supervisor messages since your last round, oldest first:
- 09:02 gh190 "Projects view" (w3:p1): integrated ticket 2 of 4 on gh190, `just check` green. Handing ticket 3 to the implementer.
- 09:14 gh205 "Board filters" (w5:p1): ticket 1 handed off; implementer working.
- 09:31 gh210 "Audit log export" (w6:p1): merge ask sent, waiting on the owner.
Owner, 09:45: "where are we? and gh205's PR CI has been red for two hours, I only saw it by opening GitHub myself. you should have told me."
Sandbox run: there is no Herdr and no GitHub; octo-feather-state is a scratch dir. Write each message you would send to a pane as a line `-> <pane>: <message>` in your final message, which is your reply to the owner. It ends with exactly one fenced json block and nothing else in json:
```json
{"attention": "<the lane key that needs action first, or \"none\">"}
```
```

Smoke: agents/director.md
Removed: the director log's two-moment list "on each prod (waking or redirecting a supervisor) and note to the owner worth keeping" (now three, the finding by pointer to `#handoff-director-finding`); incident: issue #137, owner-caught classes logged 2026-10-27 with no role rule to log them and no status answer read from the report.
