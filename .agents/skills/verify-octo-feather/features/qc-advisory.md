# qc-advisory

Criteria:

- [quality#acceptance-qc-advisory](../../../../docs/specs/quality.spec.html#acceptance-qc-advisory)

Drive criterion: `quality#acceptance-qc-advisory`

## Sub-features

- `qc` `just qc` on a scratch target whose `qc.toml` declares a passing demo, the kit's judgment model induced to answer `does-not-show`: the criterion passes, and the advisory model judgment (answer, confidence, question `criterion-evidence`, the model) shows beside it and in the report's `results`.

- `sprint` repeats that real passing demo with explicit invocation authorization, observing NOT RUN metadata and the same built status. Eligibility and event expiry are owned by [quality#qc-advisory-sprint](../../../../docs/specs/quality.spec.html#qc-advisory-sprint).

## How to get to it (user POV)

- A supervisor runs `just qc docs/specs/<slug>.status.json <PR> <id>...` on the lane's integrated head. Each claimed criterion whose result has an evidence record gets the kit's judgment model's answer to the closed question in `evals/judgment-criterion-evidence/question.json`, through the one classify path. The line under the result starts `advisory model judgment`; no gate reads it. The model unreachable or failing: `advisory model judgment unavailable (...)`, the result as decided. `octo-feather-qc` with no arguments prints its usage.

The explicit invocation configuration is `OCTO_FEATHER_QC_ADVISORY_AUTHORITY=gpt-only-sprint-2026-11-08` together with `OCTO_FEATHER_QC_ADVISORY_SCOPE=<authorized scope>`; see `octo-feather-qc` usage and the owning exception above. Omit both for ordinary advice. Unsupported configurations fail before any demo or fallback runs.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them. `node` on PATH: the stub runs the kit's classify extension under it.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-advisory`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-advisory/`.

The drive makes a scratch target (the kit's `tests/fixtures/spec-status/good/demo.spec.html`, its status file, a `qc.toml` whose one demo is `values.qc_demo_pass`) and scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-advisory/state`). The induced failure is at the classifier boundary: the kit's stub `pi` (`tests/fixtures/classify-stub/pi`, its usage in its header), first on the qc sandbox's PATH through `OCTO_FEATHER_QC_PATH` (`octo-feather-qc` usage), runs the real classify extension under node with a stub model registry listing the kit's judgment model (`evals/judgment-model.json`), which answers `STUB_ANSWER=does-not-show` at `STUB_CONFIDENCE=0.91`. No real model is called.

- **Induced no** (`qc`). In the scratch target, run `just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a`. Observe exit 0; `PASS acceptance-a`, then `demo exit status 0`, `evidence complete; decision demo checks; record <id>`, then `advisory model judgment (no gate reads it): does-not-show, confidence 0.910 (criterion-evidence by <kit model>; ...)`; the status commit makes `acceptance-a` built; the report's result for it holds `verdict` pass and `advisory` with that answer, confidence and model, labelled a model judgment.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state or box store is written, no model spend.

## Smoke

Smoke: .agents/skills/verify-octo-feather/features/qc-advisory.md 2026-11-08 public `run qc-advisory` passed both `qc` and `sprint`; evidence record `20261108T214516Z-c29610f6` (dirty merge head `a8e065b`). Classifier boundary stub only, real sandboxed demos and status commits. This is focused smoke, not final lane acceptance.

## Gotchas

- The stub answers every question the same: it proves the result ignores the answer, not that a real model would say no. The real model's accuracy on this question is the bench's (`just qa --suite judgment-criterion-evidence`), never this drive's.
- Without the stub, the same `just qc` asks the box's real judgment model through Pi; offline or unauthenticated, the line says unavailable and the result is unchanged.
