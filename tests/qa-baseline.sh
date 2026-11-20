#!/usr/bin/env bash
# gate: e2e
# End-to-end test for scripts/octo-feather-qa (factory evals), driven as a command with a stub `pi` and a fake
# `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py); each run in the real qc sandbox.
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves the command's wiring of --baseline (what it does: octo-feather-qa --help): one evaluation naming the baseline,
# its runs interleaved, the exit by the current kit, an unknown or missing baseline 64. A case's time and tokens and
# the baseline beside the current kit with the difference (spec quality#acceptance-qa-cost,
# quality#acceptance-qa-baseline): tests/gate/kit/test_qa_stored.py, test_qa_baseline, in-process (#1090).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `baseline` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" baseline
