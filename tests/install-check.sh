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
printf '#!/bin/sh\necho "linear 3.0.0"\n' >"$t/old/linear"; chmod +x "$t/bin/"* "$t/old/linear"
cp "$(command -v just)" "$t/bin/just"   # its own dir goes on the recipe's PATH: the test's, never one holding a linear
# PATH without any linear: every dir holding one is dropped (the recipe adds HOME/.local/bin: HOME is a fresh dir).
clean=""; IFS=: read -ra ds <<<"$PATH"; for d in "${ds[@]}"; do [[ -x "$d/linear" ]] || clean+=":$d"; done
lin_target="$t/linear"; gh_target="$t/github"
git init -q "$lin_target"; git init -q "$gh_target"; mkdir -p "$lin_target/sub"
cp "$kit/tests/fixtures/install-check/linear/.octo-feather.toml" "$lin_target/"
check() { # WANT DIR EXTRA_PATH [TARGET]: run in DIR; output in $out
  local rc=0; out="$(cd "$2" && env -u XDG_CACHE_HOME HOME="$t/home" XDG_DATA_HOME="${data:-$t/home/.local/share}" PATH="$t/bin${3:+:$3}$clean" \
    just -f "$kit/justfile" install-check ${4:+"$4"} 2>&1)" || rc=$?
  [[ "$rc" == "$1" ]] || fail "in $2 (PATH extra '${3:-}'): want exit $1, got $rc: $out"
}

check 1 "$lin_target/sub" ""
grep -q '^tracker linear ' <<<"$out" || fail "Linear target: no tracker line: $out"
grep -E '^linear MISSING \(want v3\.1\.0\)' <<<"$out" | grep -q 'releases/tag/v3\.1\.0' \
  && grep -q 'npx @schpet/linear-cli' <<<"$out" || fail "Linear target without linear: not listed missing with v3.1.0 and the install path: $out"
check 0 "$t" "$kit/.agents/skills/linear/scripts" "$lin_target"
grep -qE '^linear ok  .*/linear \(v3\.1\.0\)$' <<<"$out" || fail "Linear target, fake linear at the pin: not ok: $out"
check 1 "$lin_target" "$t/old"
grep -qE '^linear WRONG VERSION .* reports 3\.0\.0, want v3\.1\.0; .*npx @schpet/linear-cli' <<<"$out" || fail "Linear target, linear 3.0.0: $out"
check 0 "$gh_target" ""
grep -q '^tracker github-issues ' <<<"$out" && ! grep -qi linear <<<"$out" || fail "GitHub target checked linear: $out"
grep -qx "pi     version $pin ok (pi-version)" <<<"$out" || fail "pi at the pin: no ok version line: $out"
printf '#!/bin/sh\necho 0.0.1\n' >"$t/bin/pi"
check 1 "$gh_target" ""
grep -qx "pi     WRONG VERSION $t/bin/pi reports 0.0.1, want $pin (pi-version); npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin" <<<"$out" \
  || fail "pi 0.0.1: no WRONG VERSION line naming the pin and the install command: $out"
printf '#!/bin/sh\necho %s\n' "$pin" >"$t/bin/pi"
! grep -qi browser <<<"$out" || fail "GitHub target without qc.toml [browser] has a browser line: $out"
# just at the kit's pin (just-version): the just on PATH (the copy above) ok; a just reporting another release: WRONG VERSION
# naming the pin and its release page, exit 1. The stub forwards all but --version to the real just (the gate guard asks it).
jpin="$(tr -d '[:space:]' <"$kit/just-version")"
check 0 "$gh_target" ""
grep -qx "just   version $jpin ok (just-version)" <<<"$out" || fail "just at the pin: no ok version line: $out"
o="$t/home/.local/bin"; mkdir -p "$o"   # first on the recipe's PATH (the justfile's export)
printf '#!/bin/sh\n[ "$1" = --version ] && { echo "just 0.0.1"; exit 0; }\nexec "%s" "$@"\n' "$t/bin/just" >"$o/just"; chmod +x "$o/just"
check 1 "$gh_target" ""; rm -rf "$t/home/.local"
grep -qx "just   WRONG VERSION $o/just reports 0.0.1, want $jpin (just-version); install just $jpin: https://github.com/casey/just/releases/tag/$jpin" <<<"$out" \
  || fail "just 0.0.1: no WRONG VERSION line naming the pin and its release: $out"
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
echo "install-check: ok (pi $pin (pi-version) ok, pi 0.0.1 WRONG VERSION naming the pin and npm install, exit 1; just $jpin (just-version) ok, just 0.0.1 WRONG VERSION naming the pin, exit 1; Linear target: linear missing names v3.1.0 and the install path, exit 1; at the pin ok; another release named; GitHub target never checks linear nor a browser; browser target: MISSING names Playwright 1.64.1, the folder and the install command, exit 1; fake shell at the pin ok; folder under ~/.cache refused)"
