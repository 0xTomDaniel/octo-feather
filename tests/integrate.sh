#!/usr/bin/env bash
# Integration test for scripts/octo-feather-integrate: clean merge and
# cherry-pick, conflict, red gate, lane match, in a throwaway repo. Run by `just check`.
# criterion: issue-lifecycle#acceptance-pilot-full
# criterion: issue-lifecycle#acceptance-integrate-fast
# criterion: issue-lifecycle#acceptance-integrate-checkpoint
# criterion: issue-lifecycle#acceptance-brownfield-full
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
cd "$t" && g init -q repo && cd repo
printf 'check:\n    test ! -e red\n' > justfile; echo a > f; g add -A; g commit -qm base
g worktree add -q -b gh7 ../lane
g worktree add -q -b gh7-x ../gh7x   # worker branch beside lane gh7: not a lane
g worktree add -q -b gh70 ../gh70   # lane gh70: not lane gh7
g worktree add -q -b w1 ../w1; (cd ../w1 && echo b > b && g add b && g commit -qm w1)
g worktree add -q -b w2 ../w2; (cd ../w2 && echo c > c && g add c && g commit -qm w2)
c2="$(git -C ../w2 rev-parse HEAD)"
I="$kit/scripts/octo-feather-integrate"
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
run() { local want="$1"; shift; set +e; out="$("$I" "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "integrate test: '$*' want exit $want, got $rc: $out" >&2; exit 1; }; }
run 0 7 w1 "$c2"                                           # merge a branch, cherry-pick a commit
[[ -e ../lane/b && -e ../lane/c ]] || { echo "integrate test: lane missing worker files" >&2; exit 1; }
head="$(git -C ../lane rev-parse HEAD)"
(cd ../w1 && echo x > f && g commit -qam w1f); g worktree add -q -b w3 ../w3; (cd ../w3 && echo y > f && g commit -qam w3f)
run 0 7 w1
before="$(git -C ../lane rev-parse HEAD)"
run 1 7 w3                                                 # conflict on f
[[ "$(git -C ../lane rev-parse HEAD)" == "$before" ]] || { echo "integrate test: conflict did not restore the head" >&2; exit 1; }
[[ "$(git -C ../lane status --porcelain)" == "" ]] || { echo "integrate test: lane left dirty after conflict" >&2; exit 1; }
g worktree add -q -b w4 ../w4; (cd ../w4 && echo r > red && g add red && g commit -qm red)
before="$(git -C ../lane rev-parse HEAD)"
run 2 7 w4                                                 # red gate rolls back
[[ "$(git -C ../lane rev-parse HEAD)" == "$before" && "$before" != "$head" ]] || { echo "integrate test: red gate did not roll back" >&2; exit 1; }
run 66 8 w1                                                # no lane for gh8
[[ "$(git -C ../gh70 rev-parse HEAD)" == "$(git -C ../gh7x rev-parse HEAD)" ]] || { echo "integrate test: gh70 touched as lane gh7" >&2; exit 1; }
g worktree remove ../lane; g worktree remove ../gh7x
run 66 7 w1                                                # gh70 alone is not lane gh7
g worktree add -q -b gh7-demo ../suf
run 66 7 w1                                                # gh7-demo alone is not lane gh7
g worktree remove ../suf; g worktree add -q -b octo-feather/gh7 ../pre main
run 0 7 w1                                                 # namespaced lane octo-feather/gh7 integrates
[[ "$out" == *"branch=octo-feather/gh7 "* && -e ../pre/b ]] || { echo "integrate test: prefixed lane not integrated: $out" >&2; exit 1; }
# Hand-in hygiene (pilot 1, 2026-10-20): review state and factory recipes never land on the lane.
"$kit/scripts/octo-feather-exclude" . >/dev/null
mkdir -p docs/specs/a.spec.html.review/versions; echo v > docs/specs/a.spec.html.review/versions/1.html
[[ -z "$(git status --porcelain)" ]] || { echo "integrate test: excluded review state shows in git status" >&2; exit 1; }
g worktree add -q -b w5 ../w5; (cd ../w5 && mkdir -p docs/specs/a.spec.html.review/versions && echo v > docs/specs/a.spec.html.review/versions/1.html \
  && echo s > docs/specs/a.spec.html && g add docs/specs/a.spec.html && g add -f docs/specs/a.spec.html.review && g commit -qm review-state)
