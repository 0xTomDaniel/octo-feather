#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals), driven as a command with a stub `pi` and a fake
# `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py; its stub reports usage on each assistant message).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-cost and quality#acceptance-qa-baseline through --runs and --baseline (what they
# do: octo-feather-qa --help): a case's time and tokens as mean and spread; a baseline kit where the case fails beside a
# current kit where it passes, in one run id, interleaved, with the difference; exit by the current kit; bad ref 64.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `baseline` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" baseline
