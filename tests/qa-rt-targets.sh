#!/usr/bin/env bash
# gate: e2e
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: test_write by the spec fixture's declared tests, credited to the call that wrote one, with the watcher's
# collection behind a slow test runner (testkit/qa_box.py); the rt suite's other cases: tests/gate/kit/test_qa_grading.py.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `rt_targets` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" rt_targets
