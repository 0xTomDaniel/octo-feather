#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's vendored-cache section (#508; setup tests/gate/kit/testkit/qc_box.py): a warm vendored-skill cache (#69) is
# bound read-only (check-vendored green in the sandbox, writes refused); new-repo's mise trust (#428) lands in an
# empty per-run state dir, nothing persists.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `vendored` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" vendored
