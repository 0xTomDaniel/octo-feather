# one-execution-incomplete

Criteria:

- [quality#acceptance-one-execution-incomplete](../../../../docs/specs/quality.spec.html#acceptance-one-execution-incomplete)

Drive criterion: `quality#acceptance-one-execution-incomplete`

## Sub-features

- `gate` the scratch target's full gate with the claim `demo#acceptance-b`, whose tagged test skips: green, one record naming the case skipped.
- `qc` `just qc` on that head for acceptance-b: insufficient evidence naming the skipped case, no agent judge.

## How to get to it (user POV)

- A supervisor runs the lane's final full gate with the lane's claimed criteria, `OCTO_FEATHER_QC_CLAIMS="<spec>#<anchor> ..." just check` (or `just integrate --full` with it), then `just qc docs/specs/<slug>.status.json <PR> <id>...` on that head. A test is tagged with the criterion it proves by its pytest `criterion` marker; a kit-style `tests/*.sh` by a header line `# criterion: <spec>#<anchor>` (`tests/gate/test_gate.py`, `tests/gate/conftest.py`). `octo-feather-qc` with no arguments prints its usage, which owns the rest.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them; the kit's uv environment synced (`uv sync --locked`): the scratch gate runs the kit's locked pytest offline.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive one-execution-incomplete`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/one-execution-incomplete/`.

The drive makes a scratch target whose gate is the kit's runner (`tests/gate/conftest.py` and `test_gate.py` copied unchanged, the kit's locked pytest): the kit's `tests/fixtures/spec-status/good/demo.spec.html` and its status file, a `qc.toml` declaring no demo, `tests/accept.sh` tagged `demo#acceptance-a` (passes, printing `RAN-accept`), `tests/skip.sh` tagged `demo#acceptance-b` (skips, exit 77, saying why) and an untagged `tests/plain.sh`; scratch box state (`XDG_STATE_HOME` under the run state) and the stub classifier on the qc sandbox's PATH.

- **Gate** (`gate`). In the scratch target, run `OCTO_FEATHER_QC_CLAIMS=demo#acceptance-b just check`. Observe exit 0 (a skip is no failure); the line `qc capture: demo#acceptance-b: record <id>, 1 case(s): tests/skip.sh skipped`; that one record in the scratch store naming the case `skipped`.
- **qc** (`qc`). Run `just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-b`. Observe exit 2; `INSUFFICIENT EVIDENCE acceptance-b`, `missing: case tests/skip.sh (...) skipped: skip: needs a GPU, none here`, `evidence incomplete; decision tagged test assertions; record <the gate's id>`; no `agent fallback` on stderr and no fallback in the qc report; no new record; acceptance-b planned.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; the scratch records stay in the scratch store.

## Gotchas

- The gate runs pytest at 2 workers; the box rule on parallel gates applies to it as to any gate run.
- Run inside a qc sandbox (the kit's own `just qc` on this criterion), the scratch gate's capture starts a nested qc sandbox, which must pass its proof, as for qc-capture.
