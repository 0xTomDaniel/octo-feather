#!/usr/bin/env bash
# gate: e2e
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: one PASS/FAIL line per case naming the deciding transcript facts, exit 1 on any failure and 0 when all
# pass, train and held-out score lines, per-run artifacts outside the repo, --suite/--case selection, --sample stratified
# and deterministic, role-skill coverage ({tracker} resolved per fixture), the run stops once its facts are decided, a pi
# that dies without an answer fails its case, each case runs in the qc sandbox and a failed sandbox proof is a FAIL,
# refusal inside a check run.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `qa` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" qa
