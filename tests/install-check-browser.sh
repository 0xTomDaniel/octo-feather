#!/usr/bin/env bash
# Integration test for `just install-check`, its browser section (#508; setup tests/lib/install-check.sh):
#   browser target (qc.toml [browser] playwright pin, spec remote#acceptance-install-browser), no browser folder:
#     browser MISSING naming the pin, the box folder and the install command, exit 1; a fake headless shell in
#     the folder at that pin: ok, exit 0; the folder under the cache folder the qc sandbox masks: refused, exit 1;
#     GitHub target (no qc.toml [browser]): no browser line. No browser is downloaded: the folder is faked.
#   agent-browser (spec remote#acceptance-install-agent-browser), a stub: at 0.40.0 ok; 0.39.4 WRONG VERSION; none on
#     PATH: MISSING naming 0.40.0 and the npm install, exit 1.
#   PATH (#422) in the kit itself: a stale node in a system dir before mise's shims only a NOTE, exit 0; one in a
#     dir ahead of mise's SHADOWED, exit 1; shims first ok (the kit's [browser] pin is the fake shell).
# Run by `just check`; setup tests/lib/install-check.sh.
# shellcheck source=tests/lib/install-check.sh
source "$(dirname "$0")/lib/install-check.sh"
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
nomodel
echo "install-check-browser: ok (browser target: MISSING names Playwright 1.64.1, the folder and the install command, exit 1; fake shell at the pin ok; folder under ~/.cache refused; in the kit a stale node in a system dir before mise's shims a NOTE only, exit 0, one ahead of mise's dirs SHADOWED, shims first ok; agent-browser 0.40.0 ok, 0.39.4 WRONG VERSION, none MISSING naming 0.40.0 and npm install, exit 1; no model call)"
