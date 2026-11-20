#!/usr/bin/env bash
# gate: e2e
# Integration test for `just install-check`, its mise, PATH and just section (#508; setup tests/gate/kit/testkit/install_check.py):
#   mise (owner ruling #261): at mise-version ok; a mise reporting another release: WRONG VERSION naming
#     mise-version, exit 1; a target with its own mise.toml (a repo the kit created): its tools ok at their lock with
#     mise's shims first, a pin not installed
#     MISSING naming the install of the target's own locked tools (`octo-feather-mise-install TARGET`), exit 1; a
#     target without one: no tool line.
#   just, which the kit runs in every target, at the kit mise.lock version, also in a target without mise.toml:
#     ok; a just reporting 0.0.1: WRONG VERSION naming the kit lock and the fix, exit 1.
#     Uses the box's mise installs (MISE_DATA_DIR kept while HOME is a fresh dir); installs nothing.
#   PATH (#422 items 2, 10): linear is hidden alone (its dir mirrored minus it), so a mise sharing its dir stays ok;
#     each pinned tool's first hit on the caller's PATH is printed ok; a stale node or mise first on PATH: SHADOWED
#     naming it, the pinned path and the fix, exit 1. pi and agent-browser installed into the target's mise node (their
#     npm fix lines, #463) stay pinned by their version files: another copy at the pin first on PATH is ok. In the kit,
#     judged on the PATHs the kit runs from (its recipes', a pane's): a stale node in a system dir before mise's shims
#     only a NOTE, exit 0; one in a dir ahead of mise's SHADOWED, exit 1; shims first ok, no NOTE.
# Run by `just check`: its scenario `mise` in tests/gate/kit/install_check.py, whose box is tests/gate/kit/testkit/install_check.py.
exec python3 "$(dirname "$0")/gate/kit/install_check.py" mise
