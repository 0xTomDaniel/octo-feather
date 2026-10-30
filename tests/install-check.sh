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
#     naming it, the pinned path and the fix, exit 1. pi and agent-browser installed into the target's mise node (their
#     npm fix lines, #463) stay pinned by their version files: another copy at the pin first on PATH is ok. In the kit,
#     judged on the PATHs the kit runs from (its recipes', a pane's): a stale node in a system dir before mise's shims
#     only a NOTE, exit 0; one in a dir ahead of mise's SHADOWED, exit 1; shims first ok, no NOTE.
#   Python (owner ruling #422, #261): the gate's Python at the kit's .python-version, found through uv: ok with venv and
#     pidfd_open; none installed: MISSING naming `uv python install --no-bin`, exit 1, and `just check` in a copy of the
#     kit refuses, naming it. The box python3 at 3.11 or later ok; a python3 reporting 3.10: WRONG VERSION, exit 1.
#     Uses the box's uv Python installs (UV_PYTHON_INSTALL_DIR kept while HOME is a fresh dir); installs nothing.
#   Box facts (#461), each probe a stub on PATH (uname -r, unshare, agent-browser doctor, ffmpeg) or a folder the test
#     makes (XDG_STATE_HOME, OCTO_FEATHER_KIT_INSTALL), never this box's values: kernel 6.12 ok, 6.1 TOO OLD naming the
#     upgrade; unshare -rm ok, refused FAILED naming its error; the state folder's lanes/ ok, absent MISSING naming
#     mkdir -p; the kit install clone on main ok (detached on main too), on another branch NOT ON MAIN naming git switch
#     main, a worktree or no clone named with the fix; agent-browser's Chrome outside the cache folder ok, under it
#     UNREADABLE IN THE QC SANDBOX, none MISSING, both naming agent-browser install; ffmpeg ok, absent OPTIONAL with
#     exit 0; the sharing MANUAL step always. herdr, gh, jq and git absent: MISSING with each install command, exit 1.
#   Review service (#462): systemctl a stub: active and enabled ok; inactive, failed or no systemctl named with Spec
#     Chat's installer --public <vm>.exe.xyz --service, exit 1; a models MANUAL line names just install-check-models
#     and no install-check run calls pi -p. just install-check-models: the stub tests/fixtures/install-check/pi, asserted
#     first on PATH, plays the proxy: right keys ok per role model with its roles and for the judgment model (a classify
#     call); a key with trailing terminal characters REJECTED; a proxy not answering UNREACHABLE; a judgment model Pi does
#     not list FAILED; the key never printed nor on pi's command line.
# herdr, pi and gh are stubs (gh signed in, pi at the pin unless swapped), so only the tracker or pi line decides
# the exit. Run by `just check`.
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
# The PATHs the kit runs its tools from, in the kit itself (post-merge step 3 runs install-check there from the
# director's pane, #422): its recipes' PATH (the justfile puts mise's dirs before the first system dir) and a pane's
# (pi-role's with_mise). (a) A caller PATH with a system dir holding stale launchers before mise's shims (a shell
# started before the shims went first): ok and a NOTE line naming the launcher, the kit unaffected, exit 0. (b) A stale
# launcher in a dir the caller puts ahead (the justfile and pi-role keep such dirs first): SHADOWED, exit 1. (c) mise's
# shims first: ok, no NOTE. The stale /usr/local/bin is a scratch dir bound over it in a user namespace (unshare -rm,
# as tests/qc.sh needs), so no box dir is touched; the kit's [browser] pin is the fake shell above.
sysd="$t/sysbin"; mkdir -p "$sysd"; printf '#!/bin/sh\necho v18.0.0\n' >"$sysd/node"; chmod +x "$sysd/node"
[[ -d /usr/local/bin ]] || fail "no /usr/local/bin to bind the stale launchers over"
inkit() { # WANT CALLER_PATH: install-check in the kit, /usr/local/bin holding only a stale node; output in $out
  local rc=0; out="$(cd "$kit" && env -u XDG_CACHE_HOME -u AGENT_BROWSER_EXECUTABLE_PATH -u SPEC_CHAT_CLONE HOME="$t/home" XDG_STATE_HOME="$t/state" OCTO_FEATHER_KIT_INSTALL="$kitinst" XDG_DATA_HOME="$t/home/.local/share" PATH="$2" \
    "$real_unshare" -rm sh -c 'mount --bind "$1" /usr/local/bin && shift && exec "$@"' sh "$sysd" just install-check 2>&1)" || rc=$?
  [[ "$rc" == "$1" ]] || fail "in the kit (PATH $2): want exit $1, got $rc: $out"
}
inkit 0 "$t/bin:/usr/local/bin:$shims$clean"
grep -qE "^path   node ok  /\S+/node \($kit/mise\.lock\)$" <<<"$out" && ! grep -q SHADOWED <<<"$out" \
  && grep -qE "^path   node NOTE /usr/local/bin/node comes first on your shell PATH, before the pinned $shims/node \($kit/mise\.lock\); the kit is unaffected: its recipes \(justfile\) and panes \(pi-role\) put mise first and run /\S+/node; to run the pinned one in this shell too, put $shims first on PATH$" <<<"$out" \
  || fail "stale node in a system dir before mise's shims: want node ok and a NOTE line only: $out"
