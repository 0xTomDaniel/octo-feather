#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: a judgment suite's bench (its extension command run for real by the stub pi under node, stub
# classifiers at the model registry): per classifier accuracy/calibration/cost train and held-out apart, classifiers.json
# lists applied (moving alias and yes/no only skipped, never called), unavailable named, the kit's model beside the best
# and its threshold, --classifier, best's tie-break, a kit model unscored fails, a dead bench command fails, its spend
# in the ledger and an unwritable ledger changes nothing.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# Its scenario `bench` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" bench
