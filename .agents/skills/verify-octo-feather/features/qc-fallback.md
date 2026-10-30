# qc-fallback

Criteria:

- [quality#acceptance-qc-fallback](../../../../docs/specs/quality.spec.html#acceptance-qc-fallback)

Drive criterion: `quality#acceptance-qc-fallback`

## Sub-features

- `qc` `just qc` on a scratch target whose `qc.toml` declares a demo for one claimed criterion and none for the other: the declared one decided by its demo's checks, the other by the agent fallback, a fresh qc judge for it alone under the time cap, its report appended as that criterion's evidence record.
- `read` that record read back with `octo-feather-evidence read`.

## How to get to it (user POV)

- A supervisor runs `just qc docs/specs/<slug>.status.json <PR> <id>...` on the lane's integrated head. Each claimed criterion with no `[demo."<spec>#<id>"]` in the target's `qc.toml` gets its own judge, one after another; its result line reads `evidence complete; decision agent fallback; record <id>`. The report (`$(octo-feather-state)/qc/`) holds each judge's run under `fallback`, and the cap in `cap_s`. `octo-feather-qc` with no arguments prints its usage, which owns the rest.
- In the merge ask, `octo-feather-lane merge-ask` prints each criterion row's decision source under `Decision sources` after the section (its rule: `octo-feather-lane --help`, merge-ask).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-fallback`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-fallback/`.

The drive makes a scratch target (the kit's `tests/fixtures/spec-status/good/demo.spec.html`, its status file, a `qc.toml` declaring `values.qc_demo_pass` as `acceptance-a`'s demo and no demo for `acceptance-b`) and scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-fallback/state`). The judge is the kit's stub judge, `tests/fixtures/qc-judge/pi`, first on the sandbox's PATH through `OCTO_FEATHER_QC_PATH`: no model runs.

- **Run** (`qc`). In the scratch target (`env -C <scratch>`), run `just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a acceptance-b`. Observe exit 0; `PASS acceptance-a` with `decision demo checks`; `PASS acceptance-b: $ judge acceptance-b` with `evidence complete; decision agent fallback; record <id>`; the stderr line `qc: agent fallback demo#acceptance-b: a fresh qc judge, time cap <cap> s`; in the report, `cap_s` that cap (`FALLBACK_CAP_S`, scripts/octo-feather-qc) and one `fallback` run, for `acceptance-b` alone, whose judge's parent is `timeout --foreground -k 10 <cap>` and whose brief names only `acceptance-b`; the record at the head holding `judge.report.json` with that judge's report; both criteria built.
- **Read** (`read`). Run `octo-feather-evidence read --repo <scratch> --criterion demo#acceptance-b --commit <head>`. Observe one record with `judge.report.json`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state or box store is written.

## Gotchas

- Put a stub judge on the sandbox's PATH with `OCTO_FEATHER_QC_PATH`, never only on PATH: a mise-shimmed `just` puts the box's real Pi ahead of it, and a real judge runs.
- The cap stopping a judge is not driven (it would wait the cap): `tests/qc-fallback.sh` fires the stub's timeout alarm instead. Until #406 that run exits 3, evidence incomplete, naming the criterion.
- The merge ask's `Decision sources` lines are covered by `tests/lane-merge-ask.sh` (a fake GitHub), not by this drive.
