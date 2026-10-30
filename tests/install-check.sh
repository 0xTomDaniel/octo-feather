#!/usr/bin/env bash
# Integration test for `just install-check` per target (spec remote#host-tools, #acceptance-install-linear), offline:
# the kit's justfile run in a target (`just -f KIT/justfile install-check`, or TARGET as the argument).
#   Linear target (tests/fixtures/install-check/linear), no linear on PATH: exit 1, linear listed missing with the
#     pinned v3.1.0 and the install path (release binary, or npx @schpet/linear-cli);
#   the linear skill's fake linear on PATH (reports the pin): linear ok, exit 0; a linear reporting another
#     release: listed with the wanted v3.1.0, exit 1;
#   GitHub target (no config): linear never checked;
#   pi at the kit's pin (pi-version): its version line ok; pi reporting another release: WRONG VERSION naming
#     the pin and the npm install command, exit 1;
#   browser target (qc.toml [browser] playwright pin, spec remote#acceptance-install-browser), no browser folder:
#     browser MISSING naming the pin, the box folder and the install command, exit 1; a fake headless shell in
#     the folder at that pin: ok, exit 0; the folder under the cache folder the qc sandbox masks: refused, exit 1;
#     GitHub target (no qc.toml [browser]): no browser line. No browser is downloaded: the folder is faked.
#   agent-browser (spec remote#acceptance-install-agent-browser), a stub: at 0.40.0 ok; 0.39.4 WRONG VERSION; none on
#     PATH: MISSING naming 0.40.0 and the npm install, exit 1.
#   mise (owner ruling #261): at mise-version ok; a mise reporting another release: WRONG VERSION naming
#     mise-version, exit 1; a target with its own mise.toml (a repo the kit created): its tools ok at their lock with
#     mise's shims first, a pin not installed
#     MISSING naming `mise -C TARGET install --locked`, exit 1; a target without one: no tool line.
#   just, which the kit runs in every target, at the kit mise.lock version, also in a target without mise.toml:
#     ok; a just reporting 0.0.1: WRONG VERSION naming the kit lock and the fix, exit 1.
#     Uses the box's mise installs (MISE_DATA_DIR kept while HOME is a fresh dir); installs nothing.
#   PATH (#422 items 2, 10): linear is hidden alone (its dir mirrored minus it), so a mise sharing its dir stays ok;
#     each pinned tool's first hit on the caller's PATH is printed ok; a stale node or mise first on PATH: SHADOWED
#     naming it, the pinned path and the fix, exit 1.
#   Python (owner ruling #422, #261): the gate's Python at the kit's .python-version, found through uv: ok with venv and
#     pidfd_open; none installed: MISSING naming `uv python install --no-bin`, exit 1, and `just check` in a copy of the
#     kit refuses, naming it. The box python3 at 3.11 or later ok; a python3 reporting 3.10: WRONG VERSION, exit 1.
#     Uses the box's uv Python installs (UV_PYTHON_INSTALL_DIR kept while HOME is a fresh dir); installs nothing.
# herdr, pi and gh are stubs (gh signed in, pi at the pin unless swapped), so only the tracker or pi line decides
# the exit. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "install-check test: $*" >&2; exit 1; }
mkdir -p "$t/bin" "$t/home" "$t/old"
pin="$(tr -d '[:space:]' <"$kit/pi-version")"
for x in herdr gh; do printf '#!/bin/sh\nexit 0\n' >"$t/bin/$x"; done
printf '#!/bin/sh\necho %s\n' "$pin" >"$t/bin/pi"
printf '#!/bin/sh\necho "agent-browser 0.40.0"\n' >"$t/bin/agent-browser"   # at the pin; the cases below swap or drop it
printf '#!/bin/sh\necho "linear 3.0.0"\n' >"$t/old/linear"; chmod +x "$t/bin/"* "$t/old/linear"
# mise's own just, linked: its dir goes on the recipe's PATH (the test's, never one holding a linear), and the link
# resolves to mise's install, so install-check's PATH rule holds.
ln -s "$(mise which just)" "$t/bin/just"
export MISE_DATA_DIR="${MISE_DATA_DIR:-$HOME/.local/share/mise}"
UV_PYTHON_INSTALL_DIR="$(uv python dir)"; export UV_PYTHON_INSTALL_DIR
ppin="$(tr -d '[:space:]' <"$kit/.python-version")"; real_py3="$(command -v python3)"
shims="$(mise doctor --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["dirs"]["shims"])')"
mpin="$(tr -d '[:space:]' <"$kit/mise-version")"
# hide NAME PATHLIST: PATHLIST with only NAME gone: each dir holding it is mirrored minus that one file (links to
# the rest), never dropped, so the tools sharing its dir stay (#422 item 10). Prints ":dir:dir...".
hide() {
  local out="" d f m; local -a ds; IFS=: read -ra ds <<<"$2"
  for d in "${ds[@]}"; do
    [[ -n "$d" ]] || continue
    if [[ -e "$d/$1" || -L "$d/$1" ]]; then m="$(mktemp -d "$t/mirror.XXXXXX")"
      for f in "$d"/* "$d"/.[!.]*; do [[ ( -e "$f" || -L "$f" ) && "${f##*/}" != "$1" ]] && ln -s "$f" "$m/"; done; out+=":$m"
    else out+=":$d"; fi
  done; printf '%s' "$out"
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
  local rc=0; out="$(cd "$2" && env -u XDG_CACHE_HOME HOME="$t/home" XDG_DATA_HOME="${data:-$t/home/.local/share}" PATH="${pre:+$pre:}$t/bin${3:+:$3}:$shims$clean" \
    just -f "$kit/justfile" install-check ${4:+"$4"} 2>&1)" || rc=$?
  [[ "$rc" == "$1" ]] || fail "in $2 (PATH extra '${3:-}'): want exit $1, got $rc: $out"
}

