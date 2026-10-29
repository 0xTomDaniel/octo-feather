#!/usr/bin/env bash
# Integration test for the check-scripts gate (rules: #121 D1 D2). In a throwaway copy of the kit's
# tracked files, each planted script makes `just check-scripts` fail or pass. Run by `just check`.
# Cases that reach the whole shellcheck pass share runs (#207): the scripts that must pass are planted together in
# one run, which also proves the clean copy green. Each script that must fail runs alone: the bash -n fallback stops
# at the first bad file.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
git -C "$t" init -q
git -C "$t" add -A
planted=()
# plant FILE SHEBANG BODY: an executable FILE (under the copy) with that shebang and body, removed by the next run.
plant() { printf '%s\n%s\n' "$2" "$3" > "$t/$1"; chmod +x "$t/$1"; planted+=("$1"); }
# run: `just check-scripts` over the planted scripts; sets rc, out; removes them.
run() {
  git -C "$t" add -A
  set +e; out="$(cd "$t" && just check-scripts 2>&1)"; rc=$?; set -e
  for f in "${planted[@]}"; do rm -f "${t:?}/$f"; done; planted=()
}
# expect SHEBANG BODY [FILE]: alone, FILE (default scripts/x.planted) makes just check-scripts fail naming it.
expect() {
  local f="${3:-scripts/x.planted}"
  plant "$f" "$1" "$2"; run
  [[ "$rc" != 0 ]] || { echo "check-scripts test: $f '$1' with '$2' passed just check-scripts" >&2; exit 1; }
  grep -qF "$f" <<<"$out" || { echo "check-scripts test: $f '$1' with '$2' not named in the output" >&2; echo "$out" >&2; exit 1; }
}
# allow SHEBANG BODY: plants a script that must pass, checked by the next allowed run.
n=0; allow() { n=$((n + 1)); plant "scripts/x$n.planted" "$1" "$2"; }
# allowed: just check-scripts passes with every script allow planted (and the kit's own).
allowed() {
  local what; what="$(for f in "${planted[@]}"; do head -n 2 "$t/$f" | paste -sd ' ' -; done)"; run
  [[ "$rc" == 0 ]] || { echo "check-scripts test: one of these failed just check-scripts:" >&2; echo "$what" >&2; echo "$out" >&2; exit 1; }
}
py='#!/usr/bin/env python3'
uv='#!/usr/bin/env -S uv run --script'
# D1: parses, but byte-compile refuses (outside a function or loop).
expect "$py" 'return 1'
expect "$py" 'break'
expect "$py" 'continue'
expect "$py" 'yield 1'
expect "$py" 'nonlocal x'
# D2: shebangs that run python: valid python that is not shell, then invalid python.
body='print("ok")'
pys=("$uv" '#!/usr/bin/env -S uv run --quiet --script' '#!/usr/bin/python3' '#!/usr/bin/env -S python3 -u' '#!/usr/bin/env python3.12')
for sb in "${pys[@]}"; do expect "$sb" 'return 1'; done
for sb in "${pys[@]}"; do allow "$sb" "$body"; done
# A shell script stays shell though its shebang path names python.
allow '#!/opt/python3/bin/bash' 'if [ -n "${1:-}" ]; then echo "$1"; fi'
allow '#!/usr/bin/env bash' 'echo ok'
allowed
# Bad shell fails wherever check-scripts looks: scripts/, the herdr-comms assets, tests/.
expect '#!/opt/python3/bin/bash' 'if then fi'
expect '#!/usr/bin/env bash' 'if then fi'
expect '#!/usr/bin/env bash' 'if then fi' .agents/skills/herdr-comms/assets/x.planted
expect '#!/usr/bin/env bash' 'if then fi' tests/x.planted
echo "check-scripts: ok (#121 D1 D2 cases)"