o="$t/ahead"; mkdir -p "$o"; cp "$sysd/node" "$o/node"
inkit 1 "$o:$t/bin:/usr/local/bin:$shims$clean"
grep -qx "path   node SHADOWED $o/node comes first on PATH, before the pinned $shims/node ($kit/mise.lock); remove or rename $o/node, or put $shims first on PATH" <<<"$out" \
  || fail "stale node ahead of mise's dirs on the kit's PATHs: no SHADOWED line: $out"
rm -rf "$o"; inkit 0 "$t/bin:$shims:/usr/local/bin$clean"
grep -qE "^path   node ok  " <<<"$out" && ! grep -qE "^path   \S+ (NOTE|SHADOWED) " <<<"$out" || fail "mise's shims first: want ok, no NOTE: $out"
mkdir -p "$t/home/.cache/d"; cp -r "$t/home/.local/share/octo-feather" "$t/home/.cache/d/"
data="$t/home/.cache/d" check 1 "$br_target" ""
grep -q "^browser UNREADABLE IN THE QC SANDBOX $t/home/.cache/d/octo-feather/ms-playwright/1.64.1 is under $t/home/.cache" <<<"$out" \
  || fail "browser folder under the masked cache folder: not refused: $out"
# agent-browser (spec remote#acceptance-install-agent-browser): the stub at 0.40.0 ok; another release WRONG VERSION; on a
# box without it, MISSING naming 0.40.0 and the npm install. Without it: each PATH dir holding one is mirrored minus it.
grep -qx 'agent-browser version 0.40.0 ok (agent-browser-version)' <<<"$out" || fail "agent-browser at the pin: no ok line: $out"
ab 0.39.4
check 1 "$gh_target" ""
grep -qx "agent-browser WRONG VERSION $t/bin/agent-browser reports 0.39.4, want 0.40.0 (agent-browser-version); npm install -g agent-browser@0.40.0 (then agent-browser doctor --offline; no Chrome found: agent-browser install)" <<<"$out" \
  || fail "agent-browser 0.39.4: no WRONG VERSION line naming 0.40.0 and the install: $out"
# mise's shims too: an agent-browser npm put in mise's node has a shim there (#463).
rm "$t/bin/agent-browser"; saved="$clean"; clean="$(hide agent-browser "$saved")"; sshims="$shims"; shims="$(hide agent-browser "$shims")"; shims="${shims#:}"
check 1 "$gh_target" ""; clean="$saved"; shims="$sshims"
grep -qx 'agent-browser MISSING (want 0.40.0, agent-browser-version); npm install -g agent-browser@0.40.0 (then agent-browser doctor --offline; no Chrome found: agent-browser install)' <<<"$out" \
  || fail "no agent-browser on PATH: not listed MISSING with 0.40.0 and the install: $out"
ab 0.40.0
# Box facts (#461): every probe at a good value, each line ok and the manual sharing step printed, exit 0.
check 0 "$gh_target" ""
grep -qx 'kernel 6.12.0 ok (6.6 or later, the qc sandbox)' <<<"$out" && grep -qx 'userns ok (unshare -rm true, the qc sandbox)' <<<"$out" \
  && grep -qx "state  ok  $t/state/octo-feather (octo-feather-state)" <<<"$out" && grep -qx "kit    ok  $kitinst on main (OCTO_FEATHER_KIT_INSTALL)" <<<"$out" \
  && grep -qx "agent-browser browser ok  $okchrome (outside $t/home/.cache)" <<<"$out" && grep -qx "ffmpeg ok  $t/bin/ffmpeg (optional: agent-browser video recording)" <<<"$out" \
  || fail "box facts at good values: not every ok line: $out"