check 1 "$lin_target/sub" ""
grep -q '^tracker linear ' <<<"$out" || fail "Linear target: no tracker line: $out"
grep -qx "mise   version $mpin ok (mise-version)" <<<"$out" || fail "linear hidden from a dir it shares with mise: mise gone too: $out"
grep -E '^linear MISSING \(want v3\.1\.0\)' <<<"$out" | grep -q 'releases/tag/v3\.1\.0' \
  && grep -q 'npx @schpet/linear-cli' <<<"$out" || fail "Linear target without linear: not listed missing with v3.1.0 and the install path: $out"
check 0 "$t" "$kit/.agents/skills/linear/scripts" "$lin_target"
grep -qE '^linear ok  .*/linear \(v3\.1\.0\)$' <<<"$out" || fail "Linear target, fake linear at the pin: not ok: $out"
check 1 "$lin_target" "$t/old"
grep -qE '^linear WRONG VERSION .* reports 3\.0\.0, want v3\.1\.0; .*npx @schpet/linear-cli' <<<"$out" || fail "Linear target, linear 3.0.0: $out"
check 0 "$gh_target" ""
grep -q '^tracker github-issues ' <<<"$out" && ! grep -qi linear <<<"$out" || fail "GitHub target checked linear: $out"
grep -qx "pi     version $pin ok (pi-version)" <<<"$out" || fail "pi at the pin: no ok version line: $out"
grep -qE "^python gate $ppin ok  /.* \(venv, pidfd_open; \.python-version\)$" <<<"$out" \
  && grep -qE '^python3 version 3\.[0-9]+\.[0-9]+ ok  /.*/python3 \(3\.11 or later, the kit scripts\)$' <<<"$out" \
  || fail "gate Python at the pin and box python3: no ok lines: $out"
