#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's OAuth and overlay section (#508; setup tests/gate/kit/testkit/qc_box.py): OAuth credentials on the box warn
# once and are never written back; removing an ignored dir the real worktree holds (#395) succeeds in the overlay,
# all discarded.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `oauth` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" oauth
