#!/usr/bin/env bash
# gate: e2e
# The #493 regression fixture's install-check section (#508; the fixture, its namespace and the other sections:
# tests/user-mise.sh): (1) `just test -k 'install-check and not install-check-box'` (every install-check gate item
# but tests/install-check-box.sh, which tests/user-mise-ic-box.sh runs: two items, each under 40 s) passes in the kit
# copy under the fixture user's HOME, in a pane of the named Herdr session; (5) the user's mise state dir entries
# unchanged around it, the user's mise config, installs and shims byte-identical, doctor's answer unchanged.
# On Linux the only run of those items: each skips run directly, outside the fixture (#1200).
# Run by `just check`; Linux only (unshare); setup and namespaces tests/lib/user-mise.sh.
export USER_MISE_SECTION='install-check:install-check and not install-check-box'
# shellcheck source=tests/lib/user-mise.sh
source "$(dirname "$0")/lib/user-mise.sh"
