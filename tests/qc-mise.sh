#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's mise section (#508; setup tests/gate/kit/testkit/qc_box.py): mise in the sandbox (#437): a bare just through
# mise's shim runs, a tool not installed fails at its shim with no install, a caller with no mise installs fails
# the proof.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `mise` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" mise
