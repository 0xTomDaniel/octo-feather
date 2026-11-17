#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane done, the supervisor's lane close (spec issue-lifecycle
# #gates-pr-line, #acceptance-merge-linear, #acceptance-merge-approved-head, #acceptance-no-github-issue),
# offline: a Linear target's close, against the testkit's Linear stand-in (tests/gate/kit/testkit/linear.py replaying
# tests/fixtures/linear-lane-done/*/tape.json) with a recording gh first on PATH, moves the parent and every ticket
# to done through the tracker skill's
# issue-done, leaves a Canceled ticket Canceled, and runs no gh at all (no GitHub issue filed or closed); a
# GitHub target's close, against a recording gh holding issues in a JSON store, closes every sub-issue and
# then the parent through issue-done, and files nothing. A ticket the tracker cannot move fails naming it,
# after the others were tried. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"; LI="$kit/tests/gate/kit/testkit/linear"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-done test: $*" >&2; exit 1; }
export HOME="$t/home" GH_LOG="$t/gh.log" GH_STORE="$t/gh.json" FAKE_LINEAR="$t/fl"
unset GH_REPO GH_TOKEN
mkdir -p "$HOME" "$t/bin" "$t/fl" "$t/fl2"
cp "$kit/tests/fixtures/linear-lane-done/close/tape.json" "$t/fl/"; cp "$kit/tests/fixtures/linear-lane-done/no-done-state/tape.json" "$t/fl2/"
# Recording gh: logs every call; answers issue view and issue close from $GH_STORE, refuses anything else.
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]; open(os.environ["GH_LOG"], "a").write(" ".join(a) + "\n")
p = os.environ["GH_STORE"]; db = json.load(open(p)) if os.path.exists(p) else {}
if a[:2] == ["issue", "view"] and a[2] in db:
    i = db[a[2]]; kids = [{"number": int(k)} for k, x in db.items() if x.get("parent") == a[2]]
    print(json.dumps({"number": int(a[2]), "title": "t", "body": "b", "state": i["state"], "url": "u",
                      "parent": {"number": int(i["parent"])} if i.get("parent") else None,
                      "subIssues": {"nodes": kids, "totalCount": len(kids)}, "blockedBy": {"nodes": [], "totalCount": 0}}))
    sys.exit(0)
if a[:2] == ["issue", "close"] and a[2] in db:
    db[a[2]]["state"] = "CLOSED"; json.dump(db, open(p, "w")); print(f"Closed issue o/r#{a[2]}"); sys.exit(0)
print(f"recording gh: refused {' '.join(a)}", file=sys.stderr); sys.exit(1)
EOF
chmod +x "$t/bin/gh"
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
run() { # WANT DIR ARGS...: octo-feather-lane in DIR, the Linear stand-in and recording gh first on PATH
  local want="$1" dir="$2" rc; shift 2
  set +e; out="$(cd "$dir" && PATH="$t/bin:$LI:$PATH" "$L" "$@" 2>"$t/err")"; rc=$?; set -e; err="$(cat "$t/err")"
  [[ "$rc" == "$want" ]] || fail "'$*' in $dir want exit $want, got $rc: $out $err"
  ! grep -q Traceback <<<"$err" || fail "'$*' printed a traceback: $err"
}
moved() { jq -r 'select(.[0][:2] == ["issue", "update"]) | "\(.[0][2]) \(.[0][4])"' "$FAKE_LINEAR/log"; }   # each move the stand-in logged: KEY STATE

# Linear target: ENG-123 with tickets ENG-124 (Todo), ENG-125 (Canceled), ENG-126 (Done); ENG-200 is another lane's.
g init -q "$t/lin"; echo 'tracker = "linear"' > "$t/lin/.octo-feather.toml"
: > "$GH_LOG"
run 0 "$t/lin" "done" eng-123
[[ "$out" == $'ENG-124: done\nENG-125: done\nENG-126: done\nENG-123: done\nENG-123: parent and 3 tickets done' ]] || fail "linear done output: $out"
[[ "$(moved)" == $'ENG-124 completed\nENG-123 completed' ]] || fail "want ENG-124 then ENG-123 moved to Done, canceled ENG-125 and done ENG-126 left: $(moved)"
! grep -q ENG-200 "$FAKE_LINEAR/log" || fail "another lane's ENG-200 touched: $(grep ENG-200 "$FAKE_LINEAR/log")"
[[ ! -s "$GH_LOG" ]] || fail "a Linear lane's close ran gh (no GitHub issue may be filed or closed): $(cat "$GH_LOG")"
run 0 "$t/lin" "done" ENG-123   # a rerun leaves done tickets as they are
[[ "$(moved)" == $'ENG-124 completed\nENG-123 completed' ]] || fail "rerun moved again: $(moved)"
run 1 "$t/lin" "done" ENG-999; [[ "$err" == *"tracker script linear/issue-view ENG-999 failed"* ]] || fail "unknown parent: $err"
# A team with no completed state: every move fails, each named, the parent tried last.
FAKE_LINEAR="$t/fl2"
run 1 "$t/lin" "done" ENG-123
[[ "$out" == "ENG-125: done" && "$err" == *"ENG-123: 3 of 4 not done"* && "$err" == *"  - ENG-124: "*"Workflow state not found"* \
   && "$err" == *"  - ENG-123: "* && "$err" == *"rerun \`octo-feather-lane done ENG-123\`"* ]] || fail "failed moves: $out $err"
[[ "$(moved)" == $'ENG-124 completed\nENG-126 completed\nENG-123 completed' ]] || fail "moves tried: want both tickets, then the parent: $(moved)"
run 1 "$t/lin" "done"; [[ "$err" == *"usage: octo-feather-lane done PARENT"* ]] || fail "usage: $err"

# GitHub target (no .octo-feather.toml): parent 6 with sub-issues 7 and 8 (8 already closed); 9 is another lane's.
g init -q "$t/gh"
echo '{"6": {"state": "OPEN"}, "7": {"state": "OPEN", "parent": "6"}, "8": {"state": "CLOSED", "parent": "6"}, "9": {"state": "OPEN"}}' > "$GH_STORE"
: > "$GH_LOG"
run 0 "$t/gh" "done" 6
[[ "$out" == $'7: done\n8: done\n6: done\n6: parent and 2 tickets done' ]] || fail "github done output: $out"
[[ "$(jq -c '[.["6"].state, .["7"].state, .["8"].state, .["9"].state]' "$GH_STORE")" == '["CLOSED","CLOSED","CLOSED","OPEN"]' ]] \
  || fail "github states: $(cat "$GH_STORE")"
[[ "$(grep '^issue close' "$GH_LOG")" == $'issue close 7\nissue close 8\nissue close 6' ]] || fail "github closes: $(cat "$GH_LOG")"
! grep -qv '^issue \(view\|close\) ' "$GH_LOG" || fail "github close ran another gh command: $(cat "$GH_LOG")"
echo "lane-done: ok (Linear: parent and every ticket done through issue-done, Canceled left, other lanes untouched, no gh run; rerun idempotent;" \
  "unknown parent and failed moves named, parent tried last; GitHub: sub-issues then parent closed through issue-done, nothing filed)"
