#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape), driven as
# commands with no case run: no sandbox, no model, no live Herdr (tests/gate/kit/testkit/qa_box.py).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves the command's wiring of --review (rules: octo-feather-qa --help, Review): no stored run case or too few
# arguments 64; check-evals refusing a review case with no question or with facts (the case field: schema.md, Case).
# A review case's run side, awaiting review with its output, a recorded verdict and note shown, the next run showing
# them (spec quality#acceptance-qa-review): tests/gate/kit/test_qa_stored.py, test_qa_review, in-process (#1090).
# Its scenario `review` in tests/gate/kit/qa_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qa_sections.py" review