grep -qE '^sharing MANUAL exe\.dev Private sharing cannot be checked from inside the box; on the exe\.dev VM that hosts reviews, from your own machine: ssh exe\.dev share set-private \S+ \(never share set-public: a public share has no login\)$' <<<"$out" \
  || fail "no manual sharing step: $out"
# A kernel older than 6.6: TOO OLD naming the upgrade, exit 1.
echo 6.1.0 >"$t/kver"; check 1 "$gh_target" ""; echo 6.12.0 >"$t/kver"
grep -qE '^kernel 6\.1\.0 TOO OLD, want 6\.6 or later \(the qc sandbox overlay needs tmpfs user xattrs: scripts/octo-feather-qc-sandbox\); boot a 6\.6 or later kernel, then reboot \(Debian 12: .*sudo apt install -t bookworm-backports linux-image-\$\(dpkg --print-architecture\); Ubuntu 22\.04: sudo apt install linux-generic-hwe-22\.04\)$' <<<"$out" \
  || fail "kernel 6.1.0: no TOO OLD line naming the upgrade: $out"
# unshare -rm refused: FAILED naming its error and a fix (the sysctl that turns them off here, or the container), exit 1.
touch "$t/userns-off"; check 1 "$gh_target" ""; rm "$t/userns-off"
grep -qE '^userns FAILED unshare -rm true: unshare: write failed /proc/self/uid_map: Operation not permitted \(the qc sandbox runs its judge in unprivileged user namespaces, #404\); (allow them: printf ".*" \| sudo tee /etc/sysctl\.d/60-octo-feather-userns\.conf && sudo sysctl --system|no sysctl here turns them off .*)$' <<<"$out" \
  || fail "user namespaces refused: no FAILED line naming the error and the fix: $out"
# The state folder without lanes/: MISSING naming mkdir -p, exit 1.
rmdir "$t/state/octo-feather/lanes"; check 1 "$gh_target" ""; mkdir "$t/state/octo-feather/lanes"
grep -qx "state  MISSING $t/state/octo-feather/lanes (the session state folder, octo-feather-state); mkdir -p $t/state/octo-feather/lanes" <<<"$out" \
  || fail "state folder without lanes/: no MISSING line naming mkdir -p: $out"
# The kit install: detached on main ok; on another branch NOT ON MAIN naming git switch main; a worktree, and a folder
# that is no clone, each named with the fix; exit 1.
g -C "$kitinst" checkout -q --detach; check 0 "$gh_target" ""
grep -qx "kit    ok  $kitinst on main (OCTO_FEATHER_KIT_INSTALL)" <<<"$out" || fail "kit install detached on main: not ok: $out"
g -C "$kitinst" checkout -q -b feat; check 1 "$gh_target" ""
grep -qx "kit    NOT ON MAIN $kitinst is on branch feat (OCTO_FEATHER_KIT_INSTALL; octo-feather-lane post-merge step 3 fast-forwards it); live install clones stay on main (work in a git worktree): git -C $kitinst switch main" <<<"$out" \
  || fail "kit install on a branch: no NOT ON MAIN line naming git switch main: $out"
g -C "$kitinst" checkout -q main; g -C "$kitinst" worktree add -q "$t/kitwt" -b wt 2>/dev/null
kitinst="$t/kitwt" check 1 "$gh_target" ""
grep -qx "kit    A WORKTREE $t/kitwt, not the install clone (OCTO_FEATHER_KIT_INSTALL; octo-feather-lane post-merge step 3 fast-forwards it); set OCTO_FEATHER_KIT_INSTALL to the install clone (git -C $t/kitwt worktree list: its first line)" <<<"$out" \
  || fail "kit install a worktree: not named: $out"
mkdir -p "$t/noclone"; kitinst="$t/noclone" check 1 "$gh_target" ""
grep -qE "^kit    NOT A CLONE $t/noclone \(OCTO_FEATHER_KIT_INSTALL; octo-feather-lane post-merge step 3 fast-forwards it\); git clone \S+ $t/noclone, or set OCTO_FEATHER_KIT_INSTALL to the install clone$" <<<"$out" \
  || fail "kit install not a clone: no NOT A CLONE line naming git clone: $out"
