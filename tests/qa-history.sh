#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape), driven as
# commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-history through a history fixture (the form: schema.md, Case): a stub case on the
# kit's own history at a commit runs its role on that whole tree, one on a named local clone too; check-evals refuses an
# unknown repo or commit, naming case and field.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `history` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" history
