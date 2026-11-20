#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape), driven as
# commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves the shape check refuses a malformed tool_called_before or edit_under target (rules: schema.md, Facts, Before
# targets), naming case and field (their grading: tests/gate/kit/test_qa_grading.py).
# Run by `just check`.
# Its scenario `before_tool` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" before_tool
