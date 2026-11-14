# one-execution

Criteria:

- [quality#acceptance-one-execution](../../../../docs/specs/quality.spec.html#acceptance-one-execution)
- [issue-lifecycle#acceptance-qc-interim](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-qc-interim) (two specs, one `just qc`)

Drive criterion: `quality#acceptance-one-execution`

## Sub-features

- `gate` the scratch target's full gate with the claims `demo#acceptance-a other#acceptance-c`, criteria of two specs: green, one evidence record each from the gate's run of its tagged test, naming its case and outcome, each test run once in the qc sandbox.
- `qc` one `just qc` on that head naming both status files, for acceptance-a and acceptance-c: each judged pass from its record, nothing rerun, both status files changed in one status-only commit.

## How to get to it (user POV)

- A supervisor runs the lane's final full gate given the lane's claimed criteria, then one `just qc docs/specs/<slug>.status.json... <PR> <id>...` on that head (which status files: issue-lifecycle spec `#qc-interim`). How a test is tagged and how the gate is given the claims: the docstrings of `tests/gate/test_gate.py` and `tests/gate/conftest.py`; `octo-feather-qc` with no arguments prints its usage, which owns the rest.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them; the kit's uv environment synced (`uv sync --locked`): the scratch gate runs the kit's locked pytest offline.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive one-execution`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/one-execution/`.

The drive makes a scratch target whose gate is the kit's runner (`tests/gate/conftest.py` and `test_gate.py` copied unchanged, the kit's locked pytest): the kit's `tests/fixtures/spec-status/good/demo.spec.html` and its status file, a second spec `other.spec.html` (that spec, anchors `acceptance-c` and `acceptance-d`) and its status file, a `qc.toml` declaring no demo, `tests/accept.sh` tagged `demo#acceptance-a` (passes, printing `RAN-accept`), `tests/skip.sh` tagged `demo#acceptance-b` (skips, exit 77, saying why) `tests/other.sh` tagged `other#acceptance-c` (passes) and an untagged `tests/plain.sh`; scratch box state (`XDG_STATE_HOME` under the run state) and the stub classifier on the qc sandbox's PATH.

- **Gate** (`gate`). In the scratch target, run `OCTO_FEATHER_QC_CLAIMS='demo#acceptance-a other#acceptance-c' just check`. Observe exit 0; the lines `qc capture: demo#acceptance-a: record <id>, 1 case(s): tests/accept.sh passed` and `qc capture: other#acceptance-c: record <id>, 1 case(s): tests/other.sh passed`; the scratch store holding those two records, each `test.capture.json` naming its case (`tests/gate/test_gate.py::test_script[tests/accept.sh]`, `...[tests/other.sh]`), outcome `passed` and the qc sandbox's proof, each `test.output` holding `RAN-accept` once.
- **qc** (`qc`). Run `just --justfile <kit>/justfile qc docs/specs/demo.status.json docs/specs/other.status.json 7 acceptance-a acceptance-c`. Observe exit 0; for each id `PASS <id>`, `1/1 tagged cases passed in the gate's run at <head12>, not rerun`, `evidence complete; decision tagged test assertions; record <the gate's id for it>`; the store still those two records; one qc report per spec (`spec` demo and other), with no capture and no fallback; one commit on the head, changing only both status files (observed as `commit`): acceptance-a built with PR 7, its record, the head and `tests/accept.sh`, acceptance-c likewise with `tests/other.sh` (observed as `status`).
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; the scratch records stay in the scratch store.

## Gotchas

- The gate runs pytest at 2 workers; the box rule on parallel gates applies to it as to any gate run.
- Run inside a qc sandbox (the kit's own `just qc` on this criterion), the scratch gate's capture starts a nested qc sandbox, which must pass its proof, as for qc-capture.
