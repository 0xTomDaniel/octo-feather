#!/usr/bin/env bash
# Integration test for `just fast`, the kit's fast tier (quality #acceptance-fast-affected), and `just fast-map`,
# the coverage map it selects from. In a throwaway git copy of the kit's tracked files, with one static recipe
# and two test items, each running its own Python script: after a one-script change, just fast runs the static
# check and only the item whose recorded coverage reaches that script, naming each with its reason; a changed
# path on shared-machinery.txt that no coverage reaches runs every item. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
rm "$t"/tests/*.sh
sed -i 's/^export GATE_RECIPES := .*/export GATE_RECIPES := "check-dashes"/' "$t/justfile"
for n in a b; do
  printf '#!/usr/bin/env python3\nprint("%s ran")\n' "$n" > "$t/scripts/fixture-$n"
  printf '#!/usr/bin/env bash\nset -euo pipefail\n"$(dirname "$0")/../scripts/fixture-%s"\n' "$n" > "$t/tests/$n.sh"
  chmod +x "$t/scripts/fixture-$n" "$t/tests/$n.sh"
done
g init -q; g add -A; g commit -qm base
fast() { set +e; out="$(cd "$t" && just fast 2>&1)"; rc=$?; set -e
  [[ "$rc" == 0 ]] || { echo "fast test: just fast exited $rc: $out" >&2; exit 1; }; }
ran() { grep -qF "test_gate.py::$1" <<<"$out"; }
(cd "$t" && just fast-map >/dev/null 2>&1) || { echo "fast test: just fast-map failed" >&2; (cd "$t" && just fast-map) >&2; exit 1; }
# One script changed: the static check, then only the item whose recorded coverage reaches it, each named.
echo '# changed' >> "$t/scripts/fixture-a"
fast
[[ "$out" == *"fast: check-dashes: static check"* && "$out" == *"fast: tests/a.sh: recorded coverage reaches scripts/fixture-a"* ]] \
  || { echo "fast test: the static check and tests/a.sh not named with their reasons: $out" >&2; exit 1; }
ran 'test_recipe[check-dashes]' && ran 'test_script[tests/a.sh]' && ! ran 'test_script[tests/b.sh]' \
  || { echo "fast test: want check-dashes and tests/a.sh run, tests/b.sh not: $out" >&2; exit 1; }
# A listed path no coverage reaches (the list itself): every item.
echo '# changed' >> "$t/shared-machinery.txt"
fast
[[ "$out" == *"fast: all 2 test items: shared-machinery.txt on shared-machinery.txt"* ]] && ran 'test_script[tests/a.sh]' && ran 'test_script[tests/b.sh]' \
  || { echo "fast test: a listed unreached change did not run every item: $out" >&2; exit 1; }
echo "fast: ok (one-script change: static check plus the covering item only, each named; listed unreached change: every item)"
