# qc-fallback

Criteria:

- [quality#acceptance-qc-fallback](../../../../docs/specs/quality.spec.html#acceptance-qc-fallback)

Drive criterion: `quality#acceptance-qc-fallback`

## Sub-features

- `neither` `just qc` on a scratch target claiming a criterion with neither a tagged acceptance test nor a declared demo: insufficient evidence naming that it has neither, no sandbox, judge or model started, the criterion planned (ADR 0035).
- `mixed` the same criterion beside one with a declared demo: the demo's result, and the same insufficient evidence.
- `read` no evidence record for the criterion with neither.

## How to get to it (user POV)

- A supervisor runs `just qc docs/specs/<slug>.status.json <PR> <id>...` on the lane's integrated head. A claimed criterion with no tagged test at the head and no `[demo."<spec>#<id>"]` command in the target's `qc.toml` gets the result lines `INSUFFICIENT EVIDENCE <id>: $ none`, `missing: no tagged acceptance test and no declared demo`, `evidence incomplete; decision none; record none`; the run exits 2 and the criterion stays planned. `octo-feather-qc` with no arguments prints its usage, which owns the rest.
- In the merge ask, `octo-feather-lane merge-ask` fails on it as on any insufficient evidence (its rule: `octo-feather-lane --help`, merge-ask).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the mixed case's demo runs in the qc sandbox.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-fallback`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-fallback/`.

The drive makes a scratch target (the kit's `tests/fixtures/spec-status/good/demo.spec.html`, its status file, a `qc.toml` declaring `values.qc_demo_pass` as `acceptance-a`'s demo and nothing for `acceptance-b`) and scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-fallback/state`). A stub `pi` that reaches no model is first on the sandbox's PATH through `OCTO_FEATHER_QC_PATH`, for the advisory on `acceptance-a`'s record.

- **Neither** (`neither`). In the scratch target (`env -C <scratch>`), run `just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-b`. Observe exit 2; `INSUFFICIENT EVIDENCE acceptance-b` with `missing: no tagged acceptance test and no declared demo` and `evidence incomplete; decision none; record none`; no `qc sandbox`, `pi-role`, `qc-judge` or `agent fallback` on stderr; in the report no `fallback` or `cap_s` key, the result with no record; both criteria planned, the head unchanged.
- **Mixed** (`mixed`). Run the same with `acceptance-a acceptance-b`. Observe exit 2; `PASS acceptance-a` with `decision demo checks` and its record; `acceptance-b` as above; acceptance-a built, acceptance-b planned.
- **Read** (`read`). Run `octo-feather-evidence read --repo <scratch> --criterion demo#acceptance-b --commit <head> --json`. Observe `[]`: nothing was recorded for it.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state or box store is written.

## Gotchas

- Put a stub `pi` on the sandbox's PATH with `OCTO_FEATHER_QC_PATH`, never only on PATH: a mise-shimmed `just` puts the box's real Pi ahead of it, and the advisory on a demo's record would reach a model.
- The merge ask's failure on insufficient evidence is covered by `tests/gate/kit/test_lane_merge_ask.py` (a fake GitHub), not by this drive.
