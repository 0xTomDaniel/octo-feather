#!/usr/bin/env bash
# Integration test for the review of a main merge's resolution (the rule: issue-lifecycle #lanes-one-head), no network:
# a fake `gh` holds PR #7 of o/r. `octo-feather-lane resolution` prints a conflicted merge's remerge diff and its files;
# `verdict --resolution` posts a verdict naming the merge and only those files; merge-ask passes on the earlier review
# verdict with it and refuses without it, naming the merge; a fix commit after the reviewed head needs a full review.
# Run by `just check`.
# criterion: issue-lifecycle#acceptance-review-resolution
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"; G="$kit/scripts/octo-feather-gate"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-review-resolution test: $*" >&2; exit 1; }
export HOME="$t/home" FAKE_GH="$t/gh" XDG_STATE_HOME="$t/xdg" OCTO_FEATHER_QC_DIR="$t/qc"
unset HERDR_SESSION
mkdir -p "$HOME" "$t/bin" "$FAKE_GH"
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
# Fake GitHub for repo o/r, PR #7 in $FAKE_GH/7.json: pr view, and issue comments by POST, edits by PATCH.
import json, os, re, sys
a = sys.argv[1:]; p = os.environ["FAKE_GH"] + "/7.json"
if a[:3] == ["pr", "view", "7"]:
    d = json.load(open(p)); print(json.dumps({k: d[k] for k in a[a.index("--json") + 1].split(",") if k in d})); sys.exit(0)
if a[0] == "api" and "-X" in a:
    m, path = a[a.index("-X") + 1], a[a.index("-X") + 2]; d = json.load(open(p))
    body = json.load(open(a[a.index("--input") + 1]))["body"]
    if m == "POST" and path.endswith("/issues/7/comments"):
        c = {"body": body, "url": f"https://github.com/o/r/pull/7#issuecomment-{1001 + len(d['comments'])}"}; d["comments"].append(c)
    elif m == "PATCH" and (r := re.search(r"/issues/comments/(\d+)$", path)):
        c = next(c for c in d["comments"] if c["url"].endswith("-" + r.group(1))); c["body"] = body
    else: sys.exit(f"fake gh: unexpected {a}")
    json.dump(d, open(p, "w")); print(c["url"]); sys.exit(0)
