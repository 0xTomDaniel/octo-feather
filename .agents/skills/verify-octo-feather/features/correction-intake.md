# correction-intake

Criteria:

- [comms#acceptance-reflect-files-correction](../../../../docs/specs/comms.spec.html#acceptance-reflect-files-correction)
- [issue-lifecycle#acceptance-writer-route-lane](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-writer-route-lane)
- [comms#acceptance-correction-intake](../../../../docs/specs/comms.spec.html#acceptance-correction-intake)
- [comms#acceptance-reflect-files-route-owner](../../../../docs/specs/comms.spec.html#acceptance-reflect-files-route-owner)

Drive criterion: `comms#acceptance-reflect-files-correction`
Drive criterion: `issue-lifecycle#acceptance-writer-route-lane`
Drive criterion: `comms#acceptance-correction-intake`
Drive criterion: `comms#acceptance-reflect-files-route-owner`

## Sub-features

- `file-rule` archive a scratch lane of target `varelaseb/octo-lite` while its archived lanes gh910 and gh911 hold `stale-pointer` and `own-pointer` logged blocking once each (code review, product judge), `slow-gate` only in reflection findings, and `one-lane` blocking twice in gh910; the director reflection routes `stale-pointer` to a kit role, gh912's lane reflection routes `own-pointer` `target:`: `stale-pointer`'s issue only in the kit's tracker naming that route, the target lanes' findings by lane, date and class only; `own-pointer`'s only in the target's, quoting its lanes' findings and gh912's routing finding; none for the others.
- `intake` `octo-feather-lane intake` over that tracker plus seeded open issues (`slow-gate`, two of `one-lane`): each class's line, its issues, `duplicates:` for `one-lane`, its findings; the tracker unchanged.

## How to get to it (user POV)

- Correction lanes file themselves at `octo-feather-lane archive` and `reflect`; the director reads `octo-feather-lane intake` to close the open ones the rule does not make due. Output lines: `octo-feather-lane --help`; the rule: issue-lifecycle spec `#lanes-correction`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive correction-intake`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/correction-intake/`.

The drive seeds a scratch state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/correction-intake/state`): archived lanes gh910 and gh911 with the finding lines Sub-features names, open lane gh912 with none, records naming repository `varelaseb/octo-lite` (a real repository, never written: the tracker is faked) and a `started_at` after its creation, an empty director log. The tracker is the kit's offline fake gh (`tests/fixtures/tracker-gh`, its store `scratch/correction-intake/gh.json`, its `repos` the real `gh repo view` answers of the kit and the target) under the real github-issues scripts. The reflectors are a stub `pi` the drive writes (`REFLECT_STUB_PI` in the helper, first on PATH) printing a reply in the reflector's form: the lane's one routing `own-pointer` to `target: docs/pointers.md`, the director's one routing `stale-pointer` to `agents/implementer.md Rules`. No model is called.

- **What files** (`file-rule`, two checks). Observe exit 0, `correction lane: filed <n> in github-issues 0xTomDaniel/octo-feather for stale-pointer (2 findings; route: agents/implementer.md Rules)`, its issue the kit's only one, quoting `- gh910 2026-10-20T00:00:00Z stale-pointer` and gh911's alike, no summary or target text; and `correction lane: filed <n> in github-issues varelaseb/octo-lite for own-pointer (3 findings; route: target: docs/pointers.md)`, its issue quoting gh910's, gh911's and gh912's findings in full; two issues in the store.
- **Intake** (`intake`). Observe exit 0, `class stale-pointer: due yes; blocking 2 in 2 lane(s) (gh910, gh911); findings 3`, `class slow-gate: due no; blocking 0 in 0 lane(s); findings 2`, `class one-lane: due no; blocking 2 in 1 lane(s) (gh910); findings 2` with `duplicates: 2 open issues of class one-lane`, and `intake.obs.unchanged` `yes`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state, no tracker write beyond the fake store, no model call.

## Gotchas

- The real reflectors' archive path is the correction-lane drive's (a model run); this one proves the rule and the intake with stubbed reflectors.
