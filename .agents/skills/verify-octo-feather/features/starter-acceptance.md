# starter-acceptance

Criteria:

- [templates#acceptance-starter-acceptance-test](../../../../docs/specs/templates.spec.html#acceptance-starter-acceptance-test)

Drive criterion: `templates#acceptance-starter-acceptance-test`

## Sub-features

Each case runs once per template, `python-<case>` and `typescript-<case>`:

- `new-repo` `just new-repo LANG DEST --no-spec-chat`, its packages installed offline, its status file made (`octo-feather-spec-status init`) and committed (observed as `install`).
- `gate` `OCTO_FEATHER_QC_CLAIMS=app#acceptance-hello-json just check`: green, and `qc capture: app#acceptance-hello-json: record <id>, 1 case(s): <test> passed`; the store holds that one record (observed as `store`).
- `qc` `just qc docs/specs/app.status.json 7 acceptance-hello-json`: `PASS`, `decision tagged test assertions; record <id>` the gate's record, stderr naming it judged from the gate's record, not rerun; no new record, no demo and no judge in the report (observed as `report`); the status file's entry built with that record, its commit and the test (observed as `status`).

## How to get to it (user POV)

- In a repo from either template, the lane's final full gate runs with the lane's claims (`OCTO_FEATHER_QC_CLAIMS=<spec>#<anchor> just check`), then the supervisor runs `just qc docs/specs/<spec>.status.json <PR> <id>...` on that head. How the starter criterion's test is tagged: the created repo's verify-app skill, Acceptance.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- The uv cache and pnpm store hold both templates' locked packages (as [template-tiers](template-tiers.md)); unprivileged user namespaces for the qc sandbox (Linux).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive starter-acceptance`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/starter-acceptance/`.

- **Scratch repos.** One repo per template under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/starter-acceptance/<lang>`.
- **Model boundary.** `OCTO_FEATHER_QC_PATH` puts the kit's stub classifier `pi` (tests/fixtures/classify-stub/pi) first on the qc sandbox's PATH: `just qc`'s advisory answer shows unavailable, no model is called.
- **Side effects.** `XDG_STATE_HOME` (trend lines, the scratch evidence store) and `MISE_STATE_DIR` under the scratch; `GATE_WORKERS=2`. Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The drive commits nothing between its `gate` and `qc` cases: `just qc` judges records of its own head only, and what a claims run refuses (quality spec `#qc-capture`, `#qc-judgment`).