# The gate's Python not installed (no managed install, the box's own Pythons not taken): named with the fix, exit 1;
# `just check` in a copy of the kit refuses before any item, naming it.
fix="uv python install --no-bin $ppin (--no-bin: no python3.X link in ~/.local/bin, which would change"
UV_PYTHON_INSTALL_DIR="$t/nopy" UV_PYTHON_PREFERENCE=only-managed check 1 "$gh_target" ""
grep -qF "python gate $ppin MISSING (.python-version); $fix" <<<"$out" || fail "gate Python not installed: no MISSING line naming the fix: $out"
mkdir -p "$t/kit"; (cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t/kit"
rc=0; gout="$(cd "$t/kit" && UV_PYTHON_INSTALL_DIR="$t/nopy" UV_PYTHON_PREFERENCE=only-managed just check 2>&1)" || rc=$?
[[ "$rc" != 0 ]] && grep -qF "check-tests: the gate's Python $ppin (.python-version) is not installed; install it once, with network: $fix" <<<"$gout" \
  || fail "just check without the gate's Python: not refused naming the fix (exit $rc): $gout"
# A box python3 older than 3.11 first on PATH (it answers --version; the recipe's other python3 calls run the real one).
o="$t/py310"; mkdir -p "$o"; printf '#!/bin/sh\n[ "$1" = --version ] && { echo "Python 3.10.12"; exit 0; }\nexec "%s" "$@"\n' "$real_py3" >"$o/python3"; chmod +x "$o/python3"
pre="$o" check 1 "$gh_target" ""; rm -rf "$o"
grep -qx "python3 WRONG VERSION $o/python3 reports 3.10.12, want 3.11 or later (the kit scripts read TOML with tomllib); install Python 3.11 or later as the box python3 (Debian 12, Ubuntu 24.04: apt install python3), first on PATH" <<<"$out" \
  || fail "box python3 3.10: no WRONG VERSION line naming 3.11 and the fix: $out"
printf '#!/bin/sh\necho 0.0.1\n' >"$t/bin/pi"
check 1 "$gh_target" ""
grep -qx "pi     WRONG VERSION $t/bin/pi reports 0.0.1, want $pin (pi-version); npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin" <<<"$out" \
  || fail "pi 0.0.1: no WRONG VERSION line naming the pin and the install command: $out"
printf '#!/bin/sh\necho %s\n' "$pin" >"$t/bin/pi"
! grep -qi '^browser' <<<"$out" || fail "GitHub target without qc.toml [browser] has a browser line: $out"
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
grep -qx "mise   just 0.0.1 MISSING ($mise_target/mise.lock); mise -C $mise_target install --locked" <<<"$out" \
  || fail "created repo, just at a pin not installed: no MISSING line naming the install: $out"
# Browser target: qc.toml declares the headless browser at a Playwright pin.
br_target="$t/browser"; git init -q "$br_target"
printf 'format = 1\n[entry]\ncommand = "app"\n[services]\n[fixture]\n[values]\n[browser]\nplaywright = "1.64.1"\n' >"$br_target/qc.toml"
folder="$t/home/.local/share/octo-feather/ms-playwright/1.64.1"
check 1 "$br_target" ""
grep -qx "browser MISSING (want Playwright 1.64.1 headless Chromium shell in $folder); install: PLAYWRIGHT_BROWSERS_PATH=$folder npx -y playwright@1.64.1 install --only-shell chromium" <<<"$out" \
  || fail "browser target without the browser: no MISSING line naming the pin, folder and install command: $out"
mkdir -p "$folder/chromium_headless_shell-1248"; touch "$folder/chromium_headless_shell-1248/INSTALLATION_COMPLETE"
check 0 "$br_target" ""
grep -qx "browser ok  $folder/chromium_headless_shell-1248 (Playwright 1.64.1; PLAYWRIGHT_BROWSERS_PATH=$folder)" <<<"$out" \
  || fail "browser target, fake headless shell at the pin: not ok: $out"
mkdir -p "$t/home/.cache/d"; cp -r "$t/home/.local/share/octo-feather" "$t/home/.cache/d/"
data="$t/home/.cache/d" check 1 "$br_target" ""
grep -q "^browser UNREADABLE IN THE QC SANDBOX $t/home/.cache/d/octo-feather/ms-playwright/1.64.1 is under $t/home/.cache" <<<"$out" \
  || fail "browser folder under the masked cache folder: not refused: $out"
# agent-browser (spec remote#acceptance-install-agent-browser): the stub at 0.40.0 ok; another release WRONG VERSION; on a
# box without it, MISSING naming 0.40.0 and the npm install. Without it: each PATH dir holding one is mirrored minus it.
grep -qx 'agent-browser version 0.40.0 ok (agent-browser-version)' <<<"$out" || fail "agent-browser at the pin: no ok line: $out"
printf '#!/bin/sh\necho "agent-browser 0.39.4"\n' >"$t/bin/agent-browser"
check 1 "$gh_target" ""
grep -qx "agent-browser WRONG VERSION $t/bin/agent-browser reports 0.39.4, want 0.40.0 (agent-browser-version); npm install -g agent-browser@0.40.0 (then agent-browser doctor --offline; no Chrome found: agent-browser install)" <<<"$out" \
  || fail "agent-browser 0.39.4: no WRONG VERSION line naming 0.40.0 and the install: $out"
rm "$t/bin/agent-browser"; saved="$clean"; clean="$(hide agent-browser "$saved")"
check 1 "$gh_target" ""; clean="$saved"
grep -qx 'agent-browser MISSING (want 0.40.0, agent-browser-version); npm install -g agent-browser@0.40.0 (then agent-browser doctor --offline; no Chrome found: agent-browser install)' <<<"$out" \
  || fail "no agent-browser on PATH: not listed MISSING with 0.40.0 and the install: $out"
printf '#!/bin/sh\necho "agent-browser 0.40.0"\n' >"$t/bin/agent-browser"; chmod +x "$t/bin/agent-browser"
echo "install-check: ok (gate Python $ppin ok, not installed MISSING naming uv python install --no-bin and just check refusing, exit 1; box python3 ok, 3.10 WRONG VERSION, exit 1; linear hidden alone, mise in its dir ok; a stale node or mise first on PATH SHADOWED naming the pinned path and the fix, exit 1; agent-browser 0.40.0 ok, 0.39.4 WRONG VERSION, none MISSING naming 0.40.0 and npm install, exit 1; pi $pin (pi-version) ok, pi 0.0.1 WRONG VERSION naming the pin and npm install, exit 1; mise at its pin ok, 2000.1.1 named, exit 1; a created repo's mise.toml tools ok, MISSING named, exit 1; a repo the kit did not create gets no tool line; just checked at the kit lock in every target (ok, 0.0.1 WRONG VERSION); Linear target: linear missing names v3.1.0 and the install path, exit 1; at the pin ok; another release named; GitHub target never checks linear nor a browser; browser target: MISSING names Playwright 1.64.1, the folder and the install command, exit 1; fake shell at the pin ok; folder under ~/.cache refused)"
