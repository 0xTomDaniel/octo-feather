#!/usr/bin/env bash
# gate: e2e
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape), driven as
# commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves based fixtures (rule: .agents/skills/eval-cases/references/schema.md, Fixtures, #988) in octo-feather-qa's case
# repo (main, head, head.then and branches: #991) and check-evals' fixture checks, --trees against a flat copy, and the refusals.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `fixture_base` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" fixture_base
