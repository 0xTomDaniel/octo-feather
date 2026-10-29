#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane post-merge, the director's post-merge routine (owner ruling
# 2026-10-29 on issue 206; steps 1-2, issue 396), offline: a fake gh on PATH holds PR #7 and the push runs of
# its merge commit, and logs every call. Step 1 stops, exit 1, on a PR not merged and on one merged at another
# head; step 2 stops on a red run naming its URL, on no run within the --wait bound, and on a watch that fails
# with its run unfinished; all runs concluded success passes. Every run ends with a one-line summary of each
# step's outcome, and only gh reads run (rerun safe). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-post-merge test: $*" >&2; exit 1; }
export HOME="$t/home" GH_LOG="$t/gh.log" GH_STORE="$t/gh.json" GH_LISTS="$t/lists"
unset GH_REPO GH_TOKEN
mkdir -p "$HOME" "$t/bin"
# Fake gh: pr view from .pr; run list (only --commit <full merge sha> --event push) answers its Nth call with
# .lists[N] (the last one repeated); run watch exits .watch[id] (default 0); anything else is refused.
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]; open(os.environ["GH_LOG"], "a").write(" ".join(a) + "\n")
db = json.load(open(os.environ["GH_STORE"]))
def opt(f): return a[a.index(f) + 1] if f in a else None
if a[:3] == ["pr", "view", "7"]:
    print(json.dumps({k: db["pr"][k] for k in opt("--json").split(",")})); sys.exit(0)
if a[:2] == ["run", "list"]:
    n = len(open(os.environ["GH_LISTS"]).read()) if os.path.exists(os.environ["GH_LISTS"]) else 0
    open(os.environ["GH_LISTS"], "a").write("x")
    ok = opt("--commit") == db["pr"]["mergeCommit"]["oid"] and opt("--event") == "push"
    runs = db["lists"][min(n, len(db["lists"]) - 1)] if ok else []
    print(json.dumps([{k: r[k] for k in opt("--json").split(",")} for r in runs])); sys.exit(0)
if a[:2] == ["run", "watch"] and "--exit-status" in a:
    rc = db.get("watch", {}).get(a[2], 0)
    print(f"Run {a[2]} watched", file=sys.stderr if rc else sys.stdout); sys.exit(rc)
print(f"fake gh: refused {' '.join(a)}", file=sys.stderr); sys.exit(1)
EOF
chmod +x "$t/bin/gh"
H=1234567890abcdef1234567890abcdef12345678 M=feedfacecafebeef00112233445566778899aabb
store() { # STATE HEAD LISTS-JSON [WATCH-JSON]
  jq -n --arg s "$1" --arg h "$2" --arg m "$M" --argjson l "$3" --argjson w "${4:-{\}}" \
    '{pr: {state: $s, headRefOid: $h, mergeCommit: (if $s == "MERGED" then {oid: $m} else null end),
           baseRefName: "main", headRefName: "gh7"}, lists: $l, watch: $w}' > "$GH_STORE"
  rm -f "$GH_LISTS"; : > "$GH_LOG"
}
run1() { # name status conclusion id
  jq -nc --arg n "$1" --arg s "$2" --arg c "$3" --argjson i "$4" \
    '{databaseId: $i, status: $s, conclusion: $c, workflowName: $n, url: "https://github.com/o/r/actions/runs/\($i)"}'
}
run() { # WANT ARGS...: octo-feather-lane with the fake gh first on PATH
  local want="$1" rc; shift
  set +e; out="$(PATH="$t/bin:$PATH" "$L" "$@" 2>"$t/err")"; rc=$?; set -e; err="$(cat "$t/err")"
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"
  ! grep -q Traceback <<<"$err" || fail "'$*' printed a traceback: $err"
  last="$(tail -n1 <<<"$out")"
  ! grep -qv '^\(pr view\|run list\|run watch\) ' "$GH_LOG" || fail "'$*' ran a gh write: $(cat "$GH_LOG")"
}
green="$(run1 check completed success 11)" lint="$(run1 lint completed success 12)"
red="$(run1 check completed failure 13)" busy="$(run1 check in_progress '' 11)"

