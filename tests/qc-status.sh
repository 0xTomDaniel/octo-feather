#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's status section (#508; setup tests/gate/kit/testkit/qc_box.py): --no-sandbox prints, writes its
# report and never commits; a criterion whose declared demo passes becomes built and one whose demo fails stays planned,
# in one status-only commit (ADR 0035: no agent judge).
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `status` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" status
