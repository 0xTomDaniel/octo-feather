#!/usr/bin/env bash
# Regression fixture for #493 (the kit installs and passes its gate under the installing user's existing mise setup,
# never editing that setup: ADR 0005): a throwaway user HOME prepared as #493's "Regression fixture" says, in its own
# user+mount+network namespace (unshare -rmn: offline, as tests/qc.sh), then #493's assertions (1)-(5) run in it,
# one gate item per section (#508), each with its own fixture (tests/lib/user-mise.sh):
#   this item: the fixture's preconditions (the bound kit installs read-only, doctor exiting 0 under the user's HOME
#   and 1 under a moved HOME, python3 a mise shim, the global tools absent from the kit's mise.lock); (1) the qc
#   sandbox proof passes (octo-feather-qc with a stub judge, no model, HOME moved as the gate's tests move it); (2)
#   the negatives still exit 66: doctor printing no JSON, JSON without dirs, an uninstalled pinned tool (naming mise
#   install), and a shim of an uninstalled tool installs and writes nothing;
#   tests/user-mise-ic.sh and tests/user-mise-ic-box.sh: (1) the install-check gate items (tests/install-check*.sh,
#   split between the two) pass in the kit copy; (5) the user's mise state dir entries counted around them, unchanged;
#   tests/user-mise-templates.sh: (3) no SHADOWED line for a global-only tool in `just install-check`, nor a
#   global-only tool's dir on a template repo's recipe PATH; (4) the shared install command and `just setup` in
#   repos from both templates.
#   Every item: (5) the user's mise config, installs and shims byte-identical across its section, doctor's answer
#   under the user's HOME unchanged.
# `tests/user-mise.sh --gate [pytest args]` (just check-user-mise, #493 AC1): the whole gate, or the items pytest args
# choose, run inside the fixture instead of the assertions (tests/lib/user-mise.sh).
# Run by `just check`; Linux only (unshare); setup and namespaces tests/lib/user-mise.sh.
export USER_MISE_SECTION=sandbox
# shellcheck source=tests/lib/user-mise.sh
source "$(dirname "$0")/lib/user-mise.sh"
