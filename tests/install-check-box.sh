#!/usr/bin/env bash
# Integration test for `just install-check`, its box facts section (#508; setup tests/lib/install-check.sh):
#   Box facts (#461), each probe a stub on PATH (uname -r, unshare, agent-browser doctor, ffmpeg) or a folder the test
#     makes (XDG_STATE_HOME, OCTO_FEATHER_KIT_INSTALL), never this box's values: kernel 6.12 ok, 6.1 TOO OLD naming the
#     upgrade; unshare -rm ok, refused FAILED naming its error; the state folder's lanes/ ok, absent MISSING naming
#     mkdir -p; the kit install clone on main ok (detached on main too), on another branch NOT ON MAIN naming git switch
#     main, no clone named with the fix; a detached worktree at main ok (the box's layout, also with
#     OCTO_FEATHER_KIT_INSTALL unset: the kit dir, octo-feather-lane's kit_install()), on a branch or off main NOT ON MAIN; agent-browser's Chrome outside the cache folder ok, under it
#     UNREADABLE IN THE QC SANDBOX, none MISSING, both naming agent-browser install; ffmpeg ok, absent OPTIONAL with
#     exit 0; the sharing MANUAL step always. herdr, gh, jq and git absent: MISSING with each install command, exit 1.
# Run by `just check`; setup tests/lib/install-check.sh.
# shellcheck source=tests/lib/install-check.sh
source "$(dirname "$0")/lib/install-check.sh"
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
# A worktree of the clone (the box's layout: the main checkout first in git worktree list, the install a detached
# worktree beside it, #422): detached at main ok; on a branch NOT ON MAIN naming switch --detach origin/main.
g -C "$kitinst" checkout -q main; g -C "$kitinst" worktree add -q --detach "$t/kitwt" main 2>/dev/null
kitinst="$t/kitwt" check 0 "$gh_target" ""
grep -qx "kit    ok  $t/kitwt on main (OCTO_FEATHER_KIT_INSTALL)" <<<"$out" || fail "kit install a detached worktree at main: not ok: $out"
g -C "$t/kitwt" switch -q -c wt; kitinst="$t/kitwt" check 1 "$gh_target" ""
grep -qx "kit    NOT ON MAIN $t/kitwt is on branch wt (OCTO_FEATHER_KIT_INSTALL; octo-feather-lane post-merge step 3 fast-forwards it); live install clones stay on main (work in a git worktree): git -C $t/kitwt switch --detach origin/main" <<<"$out" \
  || fail "kit install a worktree on a branch: no NOT ON MAIN line naming switch --detach origin/main: $out"
# OCTO_FEATHER_KIT_INSTALL unset: the install is the kit dir the recipe runs from, as octo-feather-lane's kit_install()
# says (post-merge step 3 runs install-check there): a kit copy laid out as the box's (a clone's main checkout first,
# the install a detached worktree at main, its tools the kit's node_modules) is ok there; with a commit off main, NOT
# ON MAIN, exit 1.
# The kit copy the box's layout below is made of: its tracked files.
mkdir -p "$t/kit"; (cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t/kit"
g -C "$t/kit" init -q; g -C "$t/kit" add -A; g -C "$t/kit" commit -q -m kit; g clone -q --bare "$t/kit" "$t/kit-o.git"
g clone -q "$t/kit-o.git" "$t/kitmain"; g -C "$t/kitmain" worktree add -q --detach "$t/kitlive" main 2>/dev/null
ln -s "$kit/node_modules" "$t/kitlive/node_modules"
live() { # WANT: install-check from the kit install's own justfile, OCTO_FEATHER_KIT_INSTALL unset; output in $out
  local rc=0; out="$(cd "$gh_target" && env -u OCTO_FEATHER_KIT_INSTALL -u XDG_CACHE_HOME -u AGENT_BROWSER_EXECUTABLE_PATH -u SPEC_CHAT_CLONE HOME="$t/home" XDG_STATE_HOME="$t/state" XDG_DATA_HOME="$t/home/.local/share" PATH="$t/bin:$shims$clean" \
    just -f "$t/kitlive/justfile" install-check 2>&1)" || rc=$?
  [[ "$rc" == "$1" ]] || fail "kit install a detached worktree, OCTO_FEATHER_KIT_INSTALL unset: want exit $1, got $rc: $out"
}
live 0; grep -qx "kit    ok  $t/kitlive on main (the kit dir)" <<<"$out" || fail "the box's layout, OCTO_FEATHER_KIT_INSTALL unset: kit line not ok: $out"
g -C "$t/kitlive" commit -q --allow-empty -m off; live 1
grep -qx "kit    NOT ON MAIN $t/kitlive is on a detached HEAD off main (the kit dir; octo-feather-lane post-merge step 3 fast-forwards it); live install clones stay on main (work in a git worktree): git -C $t/kitlive switch --detach origin/main" <<<"$out" \
  || fail "the box's layout, a commit off main: no NOT ON MAIN line: $out"
mkdir -p "$t/noclone"; kitinst="$t/noclone" check 1 "$gh_target" ""
url="$(git -C "$kit" config --get remote.origin.url || echo '<kit url>')"   # a kit copy with no origin (tests/user-mise.sh): the placeholder
grep -qxF "kit    NOT A CLONE $t/noclone (OCTO_FEATHER_KIT_INSTALL; octo-feather-lane post-merge step 3 fast-forwards it); git clone $url $t/noclone, or set OCTO_FEATHER_KIT_INSTALL to the install clone" <<<"$out" \
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
nomodel
echo "install-check-box: ok (box facts: kernel, userns, state, kit install (a clone or a detached worktree at main, OCTO_FEATHER_KIT_INSTALL set or not), agent-browser Chrome, ffmpeg each ok and each gap named with its fix, the sharing step printed; herdr, gh, jq, git MISSING with their install; no model call)"
