#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: ran: a run through the sandbox's recording shim matched by its arguments (positional prefix, flag and value pairs anywhere) and {head}, a count of matching runs, a case's stand-ins ({repo}, {head}, {head:N} filled), stdin/stdout/exit
# passed through, an echo or other arguments fail naming the record, a shim only for a named program.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `ran` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" ran
