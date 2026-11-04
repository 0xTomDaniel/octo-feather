#!/usr/bin/env bash
# Integration test for `just install-check`, its mise, PATH and just section (#508; setup tests/lib/install-check.sh):
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
# Run by `just check`; setup tests/lib/install-check.sh.
# shellcheck source=tests/lib/install-check.sh
source "$(dirname "$0")/lib/install-check.sh"
# mise at mise-version everywhere; a repo the kit created (its own mise.toml, here the kit's pins) gets each tool
# checked at its lock, PATH resolving to mise's; a repo the kit did not create (gh_target) gets no tool line.
mise_target="$t/created"; git init -q "$mise_target"; cp "$kit/mise.toml" "$kit/mise.lock" "$mise_target/"
check 0 "$mise_target" ""
grep -qx "mise   version $mpin ok (mise-version)" <<<"$out" && grep -qE "^mise   shellcheck [0-9.]+ ok \($mise_target/mise.lock\)$" <<<"$out" \
  || fail "created repo at the pins: no ok lines: $out"
# Each pinned tool's first hit on the caller's PATH (#422 item 2): mise's shim ok; a stale node launcher first on
# PATH: SHADOWED naming it, the pinned shim and the fix, exit 1.
grep -qx "path   node ok  $shims/node ($mise_target/mise.lock)" <<<"$out" && grep -qx "path   mise ok  $mdir/mise (mise-version)" <<<"$out" \
  || fail "created repo: no resolved-path ok lines for node and mise: $out"
o="$t/stale"; mkdir -p "$o"; printf '#!/bin/sh\necho v18.0.0\n' >"$o/node"; chmod +x "$o/node"
pre="$o" check 1 "$mise_target" ""; rm -rf "$o"
grep -qx "path   node SHADOWED $o/node comes first on PATH, before the pinned $shims/node ($mise_target/mise.lock); remove or rename $o/node, or put $shims first on PATH" <<<"$out" \
  || fail "stale node first on PATH: no SHADOWED line naming it, the pinned shim and the fix: $out"
# pi and agent-browser that `npm install -g` put in the target's mise node bin dir (a path: version stands in for it,
# trusted through the environment only): pinned by pi-version and agent-browser-version, not mise.lock, so the stubs
# at those pins first on PATH are ok (#463: the scratch-HOME proof's npm-installed pi made this SHADOWED).
npm_target="$t/npmglobal"; git init -q "$npm_target"; mkdir -p "$t/node/bin"
cp "$t/bin/pi" "$t/bin/agent-browser" "$t/node/bin/"; printf '[tools]\nnode = "path:%s/node"\n' "$t" >"$npm_target/mise.toml"
MISE_TRUSTED_CONFIG_PATHS="$npm_target" check 0 "$npm_target" ""
grep -qx "path   pi ok  $t/bin/pi (pi-version)" <<<"$out" && grep -qx "path   agent-browser ok  $t/bin/agent-browser (agent-browser-version)" <<<"$out" \
  || fail "pi and agent-browser in the target's mise node bin dir: not checked by their version pins: $out"
check 0 "$gh_target" ""
grep -qx "mise   version $mpin ok (mise-version)" <<<"$out" && ! grep -qE '^mise   [^v]' <<<"$out" || fail "a repo the kit did not create got mise tool lines: $out"
o="$t/first"; mkdir -p "$o"   # first on the caller's PATH, which the justfile keeps ahead of its tools
printf '#!/bin/sh\n[ "$1" = --version ] && { echo "2000.1.1 linux-x64"; exit 0; }\nexec "%s" "$@"\n' "$(command -v mise)" >"$o/mise"; chmod +x "$o/mise"
pre="$o" check 1 "$gh_target" ""; rm -rf "$o"
grep -qE "^mise   WRONG VERSION $o/mise reports 2000\.1\.1, want $mpin \(mise-version\); install mise $mpin: " <<<"$out" \
  || fail "mise 2000.1.1: no WRONG VERSION line naming mise-version: $out"
grep -qx "path   mise SHADOWED $o/mise comes first on PATH, before the pinned $mdir/mise (mise-version); remove or rename $o/mise, or put $mdir first on PATH" <<<"$out" \
  || fail "stale mise first on PATH: no SHADOWED line naming it, the pinned mise and the fix: $out"
# just, which the kit runs in every target, at the kit mise.lock version even in a repo the kit did not create:
# ok there with no mise tool or MISSING line; a just reporting another release: WRONG VERSION naming the
# kit lock and the fix, exit 1. The stub forwards all but --version to the real just (the gate guard asks it).
jv="$(mise -C "$kit" ls --local --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["just"][0]["version"])')"
check 0 "$gh_target" ""
grep -qx "just   version $jv ok (kit mise.lock)" <<<"$out" && ! grep -qE 'MISSING' <<<"$out" \
  || fail "foreign target, just at the kit version: no ok line, or a mise demand: $out"
o="$t/first"; mkdir -p "$o"
printf '#!/bin/sh\n[ "$1" = --version ] && { echo "just 0.0.1"; exit 0; }\nexec "%s" "$@"\n' "$t/bin/just" >"$o/just"; chmod +x "$o/just"
pre="$o" check 1 "$gh_target" ""; rm -rf "$o"
grep -qx "just   WRONG VERSION $o/just reports 0.0.1, want $jv (kit mise.lock); the kit runs it in every target: .*" <<<"$out" \
  || fail "foreign target, just 0.0.1: no WRONG VERSION line naming the kit lock: $out"
printf '[tools]\njust = "%s"\n' "$jv" >"$mise_target/mise.toml"
check 0 "$mise_target" ""
grep -qx "mise   just $jv ok ($mise_target/mise.lock)" <<<"$out" || fail "created repo, just at an installed pin: no ok line: $out"
printf '[tools]\njust = "0.0.1"\n' >"$mise_target/mise.toml"
check 1 "$mise_target" ""
grep -qxF "mise   just 0.0.1 MISSING ($mise_target/mise.lock); $kit/scripts/octo-feather-mise-install $mise_target" <<<"$out" \
  || fail "created repo, just at a pin not installed: no MISSING line naming the install: $out"
nomodel
echo "install-check-mise: ok (mise at its pin ok, 2000.1.1 named, exit 1; a created repo's mise.toml tools ok, MISSING named, exit 1; a repo the kit did not create gets no tool line; a stale node or mise first on PATH SHADOWED naming the pinned path and the fix, exit 1; pi and agent-browser in the target's mise node ok by their pins; just checked at the kit lock in every target (ok, 0.0.1 WRONG VERSION); no model call)"
