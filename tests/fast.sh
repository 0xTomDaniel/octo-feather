#!/usr/bin/env bash
# Integration test for `just fast`, the kit's fast tier (quality #acceptance-fast-affected), and `just fast-map`,
# the coverage map it selects from. In a throwaway git copy of the kit's tracked files, with one static recipe
# and four test items: a.sh and b.sh each run their own Python script, c.sh is declared e2e (`# gate: e2e`) and
# runs a's script, d.sh runs a bash script coverage cannot see. After a one-script change, just fast runs the
# static check and only the item whose recorded coverage reaches that script, naming each with its reason, and
# names c.sh e2e-skipped; d.sh runs only when a path its text names changed; a changed path on
# shared-machinery.txt that no coverage reaches runs every non-e2e item. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
rm "$t"/tests/*.sh
sed -i 's/^export GATE_RECIPES := .*/export GATE_RECIPES := "check-dashes"/' "$t/justfile"
for n in a b; do
  printf '#!/usr/bin/env python3\nprint("%s ran")\n' "$n" > "$t/scripts/fixture-$n"
  printf '#!/usr/bin/env bash\nset -euo pipefail\necho %s >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-%s"\n' "$n" "$n" > "$t/tests/$n.sh"
  chmod +x "$t/scripts/fixture-$n" "$t/tests/$n.sh"
done
printf '#!/usr/bin/env bash\n# gate: e2e\nset -euo pipefail\necho c >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-a"\n' > "$t/tests/c.sh"
printf '#!/usr/bin/env bash\necho d ran\n' > "$t/scripts/fixture-d"
printf '#!/usr/bin/env bash\nset -euo pipefail\necho d >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-d"\n' > "$t/tests/d.sh"
chmod +x "$t/tests/c.sh" "$t/scripts/fixture-d" "$t/tests/d.sh"
g init -q; g add -A; g commit -qm base
# Each fixture item appends its name to FAST_RAN (outside the copy), the record of what ran.
export FAST_RAN="$t.ran"; trap 'rm -rf "$t" "$FAST_RAN"' EXIT
# fast WANT: just fast, green, ran exactly the static check plus the items WANT (sorted, space-separated).
fast() { : > "$FAST_RAN"; set +e; out="$(cd "$t" && just fast 2>&1)"; rc=$?; set -e
  [[ "$rc" == 0 ]] || { echo "fast test: just fast exited $rc: $out" >&2; exit 1; }
  local got n; got="$(sort "$FAST_RAN" | paste -sd' ' -)"; n=$(( $(wc -w <<<"$1") + 1 ))
  [[ "$got" == "$1" && "$out" == *"=== $n passed in "* ]] || { echo "fast test: want the static check and items '$1', ran '$got': $out" >&2; exit 1; }; }
(cd "$t" && just fast-map >/dev/null 2>&1) || { echo "fast test: just fast-map failed" >&2; (cd "$t" && just fast-map) >&2; exit 1; }
# One script changed: the static check, then only the item whose recorded coverage reaches it, each named.
echo '# changed' >> "$t/scripts/fixture-a"
fast a
[[ "$out" == *"fast: check-dashes: static check"* && "$out" == *"fast: tests/a.sh: recorded coverage reaches scripts/fixture-a"* ]] \
  || { echo "fast test: the static check and tests/a.sh not named with their reasons: $out" >&2; exit 1; }
[[ "$out" == *"fast: tests/c.sh: e2e"* ]] || { echo "fast test: e2e tests/c.sh not named skipped: $out" >&2; exit 1; }
# An unmapped item runs when a path its own text names changed.
(cd "$t" && git checkout -q scripts/fixture-a); echo '# changed' >> "$t/scripts/fixture-d"
fast d
[[ "$out" == *"fast: tests/d.sh: no recorded coverage; it names scripts/fixture-d"* ]] || { echo "fast test: unmapped tests/d.sh not named with its path: $out" >&2; exit 1; }
# A listed path no coverage reaches (the list itself): every item.
echo '# changed' >> "$t/shared-machinery.txt"
fast 'a b d'
[[ "$out" == *"fast: all 3 non-e2e test items: shared-machinery.txt on shared-machinery.txt"* ]] \
  || { echo "fast test: a listed unreached change not named as running every non-e2e item: $out" >&2; exit 1; }
echo "fast: ok (one-script change: static check plus the covering item only, each named, e2e named skipped; unmapped item on a path it names; listed unreached change: every non-e2e item)"