before="$(git -C ../pre rev-parse HEAD)"
run 3 7 w5; [[ "$out" == *"review state"* && "$(git -C ../pre rev-parse HEAD)" == "$before" ]] || { echo "integrate test: tracked review state not refused: $out" >&2; exit 1; }
g worktree add -q -b w6 ../w6; (cd ../w6 && printf '\nintegrate issue +refs:\n    octo-feather-integrate {{issue}} {{refs}}\n' >> justfile && g commit -qam recipes)
run 3 7 w6; [[ "$out" == *"factory recipes"* && "$(git -C ../pre rev-parse HEAD)" == "$before" ]] || { echo "integrate test: factory recipe not refused: $out" >&2; exit 1; }
# #121 D12: a quiet recipe, a defaulted parameter, an import, an unreadable justfile.
adds() { g worktree add -q -b "$1" "../$1"; (cd "../$1" && eval "$2" && g add -A && g commit -qm "$1")
  run 3 7 "$1"; [[ "$out" == *"factory recipes to the justfile ($3)"* && "$(git -C ../pre rev-parse HEAD)" == "$before" ]] \
    || { echo "integrate test: $1 adding $3 not refused: $out" >&2; exit 1; }; }
adds w8 "printf '\n@qc:\n    true\n' >> justfile" qc
adds w9 "printf '\nqc status=\"x\":\n    true\n' >> justfile" qc
adds w10 "printf 'integrate N:\n    true\n' > ci.just; printf \"\nimport 'ci.just'\n\" >> justfile" integrate
g worktree add -q -b w11 ../w11; (cd ../w11 && printf '\nfoo:\n\ttrue\n  x\n' >> justfile && g commit -qam broken)
run 3 7 w11; [[ "$out" == *"justfile does not parse"* && "$(git -C ../pre rev-parse HEAD)" == "$before" ]] || { echo "integrate test: unreadable justfile not refused: $out" >&2; exit 1; }
# #121 D13: a lane qc recipe's parameters edited.
(cd ../pre && printf '\nqc STATUS:\n    true\n' >> justfile && g commit -qam lane-qc)
g worktree add -q -b w12 ../w12 octo-feather/gh7; (cd ../w12 && sed -i 's/^qc STATUS:/qc STATUS PR:/' justfile && g commit -qam qc-params)
run 0 7 w12; grep -q '^qc STATUS PR:' ../pre/justfile || { echo "integrate test: qc parameter edit not integrated: $out" >&2; exit 1; }
# PR #140 review finding 3 (owner: docs/adr/0017): an alias-only hand-in.
g worktree add -q -b w13 ../w13 octo-feather/gh7; (cd ../w13 && printf '\nalias integrate := check\n' >> justfile && g commit -qam alias)
run 0 7 w13; grep -qx 'alias integrate := check' ../pre/justfile || { echo "integrate test: alias-only hand-in not integrated: $out" >&2; exit 1; }
before="$(git -C ../pre rev-parse HEAD)"
g worktree add -q -b w7 ../w7; (cd ../w7 && mkdir -p docs/specs && echo s > docs/specs/a.spec.html && g add docs/specs/a.spec.html && g commit -qm spec)
run 0 7 w7                                                 # a spec alone stays tracked and integrates
run 64 ENG-7 w1; [[ "$out" == *"not a GitHub issue number"* ]] || { echo "integrate test: ENG-7 in a GitHub target: $out" >&2; exit 1; }
# Linear target (roles spec #lane-key): ENG-123 lands on the worktree on branch eng-123, never eng-1230
# or eng-123-x; an unknown tracker is refused before any worktree is touched.
cd "$t" && g init -q lin && cd lin
printf 'check:\n    true\n' > justfile; echo 'tracker = "linear"' > .octo-feather.toml; echo a > f; g add -A; g commit -qm base
g worktree add -q -b eng-1230 ../l1230; g worktree add -q -b eng-123-x ../l123x
g worktree add -q -b lw ../lw; (cd ../lw && echo l > l && g add l && g commit -qm lw)
run 66 ENG-123 lw                                          # eng-1230 and eng-123-x are not lane eng-123
g worktree add -q -b eng-123 ../l123
run 0 ENG-123 lw
[[ "$out" == *"branch=eng-123 "* && -e ../l123/l && ! -e ../l1230/l && ! -e ../l123x/l ]] || { echo "integrate test: Linear lane eng-123 not integrated: $out" >&2; exit 1; }
run 64 12 lw; [[ "$out" == *"not a Linear issue key"* ]] || { echo "integrate test: 12 in a Linear target: $out" >&2; exit 1; }
echo 'tracker = "jira"' > .octo-feather.toml; g commit -qam jira; head="$(git -C ../l123 rev-parse HEAD)"
run 64 ENG-123 lw; [[ "$out" == *"unknown tracker 'jira'"* && "$(git -C ../l123 rev-parse HEAD)" == "$head" ]] || { echo "integrate test: jira target: $out" >&2; exit 1; }
# Gate tiers (issue-lifecycle #lanes-checkpoints): a repo with a fast recipe and a shared-machinery list.
# The full gate reds on machinery/b, the fast tier never reds.
cd "$t" && g init -q tiers && cd tiers
printf 'check:\n    @echo gate=full\n    test ! -e machinery/b\nfast:\n    @echo gate=fast\n' > justfile
printf '# listed\nmachinery\n' > shared-machinery.txt; mkdir machinery; echo a > machinery/a; echo a > f; g add -A; g commit -qm base
g worktree add -q -b gh9 ../t9
work() { g worktree add -q -b "$1" "../$1" gh9; (cd "../$1" && eval "$2" && g add -A && g commit -qm "$1"); }
passed() { (cd ../t9 && "$kit/scripts/octo-feather-gate" passed); }
# issue-lifecycle#acceptance-pilot-full: the lane's first integration runs the full gate and records the pass.
work t1 'echo 1 > one'; run 0 9 t1
[[ "$out" == *gate=full* && "$out" != *gate=fast* && "$out" == *"tier: full (pilot"* ]] || { echo "integrate test: pilot did not run the full gate: $out" >&2; exit 1; }
h1="$(git -C ../t9 rev-parse HEAD)"
rec="$(passed)" && [[ "$rec" == *"\"head\": \"$h1\""* && "$rec" == *'"clean": true'* ]] || { echo "integrate test: pilot pass not recorded for $h1: $rec" >&2; exit 1; }
# issue-lifecycle#acceptance-integrate-fast: past it, a branch touching no listed path runs only the fast tier.
work t2 'echo 2 > two'; run 0 9 t2
[[ "$out" == *gate=fast* && "$out" != *gate=full* && "$out" == *provisional* ]] || { echo "integrate test: unlisted change not fast and provisional: $out" >&2; exit 1; }
! passed >/dev/null 2>&1 || { echo "integrate test: a fast-only head has a full pass recorded" >&2; exit 1; }
# Two full passes on heads whose gate configuration did not change (justfile only: no Justfile, .justfile or
# lock files) record one configuration identity.
config() { (cd ../t9 && "$kit/scripts/octo-feather-gate" passed "$1") | python3 -c 'import json, sys; print(json.load(sys.stdin)["gate_config"])'; }
work t4 'echo 4 > four'; run 0 9 --full t4
[[ "$(config "$h1")" == "$(config HEAD)" && -n "$(config HEAD)" ]] || { echo "integrate test: unchanged configuration, two identities: $(config "$h1") $(config HEAD)" >&2; exit 1; }
# issue-lifecycle#acceptance-integrate-checkpoint: renaming a listed file runs the full gate; red rolls back, naming it.
work t3 'g mv machinery/a machinery/b'; before="$(git -C ../t9 rev-parse HEAD)"; run 2 9 t3
[[ "$out" == *gate=full* && "$out" == *"machinery/a"* && "$out" == *"machinery/b"* && "$(git -C ../t9 rev-parse HEAD)" == "$before" ]] \
  || { echo "integrate test: listed rename not full and rolled back: $out" >&2; exit 1; }