# agent-browser's own Chrome under the cache folder the qc sandbox masks, and none found: each named with
# agent-browser install, exit 1.
abfix="agent-browser install (Chrome for Testing into $t/home/.agent-browser/browsers, which agent-browser searches first; drop any AGENT_BROWSER_EXECUTABLE_PATH, or executablePath in ~/.agent-browser/config.json, naming another)"
chrome "$t/home/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome"; check 1 "$gh_target" ""
grep -qxF "agent-browser browser UNREADABLE IN THE QC SANDBOX $t/home/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome is under $t/home/.cache, which the sandbox masks; $abfix" <<<"$out" \
  || fail "agent-browser Chrome under the cache folder: not refused with the fix: $out"
chrome ""; check 1 "$gh_target" ""; chrome "$okchrome"
grep -qxF "agent-browser browser MISSING (agent-browser doctor --offline names no Chrome); $abfix" <<<"$out" \
  || fail "agent-browser without Chrome: no MISSING line with the fix: $out"
# ffmpeg absent: an OPTIONAL line naming the install, and the check still passes.
mv "$t/bin/ffmpeg" "$t/ffmpeg"; saved="$clean"; clean="$(hide ffmpeg "$saved")"
check 0 "$gh_target" ""; clean="$saved"; mv "$t/ffmpeg" "$t/bin/ffmpeg"
grep -qx 'ffmpeg OPTIONAL not installed; only agent-browser video recording needs it, the check passes; to record video: sudo apt install ffmpeg' <<<"$out" \
  || fail "no ffmpeg: no OPTIONAL line naming the install, or the check failed: $out"
# herdr, gh, jq and git absent: each MISSING with its official install command, exit 1.
mkdir -p "$t/aside"; mv "$t/bin/herdr" "$t/bin/gh" "$t/aside/"; saved="$clean"; clean="$(hide "herdr gh jq git" "$saved")"
check 1 "$gh_target" ""; clean="$saved"; mv "$t/aside/"* "$t/bin/"
grep -qxF 'herdr  MISSING; curl -fsSL https://herdr.dev/install.sh | sh' <<<"$out" \
  && grep -qxF 'jq     MISSING; sudo apt install jq (Debian, Ubuntu)' <<<"$out" && grep -qxF 'git    MISSING; sudo apt install git (Debian, Ubuntu)' <<<"$out" \
  && grep -qE "^gh     MISSING; \(Debian, Ubuntu: GitHub CLI's apt repository\) .*https://cli\.github\.com/packages stable main.* && sudo apt install gh -y$" <<<"$out" \
  || fail "herdr, gh, jq, git absent: not each MISSING with its install command: $out"
# The review service (spec remote#review-service, #review-setup): active and enabled ok; inactive or not installed
# NOT RUNNING, no systemctl MISSING, each naming Spec Chat's installer with --public <vm>.exe.xyz --service, exit 1.
review_fix="$t/home/src/spec-chat/scripts/install-spec-chat --review $kit/docs/specs/index.spec.html --public \S+\.exe\.xyz --service \(remote#review-setup\)"
check 0 "$gh_target" ""
grep -qx "review ok  spec-chat-review.service active, enabled (Spec Chat's review service, systemd --user)" <<<"$out" || fail "review service up: no ok line: $out"
# The model check is its own recipe (spec remote#host-models): one line names it, and no run above called a model.
grep -qx 'models MANUAL not checked here (no model call); at box setup and after a model key change: just install-check-models' <<<"$out" \
  || fail "no line naming just install-check-models: $out"
! grep -qE '(^| )(-p|--print)( |$)' "$t/pi-calls" || fail "install-check called a model: $(cat "$t/pi-calls")"
printf 'ActiveState=inactive\nUnitFileState=\n' >"$t/unit"; check 1 "$gh_target" ""
grep -qxE "review NOT RUNNING spec-chat-review\.service is inactive, not installed \(want active, enabled: the systemd user service box setup installs\); $review_fix" <<<"$out" \
  || fail "review service not installed: no NOT RUNNING line naming the installer: $out"
