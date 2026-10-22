#!/usr/bin/env bash
# Integration test for scripts/octo-feather-integrate: clean merge and
# cherry-pick, conflict, red gate, lane match, in a throwaway repo. Run by `just check`.
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
g worktree add -q -b w7 ../w7; (cd ../w7 && mkdir -p docs/specs && echo s > docs/specs/a.spec.html && g add docs/specs/a.spec.html && g commit -qm spec)
run 0 7 w7                                                 # a spec alone stays tracked and integrates
echo "integrate: ok (merge, cherry-pick, conflict, red gate, missing lane, lane match gh<N> or <prefix>/gh<N>, review state and factory recipes refused, spec kept)"
