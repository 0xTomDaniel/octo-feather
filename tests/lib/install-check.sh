# shellcheck shell=bash
# shellcheck disable=SC2034  # ppin, real_py3, real_unshare, mpin, mdir: used by the items that source this file
# Sourced by tests/install-check.sh and each tests/install-check-<section>.sh (the `just install-check` test, one gate
# item per section, #508), never run itself: in tests/lib/ so the gate's tests/*.sh glob does not collect it. Offline:
# the kit's justfile run in a target (`just -f KIT/justfile install-check`, or TARGET as the argument). Each item gets
# its own throwaway dir ($t: HOME, the state folder, the kit install clone, the targets), the stubs on PATH, hide,
# check, and nomodel (no install-check run of the item called a model: each item ends with it).
# herdr, pi and gh are stubs (gh signed in, pi at the pin unless swapped), so only the tracker or pi line decides
# the exit.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "install-check test: $*" >&2; exit 1; }
mkdir -p "$t/bin" "$t/home" "$t/old"
pin="$(tr -d '[:space:]' <"$kit/pi-version")"
for x in herdr gh; do printf '#!/bin/sh\nexit 0\n' >"$t/bin/$x"; done
printf '#!/bin/sh\necho "$*" >>%s/pi-calls\necho %s\n' "$t" "$pin" >"$t/bin/pi"
# The review service: systemctl --user show answers $t/unit (active, enabled unless a case rewrites it).
printf 'ActiveState=active\nUnitFileState=enabled\n' >"$t/unit"
printf '#!/bin/sh\n[ "$1 $2" = "--user show" ] && exec cat "%s/unit"\nexit 1\n' "$t" >"$t/bin/systemctl"
ab() { printf '#!/bin/sh\n[ "$1" = doctor ] && exec cat "%s/doctor.json"\necho "agent-browser %s"\n' "$t" "$1" >"$t/bin/agent-browser"; chmod +x "$t/bin/agent-browser"; }
ab 0.40.0   # at the pin; the cases below swap or drop it
# chrome PATH: agent-browser doctor --offline --quick --json names Chrome at PATH (pass); no PATH: none found (fail).
chrome() { if [[ -n "${1:-}" ]]; then printf '{"checks":[{"category":"Chrome","id":"chrome.installed","message":"Google Chrome for Testing 156.0.8078.4 at %s","status":"pass"}]}\n' "$1"
  else printf '{"checks":[{"category":"Chrome","id":"chrome.installed","message":"Chrome not found","status":"fail"}]}\n'; fi >"$t/doctor.json"; }
okchrome="$t/home/.agent-browser/browsers/chrome-156/chrome-linux64/chrome"; chrome "$okchrome"
# The kernel and user namespace probes: uname -r answers $t/kver (the rest goes to the real uname); unshare succeeds
# unless $t/userns-off exists. ffmpeg present; one case below drops it.
echo 6.12.0 >"$t/kver"
printf '#!/bin/sh\n[ "$1" = -r ] && exec cat "%s/kver"\nexec "%s" "$@"\n' "$t" "$(command -v uname)" >"$t/bin/uname"
printf '#!/bin/sh\n[ -e "%s/userns-off" ] && { echo "unshare: write failed /proc/self/uid_map: Operation not permitted" >&2; exit 1; }\nexit 0\n' "$t" >"$t/bin/unshare"
printf '#!/bin/sh\nexit 0\n' >"$t/bin/ffmpeg"
# The session state folder (XDG_STATE_HOME) with its lanes/, and the live kit install: a clone of a bare origin, on main.
mkdir -p "$t/state/octo-feather/lanes"
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
g init -q --bare "$t/kit-origin.git"; g clone -q "$t/kit-origin.git" "$t/kitinst" 2>/dev/null
g -C "$t/kitinst" commit -q --allow-empty -m one; g -C "$t/kitinst" push -q origin main
kitinst="$t/kitinst"
printf '#!/bin/sh\necho "linear 3.0.0"\n' >"$t/old/linear"; chmod +x "$t/bin/"* "$t/old/linear"
# mise's own just, linked: its dir goes on the recipe's PATH (the test's, never one holding a linear), and the link
# resolves to mise's install, so install-check's PATH rule holds.
ln -s "$(mise which just)" "$t/bin/just"
export MISE_DATA_DIR="${MISE_DATA_DIR:-$HOME/.local/share/mise}"
UV_PYTHON_INSTALL_DIR="$(uv python dir)"; export UV_PYTHON_INSTALL_DIR
ppin="$(tr -d '[:space:]' <"$kit/.python-version")"; real_py3="$(command -v python3)"; real_unshare="$(command -v unshare)"
shims="$(mise doctor --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["dirs"]["shims"])')"
mpin="$(tr -d '[:space:]' <"$kit/mise-version")"
# hide NAMES PATHLIST: PATHLIST with only NAMES (space-separated) gone: each dir holding one is mirrored minus those
# files (links to the rest), never dropped, so the tools sharing its dir stay (#422 item 10). Prints ":dir:dir...".
hide() {
  python3 -c 'import os, sys, tempfile
names, scratch = set(sys.argv[1].split()), sys.argv[3]
out = ""
for d in filter(None, sys.argv[2].split(":")):
    if not any(os.path.lexists(os.path.join(d, n)) for n in names): out += ":" + d; continue
    m = tempfile.mkdtemp(prefix="mirror.", dir=scratch)
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f not in names: os.symlink(os.path.join(d, f), os.path.join(m, f))
    out += ":" + m
print(out, end="")' "$1" "$2" "$t"
}
# PATH without any linear (the recipe adds HOME/.local/bin: HOME is a fresh dir). The owner's Debian layout: linear
# and mise in one dir ($t/shared, the only mise on it), so hiding linear must keep that mise (first case below).
mkdir -p "$t/shared"; ln -s "$(command -v mise)" "$t/shared/mise"
printf '#!/bin/sh\necho "linear 3.1.0"\n' >"$t/shared/linear"; chmod +x "$t/shared/linear"
clean="$(hide linear "$t/shared$(hide mise "$PATH")")"
mdir="$(dirname "$(PATH="${clean#:}" command -v mise)")"   # $t/shared mirrored minus linear
lin_target="$t/linear"; gh_target="$t/github"
git init -q "$lin_target"; git init -q "$gh_target"; mkdir -p "$lin_target/sub"
cp "$kit/tests/fixtures/install-check/linear/.octo-feather.toml" "$lin_target/"
check() { # WANT DIR EXTRA_PATH [TARGET]: run in DIR (with $pre first on the caller's PATH); output in $out
  local rc=0; out="$(cd "$2" && env -u XDG_CACHE_HOME -u AGENT_BROWSER_EXECUTABLE_PATH -u SPEC_CHAT_CLONE HOME="$t/home" XDG_STATE_HOME="$t/state" OCTO_FEATHER_KIT_INSTALL="$kitinst" XDG_DATA_HOME="${data:-$t/home/.local/share}" PATH="${pre:+$pre:}$t/bin${3:+:$3}:$shims$clean" \
    just -f "$kit/justfile" install-check ${4:+"$4"} 2>&1)" || rc=$?
  [[ "$rc" == "$1" ]] || fail "in $2 (PATH extra '${3:-}'): want exit $1, got $rc: $out"
}
# nomodel: no install-check run so far called a model (the stub pi logs each call's arguments to $t/pi-calls).
nomodel() { ! grep -qE '(^| )(-p|--print)( |$)' "$t/pi-calls" || fail "install-check called a model: $(cat "$t/pi-calls")"; }