printf 'ActiveState=failed\nUnitFileState=enabled\n' >"$t/unit"; check 1 "$gh_target" ""
grep -qxE "review NOT RUNNING spec-chat-review\.service is failed, enabled .*; $review_fix" <<<"$out" || fail "review service failed: not named: $out"
printf 'ActiveState=active\nUnitFileState=enabled\n' >"$t/unit"
mv "$t/bin/systemctl" "$t/systemctl"; saved="$clean"; clean="$(hide systemctl "$saved")"
check 1 "$gh_target" ""; clean="$saved"; mv "$t/systemctl" "$t/bin/systemctl"
grep -qxE "review MISSING no systemctl: the review service runs as a systemd user service \(spec-chat-review\.service\); on a systemd box: $review_fix" <<<"$out" \
  || fail "no systemctl: no MISSING line naming the installer: $out"
# just install-check-models (spec remote#host-models): the stub pi (tests/fixtures/install-check/pi) plays the model
# proxy; it is first on PATH, which the recipe's own pi line proves before any probe case. Each model a role file names
# answers one print-mode call, the judgment model (evals/judgment-model.json) one classify call through octo-feather-qa's
# bench extension: right keys ok; a key with trailing terminal characters REJECTED (a role model's in models.json, the
# judgment model's in auth.json); a proxy that does not answer UNREACHABLE; a judgment model Pi does not list FAILED;
# each with its users and the fix, the key never printed nor on a command line.
mkdir -p "$t/mbin" "$t/pi-agent"; cp "$kit/tests/fixtures/install-check/pi" "$t/mbin/pi"
issued="sk-proxy-0123456789abcdefghijklmnopqrstuv"; printf '%s' "$issued" >"$t/issued"
judge="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["model"])' "$kit/evals/judgment-model.json")"
jprov="${judge%%/*}"
keys() { # ANTHROPIC_KEY OPENAI_BASE JUDGE_KEY: Pi's provider config (models.json) and stored key (auth.json)
  python3 -c 'import json, sys; json.dump({"providers": {"anthropic": {"baseUrl": "https://proxy.example/", "apiKey": sys.argv[1]}, "openai": {"baseUrl": sys.argv[3], "apiKey": sys.argv[2]}}}, open(sys.argv[4], "w")); json.dump({sys.argv[7]: {"type": "api_key", "key": sys.argv[5]}}, open(sys.argv[6], "w"))' \
    "$1" "$issued" "$2" "$t/pi-agent/models.json" "$3" "$t/pi-agent/auth.json" "$jprov"; }
