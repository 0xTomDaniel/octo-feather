#!/usr/bin/env bash
# gate: e2e
# The qc sandbox test's escapes section (#508; setup tests/gate/kit/testkit/qc_box.py): a failed proof check (live Herdr reachable,
# a Linear key re-entering the judge's env, a repo mask that cannot be set up) aborts before the judge; a judge
# trying each escape (#33) fails at every one, masks cannot be unmounted, leftovers are killed and agents counted,
# another repo's listing is recorded and refused, and no live record is written.
# Run by `just check`; offline and bounded, in its own namespace and throwaway HOME (tests/gate/kit/testkit/qc_box.py):
# its scenario `escapes` in tests/gate/kit/qc_sections.py.
exec python3 "$(dirname "$0")/gate/kit/qc_sections.py" escapes
