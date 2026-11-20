#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals), driven as a command with a stub `pi` and a fake
# `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py; its stub streams a parallel codemode batch as Pi does).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-skill-triggers at the max_tool_calls bound (the stop rule: octo-feather-qa --help):
# a skill read in flight in a batch that crosses the bound is graded; a read started after that batch is not.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `cap_batch` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" cap_batch
