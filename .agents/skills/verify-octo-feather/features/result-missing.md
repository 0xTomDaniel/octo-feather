# result-missing

Criteria:

- [comms#acceptance-result-missing](../../../../docs/specs/comms.spec.html#acceptance-result-missing)
- [comms#roles-goal](../../../../docs/specs/comms.spec.html#roles-goal) (the outstanding listing)

Drive criterion: `comms#acceptance-result-missing`

## Sub-features

- `results` the supervisor's `octo-feather-handoff results` after implementer-gh7's session exited mid-ticket without reporting (gone from Herdr, no parked line, no result file), general-worker-gh7 still working: implementer-gh7 `ended`, `ended, no result file`; general-worker-gh7 `live working`, `none yet`.

## How to get to it (user POV)

- A supervisor's outstanding-workers listing, `octo-feather-handoff results` (`--help`, results), put in its context after a start or a compaction by `extensions/results-on-wake.ts`; what a missing result file means: comms spec `#roles-goal`.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive result-missing`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/result-missing/`.

The world is parent-resumed's (features/parent-resumed.md), under `scratch/result-missing/`, implementer-gh7 `w1:p2` dropped from Herdr, general-worker-gh7 `w1:p3` working with its spawn line in the lane log.

- **Results** (`results`). Run as the supervisor. Observe exit 0, stdout exactly `implementer-gh7<TAB>w1:p2<TAB>ended<TAB>ended, no result file` then `general-worker-gh7<TAB>w1:p3<TAB>live working<TAB>none yet`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.
