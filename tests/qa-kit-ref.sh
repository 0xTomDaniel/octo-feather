#!/usr/bin/env bash
# gate: e2e
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: --kit-ref runs a case against an earlier kit commit (FAIL before and PASS at a kit change, with its
# sha; a missing role file named; an unknown ref 64), its kit copy built from tracked files only; other repos under HOME and
# the --kit-ref head kit masked (attempt_blocked repo).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `kit_ref` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" kit_ref