models() { # WANT: run the recipe from $t with the stub first on PATH; output in $out
  local rc=0; : >"$t/pi-calls"
  out="$(cd "$t" && PI_CODING_AGENT_DIR="$t/pi-agent" PI_STUB_LOG="$t/pi-calls" PI_STUB_ISSUED="$t/issued" PI_STUB_CLASSIFIERS="${avail-$judge}" HOME="$t/home" PATH="$t/mbin:$PATH" \
    just -f "$kit/justfile" install-check-models 2>&1)" || rc=$?
  [[ "$rc" == "$1" ]] || fail "install-check-models: want exit $1, got $rc: $out"
  ! grep -qF "$issued" <<<"$out" && ! grep -qF "$issued" "$t/pi-calls" || fail "a key was printed or passed on a command line: $out $(cat "$t/pi-calls")"
}
[[ "$(PATH="$t/mbin:$PATH" command -v pi)" == "$t/mbin/pi" ]] || fail "stub pi is not first on PATH"
roles() { grep -lx "model: $1" "$kit"/agents/*.md | xargs -n1 basename | sed 's/\.md$//' | paste -sd, - | sed 's/,/, /g'; }
ra="$(roles anthropic/claude-opus-5-5)"; ro="$(roles openai/gpt-6.1-sol)"
[[ -n "$ra" && -n "$ro" && -n "$judge" && -z "$(roles "$judge")" ]] \
  || fail "the role files no longer name anthropic/claude-opus-5-5 and openai/gpt-6.1-sol, or name the judgment model $judge: update this test"
jwho="judgment model (evals/judgment-model.json): the advisory judge, judgment benches"
keys "$issued" "https://proxy.example/v1" "$issued"; models 0
grep -qx "models pi $t/mbin/pi (one short call per role model and the judgment model, no tools; Pi reads each key from $t/pi-agent/models.json, $t/pi-agent/auth.json or its environment)" <<<"$out" \
  || fail "install-check-models did not resolve the stub pi first: $out"
calls() { python3 -c 'import json, sys; [print(" ".join(json.loads(l))) for l in open(sys.argv[1])]' "$t/pi-calls"; }
grep -qx "model  anthropic/claude-opus-5-5 ok (roles $ra)" <<<"$out" && grep -qx "model  openai/gpt-6.1-sol ok (roles $ro)" <<<"$out" \
  && grep -qxF "model  $judge ok ($jwho)" <<<"$out" \
  && [[ "$(calls | grep -c '^-p --mode json ')" == 2 && "$(calls | grep -c ' -p /octo-feather-bench ')" == 1 && "$(wc -l <"$t/pi-calls")" == 3 ]] \
  || fail "right keys: not one ok line and one call per role model and the judgment model: $out $(cat "$t/pi-calls")"
keys "$issued"$'\e[201~' "https://proxy.example/v1" "$issued"; models 1
grep -qx "model  anthropic/claude-opus-5-5 REJECTED key (401) for roles $ra (the key there ends in or holds whitespace or terminal characters); put the key the model proxy issued for provider anthropic in $t/pi-agent/models.json (providers.anthropic.apiKey) or its environment, exactly, no trailing characters, then rerun just install-check-models" <<<"$out" \
  && grep -qx "model  openai/gpt-6.1-sol ok (roles $ro)" <<<"$out" || fail "key with trailing junk: no REJECTED line with roles and fix: $out"
keys "$issued" "https://proxy.example/v1" "$issued"$'\n'; models 1
grep -qxF "model  $judge REJECTED key (401) for $jwho (the key there ends in or holds whitespace or terminal characters); put the key the model proxy issued for provider $jprov in $t/pi-agent/auth.json ($jprov.key) or its environment, exactly, no trailing characters, then rerun just install-check-models" <<<"$out" \
  || fail "judgment model key with a trailing newline: no REJECTED line with its users and fix: $out"
keys "$issued" "https://unreachable.example/v1" "$issued"; models 1
grep -qx "model  openai/gpt-6.1-sol UNREACHABLE (Connection error.) for roles $ro; the model proxy for provider openai did not answer: check this box reaches https://unreachable.example/v1 ($t/pi-agent/models.json, providers.openai.baseUrl) and the proxy is up, then rerun just install-check-models" <<<"$out" \
  || fail "proxy not answering: no UNREACHABLE line with roles and fix: $out"
keys "$issued" "https://proxy.example/v1" "$issued"; avail="" models 1
grep -qxF "model  $judge FAILED (Pi lists no classifier $judge: no key for its provider, or not in Pi catalog) for $jwho; run pi --model $judge -p ok by hand for the full error Pi gives, then rerun just install-check-models" <<<"$out" \
  || fail "judgment model Pi does not list: no FAILED line: $out"
echo "install-check: ok (review service ok, NOT RUNNING and no systemctl MISSING naming the installer; models MANUAL naming just install-check-models, no model call; install-check-models with a stub pi first on PATH: role models and the judgment model ok, trailing-junk keys REJECTED (models.json, auth.json), proxy UNREACHABLE, judgment model not listed FAILED, key never printed)"
echo "install-check: ok (box facts: kernel, userns, state, kit install, agent-browser Chrome, ffmpeg each ok and each gap named with its fix, the sharing step printed; herdr, gh, jq, git MISSING with their install; gate Python $ppin ok, not installed MISSING naming uv python install --no-bin and just check refusing, exit 1; box python3 ok, 3.10 WRONG VERSION, exit 1; linear hidden alone, mise in its dir ok; a stale node or mise first on PATH SHADOWED naming the pinned path and the fix, exit 1; in the kit a stale node in a system dir before mise's shims a NOTE only, exit 0, one ahead of mise's dirs SHADOWED, shims first ok; agent-browser 0.40.0 ok, 0.39.4 WRONG VERSION, none MISSING naming 0.40.0 and npm install, exit 1; pi $pin (pi-version) ok, pi 0.0.1 WRONG VERSION naming the pin and npm install, exit 1; mise at its pin ok, 2000.1.1 named, exit 1; a created repo's mise.toml tools ok, MISSING named, exit 1; a repo the kit did not create gets no tool line; just checked at the kit lock in every target (ok, 0.0.1 WRONG VERSION); Linear target: linear missing names v3.1.0 and the install path, exit 1; at the pin ok; another release named; GitHub target never checks linear nor a browser; browser target: MISSING names Playwright 1.64.1, the folder and the install command, exit 1; fake shell at the pin ok; folder under ~/.cache refused)"
