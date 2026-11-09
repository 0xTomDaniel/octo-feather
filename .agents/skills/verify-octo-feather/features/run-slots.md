# run-slots

Criteria:

- [quality#acceptance-verify-map-current](../../../../docs/specs/quality.spec.html#acceptance-verify-map-current) (no spec criterion owns the slots yet: the rule is owner ruling #660 2026-11-06, issue #668)

Drive criterion: `quality#acceptance-verify-map-current`

## Sub-features

- `grant-not-director` an implementer's `octo-feather-slot grant` refused (exit 77).
- `refused` a lane implementer's `just test` over 31 items without its lane's grant: refused before any item runs (exit 75), naming the count, heavy_items, the holder and the grant to ask for.
- `grant` the director's `octo-feather-slot grant gh7 --kind heavy`.
- `status` `octo-feather-slot status` naming gh7 the heavy holder, and the eval kind.
- `granted` the same `just test`, now holding the slot, passing.
- `released` `octo-feather-slot status` after it: no run holds either kind.
- `fresh-acquisition` additive `octo-feather-slot hold --kind heavy --items 99 --fresh`: a non-nested native hold using the existing grant/flock/held-ACK/stdin-EOF mechanism. Public regression reachability: `tests/gate/kit/test_slot.py::test_initial`.

## How to get to it (user POV)

- A worker or supervisor in a lane runs a gate over more than heavy_items items (`just fast`, `just check`, `just integrate --full`, `just fast-map`) or `just qa`; without its lane's grant the run stops with the refusal, which names the command to ask the director for.
- The director runs `octo-feather-slot grant <lane> --kind heavy|eval` and `octo-feather-slot status`. The rule, the files and the lane lookup: `octo-feather-slot --help`.
- An owned first-acquisition driver can select `hold --kind heavy --items 99 --fresh`; the interface and refusals are owned by `scripts/octo-feather-slot --help`. The driver keeps stdin open, requires an actual live `held:` ACK before START, and closes stdin only after owned job cleanup. A `free:`, `nested:`, refusal, timeout or EOF is not that ACK.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- The kit's gate runs offline (`just test` needs its uv venv and pnpm store, as `just check` does).

Run all existing drive cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive run-slots`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/run-slots/`. This drive does not yet select the additive fresh regression. CODEPREP status: fresh and existing paths NOT RUN for #757; this map edit is not an evidence record. Native default nonempty/nested ancestry remains FOREIGN/UNKNOWN and blocked, so the full drive is not cleared by the fresh-only source change.

The fresh public regression is separately reachable as `python3 tests/gate/kit/slot.py initial`, or the existing test runner's single item `.venv/bin/python -m pytest -n 0 -x tests/gate/kit/test_slot.py::test_initial`. It uses scratch grants and actual CLI/flocks, an owned hold Popen and stdin pipe, and existing finite external ps/argv stand-ins. Expected observations: default empty-holder `held:` ACK without ps, fresh contention refused75 without ps, real EOF release, and fresh reacquisition/release. These are proposed expectations, NOT RUN results; no native ps or old unsafe baseline is needed.

For a canonical native protocol smoke, use the exact approved clean head, an actual unexpired director grant and a separately authorized bounded driver. Select `scripts/octo-feather-slot hold --kind heavy --items 99 --fresh`, bound ACK readiness and EOF/wait cleanup, and launch no job in the first protocol smoke. A subsequent job needs its own live ACK/expiry check before START. Full source graph and proposed protocol: [#757 CODEPREP](../../../../evidence/2026-11-09-gh757-codeprep.md). Do not infer whole-helper safety, successful-cleanup RED equivalence or permission to run from this map.

The drive makes scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/run-slots/state`, HERDR_SESSION default) holding one lane record, gh7 (supervisor `w9:p1`), and a scratch suite of 31 trivial pytest items. The implementer's env: OCTO_FEATHER_ROLE=implementer, HERDR_PANE_ID=w9:p3, OCTO_FEATHER_PARENT=w9:p1, HERDR_WORKSPACE_ID=w9; the director's: OCTO_FEATHER_ROLE=director, HERDR_PANE_ID=w1:p1. No live Herdr, lane or box slot file is touched.

- **Not the director** (`grant-not-director`). As the implementer, run `octo-feather-slot grant gh7 --kind heavy`. Observe exit 77 and `grant is the director's` on stderr.
- **Refused** (`refused`). As the implementer, run `just --justfile <kit>/justfile test <scratch suite>`. Observe exit 75, no item passed, and on stderr `octo-feather-slot: refused, nothing ran: this heavy run selects 31 items, over heavy_items 30 (gate-budget.toml), and lane gh7 holds no heavy grant; current holder: none; ask the director: octo-feather-slot grant gh7 --kind heavy`.
- **Grant** (`grant`). As the director, run `octo-feather-slot grant gh7 --kind heavy`. Observe exit 0 and `granted: heavy slot to lane gh7 (granted <time> by w1:p1, expires <time>)`.
- **Status** (`status`). Run `octo-feather-slot status`. Observe `  holder: gh7 (granted ...` under heavy, and the eval kind's lines.
- **Granted** (`granted`). As the implementer, the same `just test`. Observe exit 0, `heavy slot: held: the heavy slot for lane gh7, run pid <pid> ...` and `31 passed`.
- **Released** (`released`). `octo-feather-slot status` again: `run holding it now: none` for both kinds.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- Outside a Herdr agent (no HERDR_PANE_ID or OCTO_FEATHER_ROLE) nothing is refused: the drive sets the implementer's env to be refused. A run nested under a holding run, or in the qc sandbox, is not refused either (`octo-feather-slot --help`).
