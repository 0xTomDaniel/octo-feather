# gh1004: correction lanes file in the route owner's tracker; the verify drives follow

Change: `octo-feather-lane reflect`/`archive` file each due correction lane, and each recurrence comment, in the tracker of the repository that owns the route (rule: comms spec `#reflection-correction`, `#reflection-output`; issue #1004, parent #850). The verify-octo-feather feature map follows: correction-lane's scratch lanes are the kit's and file in the kit's tracker; correction-intake's lanes are of target `varelaseb/octo-lite`, a kit-routed class files only in the kit's tracker quoting the target lanes' findings by lane, date and class, a `target:`-routed class only in the target's; the index line names the route owner.

Smoke: .agents/skills/verify-octo-feather/features/correction-intake.md (the recipe the correction-intake drive below follows; stub reflectors, no model run)
Smoke: .agents/skills/verify-octo-feather/features/correction-lane.md (the recipe the correction-lane drive below follows; the real reflectors at thinking off)
Smoke: .agents/skills/verify-octo-feather/features/README.md (its index line for correction-intake; the same correction-intake drive)

## The drives

At e03e4710 (implementer-gh1004 with origin/main 16798024 merged), offline fake gh (`tests/fixtures/tracker-gh/gh`, `repos` the real `gh repo view` answers of 0xTomDaniel/octo-feather and varelaseb/octo-lite):

- `verify-octo-feather run correction-intake`: PASS, cases file-rule (two checks) and intake; records 20261118T204606Z-26da51d3 (comms#acceptance-reflect-files-correction), 20261118T204607Z-3211d70d (issue-lifecycle#acceptance-writer-route-lane), 20261118T204607Z-8823dfd0 (comms#acceptance-correction-intake), 20261118T204607Z-4790a2e0 (comms#acceptance-reflect-files-route-owner).
- `OCTO_FEATHER_REFLECT_ARGS="--thinking off" verify-octo-feather run correction-lane`: PASS, case file-live; record 20261118T204657Z-25e94c16.

correction-intake's archive (an earlier identical run at a5922ac0):

```
correction lane: filed 901 in github-issues 0xTomDaniel/octo-feather for stale-pointer (2 findings; route: agents/implementer.md Rules)
correction lane: filed 902 in github-issues varelaseb/octo-lite for own-pointer (3 findings; route: target: docs/pointers.md)
```

The kit's issue quotes `- gh910 2026-10-20T00:00:00Z stale-pointer` and `- gh911 2026-10-21T00:00:00Z stale-pointer`, no summary or target text; the target's quotes gh910's, gh911's and gh912's routing reflection finding in full.

correction-lane's archive, the real lane and director reflectors:

```
correction lane: filed 901 in github-issues 0xTomDaniel/octo-feather for duplicated-rule (2 findings; route: implementer output template, structured rule-owner field and behavioral eval)
```

## Tests

`just test tests/gate/kit/test_lane_correction.py` (route_owner, refusal, recurrence and the rest, testkit's Pi and gh store): passed; route_owner fails against the commit before the target issue quoted its routing finding.