# issue-lifecycle#acceptance-brownfield-full: a repo the kit did not create, only its own `just check` (no fast recipe):
# every integration, past the pilot too, runs that gate in full and records the pass; the repo gains no recipe.
cd "$t" && g init -q brown && cd brown
printf 'check:\n    @echo own-gate\n' > justfile; echo a > f; g add -A; g commit -qm base
recipes="$(just --summary)"; g worktree add -q -b gh11 ../b11
for n in 1 2 3; do
  g worktree add -q -b "b$n" ../"b$n" gh11; (cd ../"b$n" && echo "$n" > "n$n" && g add -A && g commit -qm "b$n")
  run 0 11 "b$n"
  [[ "$out" == *"tier: full ("*"no fast recipe in this repo: its one gate is the full tier"* && "$out" == *own-gate* && "$out" == *"tier=full"* && "$out" != *provisional* ]] \
    || { echo "integrate test: brownfield integration $n did not run its own gate in full: $out" >&2; exit 1; }
  (cd ../b11 && "$kit/scripts/octo-feather-gate" passed >/dev/null) || { echo "integrate test: brownfield pass $n not recorded" >&2; exit 1; }
  [[ "$(cd ../b11 && just --summary)" == "$recipes" ]] || { echo "integrate test: brownfield repo gained a recipe: $(cd ../b11 && just --summary)" >&2; exit 1; }
done
echo "integrate: ok (merge, cherry-pick, conflict, red gate, missing lane, lane match gh<N> or <prefix>/gh<N>, review state and factory recipes refused (as just reads them: @qc, defaulted parameter, import; unreadable justfile), an alias-only hand-in integrates, a lane qc recipe's parameters edited, spec kept; Linear ENG-123 on eng-123 only, unknown tracker refused; tiers: pilot full and recorded, unlisted fast and provisional, one configuration identity on unchanged configuration, listed rename full and red; brownfield: only its own check, full and recorded at every integration, no recipe added)"
