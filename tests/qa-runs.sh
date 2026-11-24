#!/usr/bin/env bash
# gate: e2e
# End-to-end test for scripts/octo-feather-qa (factory evals), driven as a command with a stub `pi` and a fake `herdr`
# first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py); each run in the real qc sandbox.
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves the command's wiring of --runs (what it does: octo-feather-qa --help): the run header naming the runs, each
# run sandboxed (run-<k>/sandbox.json), the exit, a bad value 64, --help. The case over its runs (spec
# quality#acceptance-qa-repeats): tests/gate/kit/test_qa_stored.py, test_qa_runs, in-process (#1090).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `runs` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" runs