# Step 1: not merged, merged at another head, gh failing: stop at step 1, step 2 not run, no run list.
store OPEN "$H" "[[$green]]"
run 1 post-merge 7 "${H:0:7}" --lane gh7
[[ "$out" == *"step 1 merged: stopped: PR #7 is OPEN, not merged"* ]] || fail "not merged: $out"
[[ "$last" == "post-merge gh7 PR #7: step 1 merged stopped; step 2 main CI not run" ]] || fail "not merged summary: $last"
! grep -q '^run ' "$GH_LOG" || fail "not merged still listed runs: $(cat "$GH_LOG")"
store MERGED "abcdef0$H" "[[$green]]"
run 1 post-merge 7 "${H:0:12}" --lane gh7
[[ "$out" == *"step 1 merged: stopped: PR #7 merged at head abcdef012345, not at the pinned head ${H:0:12}"* ]] || fail "other head: $out"
[[ "$last" == "post-merge gh7 PR #7: step 1 merged stopped; step 2 main CI not run" ]] || fail "other head summary: $last"
run 1 post-merge 8 "$H" --lane gh7
[[ "$out" == *"step 1 merged: stopped: gh pr view 8 failed"* && "$last" == *"step 1 merged stopped"* ]] || fail "gh failing: $out"

# Step 2 green: a run in progress is watched to its end, a second workflow joins; every run success: exit 0.
store MERGED "$H" "[[$busy], [$green, $lint]]"
run 0 post-merge 7 "$H" --lane gh7 --repo o/r
[[ "$(head -n1 <<<"$out")" == "step 1 merged: ok: PR #7 (gh7) merged into main at head ${H:0:12}, merge commit ${M:0:12}" ]] || fail "step 1 line: $out"
[[ "$out" == *"step 2 main CI: ok: 2 push runs on ${M:0:12} concluded success: check https://github.com/o/r/actions/runs/11, lint https://github.com/o/r/actions/runs/12"* ]] || fail "green line: $out"
[[ "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI ok" ]] || fail "green summary: $last"
grep -qx "run watch 11 --exit-status -R o/r" "$GH_LOG" || fail "running run not watched with --exit-status in o/r: $(cat "$GH_LOG")"
grep -qx "pr view 7 --json state,headRefOid,mergeCommit,baseRefName,headRefName -R o/r" "$GH_LOG" || fail "pr view: $(cat "$GH_LOG")"
[[ "$(wc -l <<<"$out")" == 3 ]] || fail "green prints one line per step and the summary: $out"
run 0 post-merge 7 "$H" --lane gh7 --repo o/r   # rerun: same result, still reads only
[[ "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI ok" ]] || fail "rerun: $out"

# A run that appears within the bound is waited for.
store MERGED "$H" "[[], [$green]]"
run 0 post-merge 7 "$H" --lane gh7 --wait 1
[[ "$out" == *"step 2 main CI: ok: 1 push run on ${M:0:12} concluded success"* ]] || fail "late run: $out"

# Step 2 red: one run failed: stop naming its URL, never healthy.
store MERGED "$H" "[[$red, $lint]]" '{"13": 1}'
run 1 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 2 main CI: stopped: main CI red on ${M:0:12}: check failure https://github.com/o/r/actions/runs/13"* ]] || fail "red: $out"
[[ "$out" != *"concluded success"* && "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI stopped" ]] || fail "red summary: $out"
# A watch that fails while its run reads unfinished: stop naming it, never healthy.
store MERGED "$H" "[[$busy]]" '{"11": 1}'
run 1 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 2 main CI: stopped: gh run watch 11 failed"*"https://github.com/o/r/actions/runs/11"* ]] || fail "watch failed: $out"
# No run within the bound: stop naming it.
store MERGED "$H" "[[]]"
run 1 post-merge 7 "$H" --lane gh7 --wait 0
[[ "$out" == *"step 2 main CI: stopped: no push run on merge commit ${M:0:12} within 0s"* ]] || fail "no run: $out"
[[ "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI stopped" ]] || fail "no run summary: $last"

# Usage: missing --lane, a HEAD that is no sha.
run 1 post-merge 7 "$H"; [[ "$err" == *"usage: octo-feather-lane post-merge PR HEAD --lane NAME"* ]] || fail "usage: $err"
run 1 post-merge 7 nothex --lane gh7; [[ "$err" == *"HEAD must be"* ]] || fail "bad head: $err"
echo "lane-post-merge: ok (step 1 stops on not merged, other head, gh failure; step 2 watches to the end, green passes," \
  "red names the run URL, failed watch and no run in bound stop; summary last; reads only)"
