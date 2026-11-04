#!/usr/bin/env bash
# The #493 regression fixture's templates section (#508; the fixture, its namespace and the other sections:
# tests/user-mise.sh): (3) `just install-check` with a venv first on the pane PATH prints no SHADOWED line for a
# global-only tool; (4) README's install step exits 0 in the kit; in repos from templates/python and
# templates/typescript, `just setup` without the kit's scripts on PATH fails with mise's exit naming
# octo-feather-mise-install, exits 0 without the global config and with the kit's scripts; (3) their recipe PATH
# holds no global-only tool's dir; (5) the user's mise config, installs and shims byte-identical, doctor unchanged.
# Run by `just check`; Linux only (unshare); setup and namespaces tests/lib/user-mise.sh.
export USER_MISE_SECTION=templates
# shellcheck source=tests/lib/user-mise.sh
source "$(dirname "$0")/lib/user-mise.sh"
