#!/usr/bin/env bash
# Integration test for the check-scripts gate (rules: #121 D1, #361). In a throwaway git copy of the kit's tracked
# files, each planted file makes `just check-scripts` fail naming it, or pass. ShellCheck runs over the `shell`
# attribute's files (.gitattributes); Python byte-compiles over ruff's list. Which files belong to which language is
# check-languages' rule (tests/languages.sh). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
# The copy shares the kit's pyproject.toml and uv.lock, so the kit's uv environment serves it (offline).
export UV_PROJECT_ENVIRONMENT="$kit/.venv"
# plant FILE BODY [MODE]: FILE (under the copy) with BODY, executable unless MODE is 644, tracked.
plant() { mkdir -p "$(dirname "$t/$1")"; printf '%s\n' "$2" >"$t/$1"; chmod "${3:-755}" "$t/$1"; g add -A; }
# shell FILE: give FILE the `shell` attribute.
shell() { printf '%s shell\n' "$1" >>"$t/.gitattributes"; g add -A; }
# run: just check-scripts into rc and out, then back to the base commit.
run() { set +e; out="$(cd "$t" && just check-scripts 2>&1)"; rc=$?; set -e; g reset -q --hard; g clean -qfd; }
# expect FILE: the last plant fails just check-scripts naming FILE.
expect() {
  run
  [[ "$rc" != 0 ]] || { echo "check-scripts test: $1 passed just check-scripts" >&2; exit 1; }
  grep -qF "$1" <<<"$out" || { echo "check-scripts test: $1 not named in the output" >&2; echo "$out" >&2; exit 1; }
}
run; [[ "$rc" == 0 ]] || { echo "check-scripts test: the clean copy is not green" >&2; echo "$out" >&2; exit 1; }
grep -qF "scripts: shellcheck ok" <<<"$out" || { echo "check-scripts test: no shellcheck ok line" >&2; echo "$out" >&2; exit 1; }
# D1: parses, but byte-compile refuses (outside a function or loop), in ruff's list: one run, each named.
n=0; for body in 'return 1' 'break' 'continue' 'yield 1' 'nonlocal x'; do n=$((n + 1)); plant "scripts/x_planted$n.py" "$body" 644; done
expect scripts/x_planted1.py; for i in 2 3 4 5; do grep -qF "scripts/x_planted$i.py" <<<"$out" || { echo "check-scripts test: scripts/x_planted$i.py not named" >&2; echo "$out" >&2; exit 1; }; done
# Bad shell fails wherever the attribute names it, all in one ShellCheck run: a *.sh file, an extensionless
# script, a skill asset.
bad=(tests/x-planted.sh scripts/x-planted .agents/skills/herdr-comms/assets/x-planted)
for f in "${bad[@]}"; do plant "$f" $'#!/usr/bin/env bash\nif then fi'; done
shell scripts/x-planted; shell .agents/skills/herdr-comms/assets/x-planted
expect "${bad[0]}"; for f in "${bad[@]:1}"; do grep -qF "$f" <<<"$out" || { echo "check-scripts test: $f not named" >&2; echo "$out" >&2; exit 1; }; done
# A script in scripts/ that is not executable.
plant scripts/x-planted.sh $'#!/usr/bin/env bash\necho ok' 644; expect scripts/x-planted.sh
echo "check-scripts: ok (#121 D1 compile cases; shellcheck over the shell attribute; executables)"
