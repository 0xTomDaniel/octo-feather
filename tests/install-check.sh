#!/usr/bin/env bash
# Integration test for `just install-check` per target (spec remote#host-tools, #acceptance-install-linear), offline:
# the kit's justfile run in a target (`just -f KIT/justfile install-check`, or TARGET as the argument).
# One section of the `just install-check` test per gate item (#508): tests/install-check.sh and each tests/install-check-*.sh (mise, browser, box, models).
#   Linear target (tests/fixtures/install-check/linear), no linear on PATH: exit 1, linear listed missing with the
#     pinned v3.1.0 and the install path (release binary, or npx @schpet/linear-cli);
#   the testkit's Linear stand-in on PATH answering `linear --version` from a tape
#     (tests/fixtures/linear-install-check): at the pin, linear ok, exit 0; another release (3.0.0): listed with the
#     wanted v3.1.0, exit 1;
#   GitHub target (no config): linear never checked;
#   pi at the kit's pin (pi-version): its version line ok; pi reporting another release: WRONG VERSION naming
#     the pin and the npm install command, exit 1;
#   PATH (#422 item 10): linear is hidden alone (its dir mirrored minus it), so a mise sharing its dir stays ok.
#   Python (owner ruling #422, #261): the gate's Python at the kit's .python-version, found through uv: ok with venv and
#     pidfd_open; none installed: MISSING naming `uv python install --no-bin`, exit 1, and `just check` in a copy of the
#     kit refuses, naming it. The box python3 at 3.11 or later ok; a python3 reporting 3.10: WRONG VERSION, exit 1.
#     Uses the box's uv Python installs (UV_PYTHON_INSTALL_DIR kept while HOME is a fresh dir); installs nothing.
# Run by `just check`; setup tests/lib/install-check.sh.
# shellcheck source=tests/lib/install-check.sh
source "$(dirname "$0")/lib/install-check.sh"

check 1 "$lin_target/sub" ""
grep -q '^tracker linear ' <<<"$out" || fail "Linear target: no tracker line: $out"
grep -qx "mise   version $mpin ok (mise-version)" <<<"$out" || fail "linear hidden from a dir it shares with mise: mise gone too: $out"
grep -E '^linear MISSING \(want v3\.1\.0\)' <<<"$out" | grep -q 'releases/tag/v3\.1\.0' \
  && grep -q 'npx @schpet/linear-cli' <<<"$out" || fail "Linear target without linear: not listed missing with v3.1.0 and the install path: $out"
tape() { mkdir -p "$t/fl/$1"; cp "$kit/tests/fixtures/linear-install-check/$1/tape.json" "$t/fl/$1/"; echo "$t/fl/$1"; }   # a FAKE_LINEAR dir
FAKE_LINEAR="$(tape pin)" check 0 "$t" "$kit/tests/gate/kit/testkit/linear" "$lin_target"
grep -qE '^linear ok  .*/linear \(v3\.1\.0\)$' <<<"$out" || fail "Linear target, linear at the pin: not ok: $out"
FAKE_LINEAR="$(tape old)" check 1 "$lin_target" "$kit/tests/gate/kit/testkit/linear"
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
nomodel
echo "install-check: ok (Linear target: linear missing names v3.1.0 and the install path, exit 1; at the pin ok; another release named; linear hidden alone, mise in its dir ok; GitHub target never checks linear nor a browser; gate Python $ppin ok, not installed MISSING naming uv python install --no-bin and just check refusing, exit 1; box python3 ok, 3.10 WRONG VERSION, exit 1; pi $pin (pi-version) ok, pi 0.0.1 WRONG VERSION naming the pin and npm install, exit 1; no model call)"