sys.exit(f"fake gh: unexpected {a}")
EOF
chmod +x "$t/bin/gh"; export PATH="$t/bin:$PATH"
run() { local want="$1"; shift; set +e; out="$("$L" "$@" 2>"$t/err")"; rc=$?; err="$(cat "$t/err")"; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"; }

# The lane: main B; the lane's code J (reviewed, clear) and qc's status commit H. Main then changes the lane's line
# of app.py (a conflict) and notes.txt (no lane file); the lane merges it as M, resolving the conflict by hand; qc
# reruns on M (its status commit H2, the PR head). M's full gate pass is recorded.
R="$t/repo"; mkdir -p "$R/docs/specs"; cd "$R"
git init -q -b main .; git config user.email t@example.com; git config user.name t; git config commit.gpgsign false
status() { printf '{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {"acceptance-a": {"status": "%s", "pr": %s}}}\n' "$1" "$2" > docs/specs/demo.status.json; }
commit() { git add -A; git commit -q -m "$1"; git rev-parse HEAD; }
on() { git checkout -q --detach "$1"; shift; "$@" >/dev/null; git rev-parse HEAD; git checkout -q -f lane; }
status planned null; seq 1 20 > app.py; echo notes > notes.txt
B="$(commit base)"; git update-ref refs/remotes/origin/main "$B"; git checkout -q -b lane
sed -i 1s/.*/one/ app.py; J="$(commit "feat: x")"
status built 7; H="$(commit "qc: built acceptance-a (judged ${J:0:12})")"
MAIN="$(on "$B" sh -c 'sed -i 1s/.*/uno/ app.py; echo main >> notes.txt; git commit -qam "main: two files"')"
git update-ref refs/remotes/origin/main "$MAIN"
resolved_merge() { # merge MAIN, resolving app.py's conflict by keeping the lane's line
  git merge -q --no-edit "$MAIN" 2>/dev/null || true; sed -i '1,/^>>>>>>>/{/^<<<<<<<\|^=======\|^>>>>>>>\|^uno$/d}' app.py
  git commit -qam 'Merge main, conflict resolved'; }
M="$(on "$H" resolved_merge)"
[[ "$(git show "$M:app.py" | head -2)" == $'one\n2' ]] || fail "fixture: the resolution kept $(git show "$M:app.py" | head -2)"
qc() { echo >> docs/specs/demo.status.json; git commit -qam "qc: built acceptance-a (judged ${1:0:12})"; }   # qc's status-only commit
H2="$(on "$M" qc "$M")"
on "$M" "$G" record --reason "lane final head" --seconds 1 >/dev/null
ST=(--status docs/specs/demo.status.json)
check_ok='[{"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"}]'
printf '{"number": 7, "baseRefName": "main", "headRefName": "gh6", "headRefOid": "%s", "body": "", "statusCheckRollup": %s, "comments": []}\n' "$H2" "$check_ok" > "$FAKE_GH/7.json"
printf 'Findings: none blocking.\nChecks: none\nVerdict: clear\n' > "$t/clear"
run 0 verdict 7 "$J" "$t/clear"; url="$out"   # the earlier review, of J

body() { # HEAD JUDGED REVIEWED_LINE
  printf 'Closes #6\n\n## Merge ask\n\nHead: %s\nChecks: check pass\nJudged: %s to %s: qc status commits %s change only docs/specs/demo.status.json\n' "${1:0:12}" "${2:0:12}" "${1:0:12}" "${1:0:12}"
  printf '| criterion | qc verdict | judged | evidence |\n|---|---|---|---|\n| demo#acceptance-a | pass | judged %s | r |\nReview verdict: %s\n%sBuilt: demo#acceptance-a\nFailed: none\n' "${2:0:12}" "$url" "$3"
}
setpr() { # HEAD JUDGED [REVIEWED_LINE]
  python3 - "$FAKE_GH/7.json" "$1" "$(body "$1" "$2" "${3:-}")" <<'EOF'
import json, sys; p, head, body = sys.argv[1:]; d = json.load(open(p)); d.update(headRefOid=head, body=body); json.dump(d, open(p, "w"))
EOF
}

# without a resolution verdict: refused, naming the merge
setpr "$H2" "$M"; run 1 merge-ask 7 "${ST[@]}"
grep -qF "Review verdict: merge ${M:0:12} 'Merge main, conflict resolved' resolved a conflict with origin/main: the review verdict does not carry over without a clear resolution verdict naming it" <<<"$err" \
  || fail "no resolution verdict: not refused naming the merge: $err"

# the lever: the remerge diff and only the files the resolution changed (notes.txt is main's own change)
run 0 resolution "${M:0:12}"
[[ "$(head -2 <<<"$out")" == "Resolution of merge $M 'Merge main, conflict resolved' (git show --remerge-diff; issue-lifecycle #lanes-one-head):"$'\n'"Files: app.py" ]] \
  || fail "resolution header: $out"
grep -qx -- '-uno' <<<"$out" && ! grep -q notes.txt <<<"$out" || fail "resolution printed more or less than the remerge diff: $out"
run 1 resolution "${J:0:12}"; grep -qF "commit ${J:0:12} is not a merge" <<<"$err" || fail "resolution of a non-merge: $err"

# the resolution verdict names the merge and only its files; merge-ask then asks for the Reviewed proof, then passes
run 0 verdict 7 "${M:0:12}" "$t/clear" --resolution; rurl="$out"
python3 - "$FAKE_GH/7.json" "$M" "$rurl" <<'EOF' || fail "resolution verdict body"
import json, sys; c = next(c for c in json.load(open(sys.argv[1]))["comments"] if c["url"] == sys.argv[3])
assert f"\nMerge: {sys.argv[2]}\nFiles: app.py\n" in c["body"] and "\nVerdict: clear\n" in c["body"], c["body"]
EOF
run 1 merge-ask 7 "${ST[@]}"
want="Reviewed: ${J:0:12} to ${M:0:12}: qc status commits ${H:0:12} change only docs/specs/demo.status.json; resolution of merge ${M:0:12} (app.py) reviewed clear: $rurl"
grep -qF "Reviewed: missing; add the check's proof line \`$want\`" <<<"$err" || fail "no Reviewed line: $err"
setpr "$H2" "$M" "$want"$'\n'; run 0 merge-ask 7 "${ST[@]}"
grep -qxF "$want" <<<"$out" || fail "pass did not print the Reviewed proof: $out"

# a blocking resolution verdict keeps nothing
printf 'Findings: the resolution drops main.\nChecks: none\nVerdict: blocking\n' > "$t/blocking"
run 0 verdict 7 "${M:0:12}" "$t/blocking" --resolution
run 1 merge-ask 7 "${ST[@]}"; grep -qF "Review verdict: merge ${M:0:12} 'Merge main, conflict resolved' resolved a conflict" <<<"$err" || fail "blocking resolution verdict kept the review: $err"
run 0 verdict 7 "${M:0:12}" "$t/clear" --resolution

# a fix commit after the reviewed head still needs a full fresh review, the resolution verdict aside
F="$(on "$H2" sh -c 'echo fix >> app.py; git commit -qam "fix: after merge"')"
F2="$(on "$F" qc "$F")"
on "$F" "$G" record --reason "lane final head" --seconds 1 >/dev/null
setpr "$F2" "$F" "$want"$'\n'; run 1 merge-ask 7 "${ST[@]}"
grep -qF "Review verdict: commit ${F:0:12} 'fix: after merge' after the reviewed head ${J:0:12} changes app.py" <<<"$err" || fail "fix commit after the reviewed head: $err"

# --resolution on a merge with nothing beyond git's automatic merge is refused: there is no resolution to review
C="$(on "$B" sh -c 'echo c > c.txt; git add c.txt; git commit -qm "main: c"')"; git update-ref refs/remotes/origin/main "$C"
CM="$(on "$H" git merge -q --no-edit "$C")"; setpr "$CM" "$J"
run 1 verdict 7 "${CM:0:12}" "$t/clear" --resolution; grep -qF "merge ${CM:0:12} changes nothing beyond git's automatic merge" <<<"$err" || fail "clean merge resolution: $err"
# a lane that builds no criterion: its review verdict on N, then a resolved merge NM, the PR head: the same rule
N="$(on "$B" sh -c 'sed -i 1s/.*/one/ app.py; git commit -qam "fix: a rule"')"; git update-ref refs/remotes/origin/main "$MAIN"
NM="$(on "$N" resolved_merge)"; [[ "$(git show "$NM:app.py" | head -2)" == $'one\n2' ]] || fail "fixture: NM's resolution"
on "$NM" "$G" record --reason "lane final head" --seconds 1 >/dev/null
nask() { python3 - "$FAKE_GH/7.json" "$NM" "$(printf 'Closes #6\n\n## Merge ask\n\nHead: %s\nChecks: check pass\nReview verdict: %s\n%sBuilt: none\nFailed: none\n' "${NM:0:12}" "$url" "$1")" <<'PY'
import json, sys; p, head, body = sys.argv[1:]; d = json.load(open(p)); d.update(headRefOid=head, body=body); json.dump(d, open(p, "w"))
PY
}
nask ""; run 0 verdict 7 "$N" "$t/clear"
run 1 merge-ask 7; grep -qF "Judged: merge ${NM:0:12} 'Merge main, conflict resolved' resolved a conflict" <<<"$err" || fail "no-criterion lane without a resolution verdict: $err"
run 0 verdict 7 "${NM:0:12}" "$t/clear" --resolution; nurl="$out"
nwant="Reviewed: ${N:0:12} to ${NM:0:12}: no qc status commit; resolution of merge ${NM:0:12} (app.py) reviewed clear: $nurl"
run 1 merge-ask 7; grep -qF "Reviewed: missing; add the check's proof line \`$nwant\`" <<<"$err" || fail "no-criterion lane, no Reviewed line: $err"
nask "$nwant"$'\n'; run 0 merge-ask 7; grep -qxF "$nwant" <<<"$out" || fail "no-criterion lane with its resolution verdict: $out"
echo "lane-review-resolution: ok (remerge diff and files printed; resolution verdict names the merge and its files; merge-ask refuses without it or with a blocking one naming the merge, passes with it and the Reviewed proof; a fix commit after the reviewed head needs a full review; a clean merge has no resolution; a no-criterion lane alike)"
