#!/usr/bin/env bash
# gate: e2e
# End-to-end test of `just fast-map` (quality #acceptance-fast-affected) over a gate item that runs its script in
# the qc sandbox (real srt and namespaces: e2e, quality #test-kinds), through the commands only: the mapping run
# maps it, and `just fast-list` selects it for a change to that script alone and not for a change to another
# item's script. A throwaway git copy of the kit's tracked files without its tests (as tests/fast.sh) holding two
# test items: a.sh runs scripts/fixture-a inside `scripts/octo-feather-qc-sandbox` (by hand, its judged worktree a
# clean repo of its own), b.sh runs scripts/fixture-b directly. Integration of the rest of just fast: tests/fast.sh.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
[[ "$(uname -s)" != Darwin ]] || { echo "fast-map-sandbox: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 77; }
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | grep -zvxE 'tests/[^/]*\.sh|tests/gate/test_cpu\.py|tests/gate/kit/(.*/)?test_[^/]*\.py' \
  | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
for n in a b; do printf '#!/usr/bin/env python3\nprint("%s ran")\n' "$n" > "$t/scripts/fixture-$n"; done
printf '#!/usr/bin/env bash\nset -euo pipefail\nk="$(cd "$(dirname "$0")/.." && pwd -P)"\nw="$(mktemp -d)"; trap '"'"'rm -rf "$w"'"'"' EXIT\ncd "$w"; git init -q; git -c user.name=t -c user.email=t@t commit -q --allow-empty -m s\n"$k/scripts/octo-feather-qc-sandbox" -- "$k/scripts/fixture-a"\n' > "$t/tests/a.sh"
printf '#!/usr/bin/env bash\nset -euo pipefail\n"$(dirname "$0")/../scripts/fixture-b"\n' > "$t/tests/b.sh"
chmod +x "$t"/scripts/fixture-? "$t"/tests/?.sh
g init -q; g add -A; g commit -qm base
set +e; map="$(cd "$t" && just fast-map -k "not test_recipe" 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 && "$map" == *"fast-map: 2 test items mapped at"* && "$map" != *"did not pass"* ]] \
  || { echo "fast-map-sandbox: want the mapping run green with both items mapped (exit $rc): $map" >&2; exit 1; }
# list WANT NOT: just fast-list names WANT selected by its recorded coverage and selects 1 of the 2 test items.
list() { local out; out="$(cd "$t" && just --set GATE_RECIPES check-dashes fast-list 2>&1)"
  [[ "$out" == *"$1"* && "$out" == *"fast: selected 2 of 3 gate items (1 static, 1 of 2 test items)"* ]] \
    || { echo "fast-map-sandbox: want '$1' and 1 of 2 test items selected: $out" >&2; exit 1; }; }
echo '# changed' >> "$t/scripts/fixture-a"
list "fast: tests/a.sh: recorded coverage reaches scripts/fixture-a"
(cd "$t" && git checkout -q scripts/fixture-a); echo '# changed' >> "$t/scripts/fixture-b"
list "fast: tests/b.sh: recorded coverage reaches scripts/fixture-b"
echo "fast-map-sandbox: ok (an item running its script in the qc sandbox mapped; a change to that script selects it alone, a change to another item's script does not)"
