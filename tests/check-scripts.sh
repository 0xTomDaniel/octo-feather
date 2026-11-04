#!/usr/bin/env bash
# Integration test for the check-scripts gate (rules: #121 D1, #361). In a throwaway git repo holding what the recipe
# runs on (the justfile and its guard, the tool pins, the lint config and lister, .gitattributes, this test as its one
# shell file; #507: the kit's own files are the recipe's gate item, not this test's), each planted file makes
# `just check-scripts` fail naming it, or pass. ShellCheck runs over the `shell`
# attribute's files (.gitattributes); Python byte-compiles over ruff's list. Which files belong to which language is
# check-languages' rule (tests/languages.sh). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t" "$t.venv"' EXIT
(cd "$kit" && tar -cf - justfile .gitattributes pyproject.toml uv.lock .python-version mise.toml mise.lock mise-version \
  scripts/check-gate-free scripts/octo-feather-lint tests/check-scripts.sh) | tar -xf - -C "$t"
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
# Bad shell fails wherever the attribute names it, all in one `just check-scripts` run: a *.sh file, an extensionless
# script, a skill asset.
bad=(tests/x-planted.sh scripts/x-planted .agents/skills/herdr-comms/assets/x-planted)
for f in "${bad[@]}"; do plant "$f" $'#!/usr/bin/env bash\nif then fi'; done
shell scripts/x-planted; shell .agents/skills/herdr-comms/assets/x-planted
expect "${bad[0]}"; for f in "${bad[@]:1}"; do grep -qF "$f" <<<"$out" || { echo "check-scripts test: $f not named" >&2; echo "$out" >&2; exit 1; }; done
# ShellCheck's batches run at once (#507): a file and the file it sources, by directive or literal path, share one
# run, so ShellCheck reads what the sourced file sets (no SC2154) and still checks it as an input.
lib=$'# shellcheck shell=bash\n# shellcheck disable=SC2034\nx_planted=1'
for i in 1 2 3 4 5 6 7 8; do plant "tests/lib/x-planted-lib$i.sh" "$lib" 644; done
plant tests/x-planted-a.sh $'#!/usr/bin/env bash\n# shellcheck source=tests/lib/x-planted-lib3.sh\nsource "$(dirname "$0")/lib/x-planted-lib3.sh"\necho "$x_planted"'
plant tests/x-planted-b.sh $'#!/usr/bin/env bash\nsource tests/lib/x-planted-lib6.sh\necho "$x_planted"'
run; [[ "$rc" == 0 ]] || { echo "check-scripts test: a sourced file's variable not seen across ShellCheck's batches" >&2; echo "$out" >&2; exit 1; }
plant tests/lib/x-planted-lib5.sh $'# shellcheck shell=bash\nif then fi' 644
plant tests/x-planted-c.sh $'#!/usr/bin/env bash\n# shellcheck source=tests/lib/x-planted-lib5.sh\nsource "$(dirname "$0")/lib/x-planted-lib5.sh"'
expect tests/lib/x-planted-lib5.sh
# Fails closed (#507): ruff's file list crashing (an environment without the lister's tomlkit, as an unsynced kit
# venv) fails the recipe naming the fix, never python: ok (0 files compile).
uv venv --offline --quiet "$t.venv"
set +e; out="$(cd "$t" && UV_PROJECT_ENVIRONMENT="$t.venv" just check-scripts 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] && grep -qF 'check-scripts: the Python file list (octo-feather-lint files) failed' <<<"$out" && grep -qF 'uv sync --locked' <<<"$out" \
  && ! grep -qF 'python: ok' <<<"$out" || { echo "check-scripts test: a crashing Python file list did not fail the recipe naming the fix" >&2; echo "$out" >&2; exit 1; }
# A script in scripts/ that is not executable.
plant scripts/x-planted.sh $'#!/usr/bin/env bash\necho ok' 644; expect scripts/x-planted.sh
echo "check-scripts: ok (#121 D1 compile cases; shellcheck over the shell attribute; executables)"
