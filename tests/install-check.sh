#!/usr/bin/env bash
# Integration test for `just install-check` per target (spec remote#host-tools, #acceptance-install-linear), offline:
# the kit's justfile run in a target (`just -f KIT/justfile install-check`, or TARGET as the argument).
#   Linear target (tests/fixtures/install-check/linear), no linear on PATH: exit 1, linear listed missing with the
#     pinned v3.1.0 and the install path (release binary, or npx @schpet/linear-cli);
#   the linear skill's fake linear on PATH (reports the pin): linear ok, exit 0; a linear reporting another
#     release: listed with the wanted v3.1.0, exit 1;
#   GitHub target (no config): linear never checked.
# herdr, pi and gh are stubs (gh signed in), so only the tracker line decides the exit. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "install-check test: $*" >&2; exit 1; }
mkdir -p "$t/bin" "$t/home" "$t/old"
for x in herdr pi gh; do printf '#!/bin/sh\nexit 0\n' >"$t/bin/$x"; done
printf '#!/bin/sh\necho "linear 3.0.0"\n' >"$t/old/linear"; chmod +x "$t/bin/"* "$t/old/linear"
cp "$(command -v just)" "$t/bin/just"   # its own dir goes on the recipe's PATH: the test's, never one holding a linear
# PATH without any linear: every dir holding one is dropped (the recipe adds HOME/.local/bin: HOME is a fresh dir).
clean=""; IFS=: read -ra ds <<<"$PATH"; for d in "${ds[@]}"; do [[ -x "$d/linear" ]] || clean+=":$d"; done
lin_target="$t/linear"; gh_target="$t/github"
git init -q "$lin_target"; git init -q "$gh_target"; mkdir -p "$lin_target/sub"
cp "$kit/tests/fixtures/install-check/linear/.octo-feather.toml" "$lin_target/"
check() { # WANT DIR EXTRA_PATH [TARGET]: run in DIR; output in $out
  local rc=0; out="$(cd "$2" && env HOME="$t/home" PATH="$t/bin${3:+:$3}$clean" \
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
echo "install-check: ok (Linear target: linear missing names v3.1.0 and the install path, exit 1; at the pin ok; another release named; GitHub target never checks linear)"
