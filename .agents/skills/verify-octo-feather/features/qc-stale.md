# qc-stale

Criteria:

- [quality#acceptance-built-links](../../../../docs/specs/quality.spec.html#acceptance-built-links)
- [quality#acceptance-evidence-stale](../../../../docs/specs/quality.spec.html#acceptance-evidence-stale)

Drive criterion: `quality#acceptance-built-links`
Drive criterion: `quality#acceptance-evidence-stale`

## Sub-features

- `qc` `just qc` on a scratch target whose `qc.toml` declares a passing demo for each of two criteria, each covering its own code path and naming its own test: both built, each status entry naming its evidence record, the commit that record was captured at and its demo's tests.
- `show` after a commit changing an unrelated file and one changing acceptance-a's covered path, `octo-feather-spec-status show`: acceptance-a stale, naming its capture commit and the commit that changed its path; acceptance-b current.

## How to get to it (user POV)

- A supervisor runs `just qc docs/specs/<slug>.status.json <PR> <id>...` on the lane's integrated head; each passed criterion's entry in the status file names `record`, `commit` and `tests` (the entry's shape: `octo-feather-spec-status` usage).
- The owner runs `octo-feather-spec-status show [DIR|STATUS...]` (default `docs/specs`) in the target: one line per criterion, planned, built with no evidence link (built before qc linked records), or built current or `STALE` with what made it stale. Read-only; never part of `just check`. Its usage owns the stale rules.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-stale`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-stale/`.

The drive makes a scratch target (the kit's `tests/fixtures/spec-status/good/demo.spec.html`, its status file, `src/a`, `src/b`, `tests/a.sh`, `tests/b.sh`, a `qc.toml` whose two demos are `qc.toml` `values.qc_demo_pass`, covering `src/a` and `src/b`) and scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-stale/state`).

- **Build both** (`qc`). In the scratch target (`env -C <scratch>`), run `just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a acceptance-b`. Observe exit 0, `PASS` for both with their record ids; the status file at the head qc left holds each as `{"status": "built", "pr": 7, "record": <its id>, "commit": <judged head>, "tests": ["tests/<a|b>.sh"]}`.
- **Show** (`show`). The drive commits a change to `README`, then one to `src/a`; in the scratch target run `octo-feather-spec-status show`. Observe `acceptance-a: built (PR #7), STALE: record <id> captured at <head>; covered path src/a changed since <head> by <commit> change a's code`, `acceptance-b: built (PR #7), current: ...` and `2 built: 1 current, 1 stale, 0 no evidence link`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state or box store is written.

## Gotchas

- `show` compares code at HEAD, not the worktree: an uncommitted change to a covered path leaves it current until committed. A criterion's text is read from the worktree's spec.
- A criterion the agent fallback built (no demo at its capture commit) has no covers or tests: only a change to its text makes it stale; its line says so.
- The kit's own status files predate the links: their built rows show `no evidence link` until a lane's `just qc` judges them again.
