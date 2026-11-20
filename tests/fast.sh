#!/usr/bin/env bash
# Integration test for `just fast` (quality #acceptance-fast-affected; what the fast tier runs: quality #recipe-fast)
# and `just fast-map`, the coverage map it selects from, and `just fast-list`, its dry run, through the commands
# only. A throwaway git copy of the kit's tracked files without its tests (tests/*.sh and its pytest kit tests),
# holding nine test items: a.sh and b.sh each run their own Python script, c.sh (`# gate: e2e`) runs a's, d.sh
# runs a bash script coverage cannot see, e.sh runs b's and fails while the file $FAST_RAN.fail exists (the mapping
# run), box.sh runs its own Python script inside the qc sandbox (scripts/octo-feather-qc-sandbox, by hand; on macOS,
# which has no qc sandbox, directly); and tests/fixtures/fast/test_f.py as a pytest kit test file, each of its three functions its own gate item. The static checks are cut
# to one with just's own command-line override (`just --set GATE_RECIPES check-dashes`); the map is built from
# the test items (`just fast-map -k "not test_recipe"`). Each item appends its name to FAST_RAN, the record of what ran.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; export FAST_RAN="$t.ran"; trap 'rm -rf "$t" "$FAST_RAN" "$FAST_RAN.fail"' EXIT
(cd "$kit" && git ls-files -z | grep -zvxE 'tests/[^/]*\.sh|tests/gate/test_cpu\.py|tests/gate/kit/(.*/)?test_[^/]*\.py' \
  | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
# Its scratch repo's git identity, for every command that commits (a recorded full pass is a git note), whatever the
# box has: a runner may have none (GitHub Actions).
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
for n in a b g; do
  printf '#!/usr/bin/env python3\nprint("%s ran")\n' "$n" > "$t/scripts/fixture-$n"
  printf '#!/usr/bin/env bash\nset -euo pipefail\necho %s >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-%s"\n' "$n" "$n" > "$t/tests/$n.sh"
done
printf '#!/usr/bin/env bash\n# gate: e2e\nset -euo pipefail\necho c >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-a"\n' > "$t/tests/c.sh"
printf '#!/usr/bin/env bash\necho d ran\n' > "$t/scripts/fixture-d"
printf '#!/usr/bin/env bash\nset -euo pipefail\necho d >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-d"\n' > "$t/tests/d.sh"
printf '#!/usr/bin/env bash\nset -euo pipefail\necho e >> "$FAST_RAN"\n"$(dirname "$0")/../scripts/fixture-b"\n[[ ! -e "$FAST_RAN.fail" ]]\n' > "$t/tests/e.sh"
printf '#!/usr/bin/env python3\nprint("s ran")\n' > "$t/scripts/fixture-s"
# box.sh's judged worktree a clean repo of its own: the sandbox refuses a dirty one, and the copy is changed below.
printf '#!/usr/bin/env bash\nset -euo pipefail\necho box >> "$FAST_RAN"\nk="$(cd "$(dirname "$0")/.." && pwd -P)"\n[[ "$(uname -s)" != Darwin ]] || exec "$k/scripts/fixture-s"\nw="$(mktemp -d)"; trap '"'"'rm -rf "$w"'"'"' EXIT; cd "$w"; git init -q; git commit -q --allow-empty -m s\n"$k/scripts/octo-feather-qc-sandbox" -- "$k/scripts/fixture-s"\n' > "$t/tests/box.sh"
rm "$t/tests/g.sh"; cp "$kit/tests/fixtures/fast/test_f.py" "$t/tests/gate/kit/"   # fixture-g: test_two's alone
chmod +x "$t"/scripts/fixture-? "$t"/tests/?.sh "$t/tests/box.sh"
g init -q; g add -A; g commit -qm base
# fast WANT: just fast, green, ran exactly the static check plus the items WANT (sorted, space-separated).
fast() { : > "$FAST_RAN"; set +e; out="$(cd "$t" && PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }--color=no" just --set GATE_RECIPES check-dashes fast 2>&1)"; rc=$?; set -e
  [[ "$rc" == 0 ]] || { echo "fast test: just fast exited $rc: $out" >&2; exit 1; }
  local got n; got="$(sort "$FAST_RAN" | paste -sd' ' -)"; n=$(( $(wc -w <<<"$1") + 1 ))
  [[ "$got" == "$1" && "$out" == *"=== $n passed in "* ]] || { echo "fast test: want the static check and items '$1', ran '$got': $out" >&2; exit 1; }; }
# The mapping run with e.sh failing: red, yet the map is written from the items that passed, e.sh left out.
touch "$FAST_RAN.fail"; set +e; map="$(cd "$t" && just fast-map -k "not test_recipe" 2>&1)"; rc=$?; set -e; rm "$FAST_RAN.fail"
[[ "$rc" != 0 && "$map" == *"fast-map: 6 test items mapped at"* && "$map" == *"fast-map: tests/e.sh did not pass: left out of the map"* ]] \
  || { echo "fast test: a mapping run with tests/e.sh failing: want it red, 6 items mapped (a, b, box, c, test_one, test_two) and e.sh named left out (exit $rc): $map" >&2; exit 1; }
