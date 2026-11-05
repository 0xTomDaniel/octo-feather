#!/usr/bin/env bash
# gate: e2e
# The #493 regression fixture's install-check section for tests/install-check-box.sh (#508; the fixture, its
# namespace and the other sections: tests/user-mise.sh; the other install-check items: tests/user-mise-ic.sh): (1)
# `just test -k tests/install-check-box.sh` passes in the kit copy under the fixture user's HOME, in a pane of the
# named Herdr session; (5) the user's mise state dir entries unchanged around it, the user's mise config, installs
# and shims byte-identical, doctor's answer unchanged.
# Run by `just check`; Linux only (unshare); setup and namespaces tests/lib/user-mise.sh.
export USER_MISE_SECTION=install-check:tests/install-check-box.sh
# shellcheck source=tests/lib/user-mise.sh
source "$(dirname "$0")/lib/user-mise.sh"
