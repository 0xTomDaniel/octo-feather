#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: role-transcript setup head (then)/branches/branch/origin/fake gh/{repo}{head}, skill load (read, cat; ls, grep, head,
# truncated; a fixture-only skill), declared_includes pass/missing/not a list, a kit_contract_edit fact failing on an
# unread skill; the rt suite's cases on the plain fixtures (the rest: tests/qa-rt-targets.sh).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `rt` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" rt
