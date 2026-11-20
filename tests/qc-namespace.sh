#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's namespace section (#508, #997; setup tests/gate/kit/testkit/qc_box.py), split from tests/qc.sh:
# a nested qc sandbox passes its proof, a pane the judge spawns runs in its PID namespace and dies with it (the
# testkit herdr; the box's real herdr only with QC_TEST_HERDR=real, `just qc-real-herdr`; the test prints which).
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `namespace` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" namespace
