#!/usr/bin/env bash
# Integration test for the check-scripts gate (#121 D1 D2): python scripts byte-compile, other
# scripts go to shellcheck (bash -n without it); a script is python when its shebang runs python. In a throwaway copy
# of the kit's tracked files, each planted script makes `just check-scripts` fail or pass. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
(cd "$t" && just check-scripts >/dev/null 2>&1) || { echo "check-scripts test: clean copy is not green" >&2; (cd "$t" && just check-scripts) >&2; exit 1; }
# run SHEBANG BODY: an executable scripts/x.planted with that shebang and body, then `just check-scripts`; sets rc, out.
run() {
  printf '%s\n%s\n' "$1" "$2" > "$t/scripts/x.planted"; chmod +x "$t/scripts/x.planted"
  set +e; out="$(cd "$t" && just check-scripts 2>&1)"; rc=$?; set -e
  rm -f "$t/scripts/x.planted"
}
# expect SHEBANG BODY: just check-scripts fails naming the script.
expect() {
  run "$@"
  [[ "$rc" != 0 ]] || { echo "check-scripts test: '$1' with '$2' passed just check-scripts" >&2; exit 1; }
  grep -qF 'scripts/x.planted' <<<"$out" || { echo "check-scripts test: '$1' with '$2' not named in the output" >&2; echo "$out" >&2; exit 1; }
}
# allow SHEBANG BODY: just check-scripts passes.
allow() {
  run "$@"
  [[ "$rc" == 0 ]] || { echo "check-scripts test: '$1' with '$2' failed just check-scripts" >&2; echo "$out" >&2; exit 1; }
}
py='#!/usr/bin/env python3'
uv='#!/usr/bin/env -S uv run --script'
# D1: parses, but byte-compile refuses (outside a function or loop).
expect "$py" 'return 1'
expect "$py" 'break'
expect "$py" 'continue'
expect "$py" 'yield 1'
expect "$py" 'nonlocal x'
# D2: what the shebang runs decides: valid python that is not shell passes, invalid python fails.
body='print("ok")'
for sb in "$uv" '#!/usr/bin/env -S uv run --quiet --script' '#!/usr/bin/python3' '#!/usr/bin/env -S python3 -u' '#!/usr/bin/env python3.12'; do
  allow "$sb" "$body"
  expect "$sb" 'return 1'
done
# A shell script stays shell though its shebang path names python.
allow '#!/opt/python3/bin/bash' 'if [ -n "${1:-}" ]; then echo "$1"; fi'
expect '#!/opt/python3/bin/bash' 'if then fi'
allow '#!/usr/bin/env bash' 'echo ok'
expect '#!/usr/bin/env bash' 'if then fi'
echo "check-scripts: ok (python byte-compiles by what the shebang runs; shell scripts stay shell)"
