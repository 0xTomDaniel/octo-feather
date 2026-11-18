#!/usr/bin/env bash
# The qc sandbox test's judge section (#508; setup tests/gate/kit/testkit/qc_box.py): --no-sandbox prints, writes its report and never
# commits; a run killed mid-judge leaves no scratch; a passed criterion becomes built and a failed one stays planned
# in one status-only commit; the judge launches from its own role file (agents/qc-judge.md), its model read there.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `judge` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" judge
