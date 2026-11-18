#!/usr/bin/env bash
# The qc sandbox test's credential-copies section (#508; setup tests/gate/kit/testkit/qc_box.py): no judge write persists (the
# worktree is an overlay on the run tmpfs): copies of Pi's credentials into ignored scratch/, .git, over 64 MiB,
# an intermediate refresh, token values alone, into HOME; the judge's rewrites of auth.json and models.json hit
# per-run copies, the box files byte-identical.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `copies` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" copies