# Nothing changed: only the items with no recorded coverage, the unmapped one and the one that did not pass.
fast 'd e'
[[ "$out" == *"fast: tests/e.sh: did not pass the mapping run at"* ]] || { echo "fast test: e.sh not named as not passed: $out" >&2; exit 1; }
# One script changed: the static check, the items whose recorded coverage reaches it (a.sh, and test_one alone of
# its file's functions), and the unmapped items, each named; the e2e items named skipped. The dry run names the
# same and runs nothing.
echo '# changed' >> "$t/scripts/fixture-a"
: > "$FAST_RAN"; list="$(cd "$t" && just --set GATE_RECIPES check-dashes fast-list 2>&1)"
[[ ! -s "$FAST_RAN" && "$list" == *"fast: selected 5 of 10 gate items (1 static, 4 of 9 test items)"* ]] \
  || { echo "fast test: just fast-list ran an item or did not count 5 of 10 selected: $list" >&2; exit 1; }
fast 'a d e one'
for want in "fast: check-dashes: static check" "fast: tests/a.sh: recorded coverage reaches scripts/fixture-a" \
  "fast: tests/gate/kit/test_f.py::test_one: recorded coverage reaches scripts/fixture-a" \
  "fast: tests/d.sh: no recorded coverage in the map at" "fast: tests/c.sh: e2e" "fast: tests/gate/kit/test_f.py::test_e2e: e2e" \
  "fast: tests/e.sh: did not pass the mapping run at" "fast: selected 5 of 10 gate items"; do
  [[ "$out" == *"$want"* && "$list" == *"$want"* ]] || { echo "fast test: '$want' not in the just fast and just fast-list output: $out --- $list" >&2; exit 1; }
done
# The script the sandboxed item runs inside the qc sandbox changed: that item is selected by its recorded coverage.
(cd "$t" && git checkout -q scripts/fixture-a); echo '# changed' >> "$t/scripts/fixture-s"
fast 'box d e'
[[ "$out" == *"fast: tests/box.sh: recorded coverage reaches scripts/fixture-s"* ]] \
  || { echo "fast test: the sandboxed item not selected by its recorded coverage: $out" >&2; exit 1; }
# A listed path no coverage reaches (the list itself): every non-e2e item.
(cd "$t" && git checkout -q scripts/fixture-s); echo '# changed' >> "$t/shared-machinery.txt"
fast 'a b box d e one two'
[[ "$out" == *"fast: all 7 non-e2e test items: shared-machinery.txt on shared-machinery.txt"* ]] \
  || { echo "fast test: a listed unreached change not named as running every non-e2e item: $out" >&2; exit 1; }
(cd "$t" && git checkout -q shared-machinery.txt)
# A file the map cannot know (absent at the map head, not on the list): every non-e2e item, the file named.
printf '#!/usr/bin/env python3\nprint("new")\n' > "$t/scripts/fixture-new"
fast 'a b box d e one two'
[[ "$out" == *"fast: all 7 non-e2e test items: scripts/fixture-new absent at the map head "*", outside the coverage map's reach"* ]] \
  || { echo "fast test: a file absent at the map head not named as running every non-e2e item: $out" >&2; exit 1; }
rm "$t/scripts/fixture-new"
# A full pass recorded after the map: files changed up to it are gated, so only changes past it feed coverage
# selection; a test item changed since the map head stays selected (the map does not know its coverage).
echo '# gated' >> "$t/scripts/fixture-a"; echo '# changed test' >> "$t/tests/b.sh"; g commit -qam 'past the map'
P="$(g rev-parse HEAD)"
# No git identity (no env, no repo, global or system config): the record fails naming it and how to set it, and
# records nothing; the gate never makes one up.
mkdir "$t.noid"; set +e
out="$(cd "$t" && env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u GIT_COMMITTER_NAME -u GIT_COMMITTER_EMAIL HOME="$t.noid" \
  XDG_CONFIG_HOME="$t.noid" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null EMAIL= scripts/octo-feather-gate record --reason "full pass" --seconds 1 2>&1)"; rc=$?; set -e
rm -rf "$t.noid"
[[ "$rc" != 0 && "$out" == *"not recorded: no git identity"*"git config user.name 'NAME' and git config user.email 'EMAIL'"* ]] \
  || { echo "fast test: a record with no git identity: want a refusal naming it, got $rc: $out" >&2; exit 1; }
! (cd "$t" && scripts/octo-feather-gate passed >/dev/null 2>&1) || { echo "fast test: a refused record left a full pass" >&2; exit 1; }
(cd "$t" && scripts/octo-feather-gate record --reason "full pass" --seconds 1 >/dev/null)
fast 'b d e'
for want in "fast: diff base: ${P:0:12}, the latest recorded full pass" "fast: tests/b.sh: changed since the map at"; do
  [[ "$out" == *"$want"* ]] || { echo "fast test: '$want' not in the output past a full pass: $out" >&2; exit 1; }
done
echo "fast: ok (a mapping run with one failing item writes the map without it, selected on every diff; one-script change: static check, the covering items (a pytest function alone of its file) and the unmapped items, each named, e2e named skipped, the dry run the same and running nothing; an item running its script in the qc sandbox mapped and selected by that script; listed unreached change and a file absent at the map head: every non-e2e item; past a recorded full pass, only later changes select, a test changed since the map stays selected)"
