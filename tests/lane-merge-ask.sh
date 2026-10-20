#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane verdict and merge-ask (spec issue-lifecycle
# #acceptance-merge-ask-evidence, issue #48), no network: a fake `gh` holds PR #7 of o/r and logs
# every call. `verdict` creates the one marker comment, updates it in place on rerun, and refuses a
# wrong head, a report with no verdict and a failed write, leaving no comment behind. `merge-ask`
# passes a complete section and prints it (also through the qc judge's offline gh, scripts/qc-bin/gh),
# fails PR #16's real body (fixture) naming each missing item, and fails each single gap: stale head,
# failing or pending check, missing row, Built unequal to the status file or to the qc commits,
# verdict link to another head or a blocking verdict, untriaged failed criterion. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-merge-ask test: $*" >&2; exit 1; }
export HOME="$t/home" FAKE_GH="$t/gh" FAKE_GH_LOG="$t/gh.log"
mkdir -p "$HOME" "$t/bin" "$FAKE_GH/pr"
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
# Fake GitHub for repo o/r: PRs in $FAKE_GH/pr/N.json; issue comments by POST, edits by PATCH.
# FAKE_GH_FAIL=write fails every api write (HTTP 502), =read fails pr view (network).
import json, os, re, sys
a = sys.argv[1:]; D = os.environ["FAKE_GH"]
open(os.environ["FAKE_GH_LOG"], "a").write(" ".join(a) + "\n")
def die(m, rc=1): print(m, file=sys.stderr); sys.exit(rc)
def path(n): return f"{D}/pr/{n}.json"
if a[:2] == ["pr", "view"]:
    if os.environ.get("FAKE_GH_FAIL") == "read": die("error connecting to api.github.com")
    if not os.path.exists(path(a[2])): die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
    d = json.load(open(path(a[2]))); f = a[a.index("--json") + 1].split(",")
    print(json.dumps({k: d[k] for k in f if k in d})); sys.exit(0)
if a[0] == "api":
    m, p = a[a.index("-X") + 1], a[a.index("-X") + 2].replace("{owner}/{repo}", "o/r")
    if os.environ.get("FAKE_GH_FAIL") == "write": die("gh: Server Error (HTTP 502)")
    body = json.load(open(a[a.index("--input") + 1]))["body"]
    if m == "POST" and (r := re.fullmatch(r"repos/o/r/issues/(\d+)/comments", p)):
        n = r.group(1); d = json.load(open(path(n)))
        cid = 1000 + sum(len(json.load(open(f"{D}/pr/{x}"))["comments"]) for x in os.listdir(f"{D}/pr")) + 1
        c = {"author": {"login": "sup"}, "body": body, "url": f"https://github.com/o/r/pull/{n}#issuecomment-{cid}"}
    elif m == "PATCH" and (r := re.fullmatch(r"repos/o/r/issues/comments/(\d+)", p)):
        for x in os.listdir(f"{D}/pr"):
            d = json.load(open(f"{D}/pr/{x}")); n = x[:-5]
            c = next((c for c in d["comments"] if c["url"].endswith(f"-{r.group(1)}")), None)
            if c: break
        else: die("gh: Not Found (HTTP 404)")
        c["body"] = body
    else: die(f"fake gh: unexpected {a}", 2)
    if m == "POST": d["comments"].append(c)
    json.dump(d, open(path(n), "w")); print(c["url"]); sys.exit(0)
die(f"fake gh: unexpected {a}", 2)
EOF
chmod +x "$t/bin/gh"; export PATH="$t/bin:$PATH"

H="$(printf 'a1b2c3d4%.0s' 1 2 3 4 5)"   # 40 hex
OTHER="$(printf 'ffee%.0s' 1 2 3 4 5 6 7 8 9 10)"
cat > "$t/demo.status.json" <<'EOF'
{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {
  "acceptance-a": {"status": "built", "pr": 7}, "acceptance-b": {"status": "built", "pr": 7},
  "acceptance-c": {"status": "planned", "pr": null}, "acceptance-d": {"status": "built", "pr": 3}}}
EOF
cat > "$t/other.status.json" <<'EOF'
{"spec": "other.spec.html", "accepted_commit": "0123abc", "criteria": {"acceptance-x": {"status": "built", "pr": 7}}}
EOF
ST=(--status "$t/demo.status.json")
check_ok='[{"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"}, {"__typename": "StatusContext", "context": "ci/x", "state": "SUCCESS"}]'
commits='[{"oid": "1", "messageHeadline": "feat: x", "messageBody": ""},
  {"oid": "2", "messageHeadline": "qc: built acceptance-a acceptance-b (judged 0123456789ab)", "messageBody": ""}]'
printf '{"number": 7, "headRefOid": "%s", "body": "", "statusCheckRollup": %s, "comments": [], "commits": %s}\n' "$H" "$check_ok" "$commits" > "$FAKE_GH/pr/7.json"

run() { local want="$1"; shift; set +e; out="$("$L" "$@" 2>"$t/err")"; rc=$?; err="$(cat "$t/err")"; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"
  grep -q Traceback <<<"$err" && fail "'$*' printed a traceback: $err"; return 0; }
comments() { python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["comments"]))' "$FAKE_GH/pr/7.json"; }
writes() { grep -c '^api' "$FAKE_GH_LOG" || true; }

# --- verdict: create once, update in place, refusals write nothing ---
printf 'Findings: none blocking.\nVerdict: clear\n' > "$t/report"
: > "$FAKE_GH_LOG"
run 0 verdict 7 "${H:0:7}" "$t/report"
url="$out"; [[ "$url" == "https://github.com/o/r/pull/7#issuecomment-1001" ]] || fail "verdict printed $url"
grep -q '^api -X POST repos/{owner}/{repo}/issues/7/comments ' "$FAKE_GH_LOG" || fail "no POST: $(cat "$FAKE_GH_LOG")"
[[ "$(comments)" == 1 ]] || fail "create made $(comments) comments"
printf 'Note: a nit.\n**Verdict:** blocking\n' > "$t/report2"
run 0 verdict 7 "$H" "$t/report2"
[[ "$out" == "$url" && "$(comments)" == 1 ]] || fail "rerun did not update in place: $out, $(comments) comments"
grep -q '^api -X PATCH repos/{owner}/{repo}/issues/comments/1001 ' "$FAKE_GH_LOG" || fail "no PATCH of 1001: $(cat "$FAKE_GH_LOG")"
python3 - "$FAKE_GH/pr/7.json" "$H" <<'EOF' || fail "comment body after update"
import json, sys; b = json.load(open(sys.argv[1]))["comments"][0]["body"]
assert b.startswith("<!-- octo-feather-review-verdict -->") and f"Head: {sys.argv[2]}\n" in b and "Verdict: blocking\n" in b and "a nit" in b, b
EOF
run 0 verdict 7 "$H" - < "$t/report"   # stdin, back to clear
[[ "$(writes)" == 3 && "$(comments)" == 1 ]] || fail "third run: $(writes) writes, $(comments) comments"
run 0 verdict 7 "$H" "$t/report"; [[ "$(writes)" == 3 ]] || fail "unchanged rerun wrote"
grep -q unchanged <<<"$err" || fail "unchanged rerun not said: $err"
# refusals: each non-zero, fix named, no write
n="$(writes)"
run 1 verdict 7 "$OTHER" "$t/report"; grep -q "is not PR #7's head.*push the reviewed head" <<<"$err" || fail "wrong head: $err"
printf 'looks fine\n' > "$t/nov"; run 1 verdict 7 "$H" "$t/nov"; grep -q 'add a line `Verdict: clear`' <<<"$err" || fail "no verdict: $err"
run 1 verdict 7 "$H" "$t/missing"; grep -q "cannot read report" <<<"$err" || fail "missing report: $err"
: > "$t/empty"; run 1 verdict 7 "$H" "$t/empty"; grep -q "is empty" <<<"$err" || fail "empty report: $err"
run 1 verdict 7 xyz "$t/report"; grep -q "commit sha" <<<"$err" || fail "bad head: $err"
run 1 verdict 7 "$H"; grep -q usage <<<"$err" || fail "usage: $err"
run 1 verdict 9 "$H" "$t/report"; grep -q "check PR #9 exists" <<<"$err" || fail "unknown PR: $err"
[[ "$(writes)" == "$n" ]] || fail "a refusal wrote"
# execution failures: a failed create leaves no comment; a failed read names the fix
cp "$FAKE_GH/pr/7.json" "$t/pr7.keep"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); d["comments"]=[]; json.dump(d,open(sys.argv[1],"w"))' "$FAKE_GH/pr/7.json"
FAKE_GH_FAIL="write" run 1 verdict 7 "$H" "$t/report"
grep -q "was not created; fix the cause.*then rerun" <<<"$err" || fail "failed write: $err"
[[ "$(comments)" == 0 ]] || fail "failed create left a comment"
cp "$t/pr7.keep" "$FAKE_GH/pr/7.json"
FAKE_GH_FAIL="write" run 1 verdict 7 "$H" "$t/report2"; grep -q "was not updated" <<<"$err" || fail "failed update: $err"
grep -qF "Verdict: clear" <<<"$(cat "$FAKE_GH/pr/7.json")" || fail "failed update changed the comment"
FAKE_GH_FAIL="read" run 1 verdict 7 "$H" "$t/report"; grep -q "error connecting.*gh auth status" <<<"$err" || fail "failed read: $err"
python3 - "$FAKE_GH/pr/7.json" <<'EOF'   # a second marker comment: refused, nothing written
import json, sys; d = json.load(open(sys.argv[1])); c = dict(d["comments"][0]); c["url"] = c["url"][:-4] + "1099"
d["comments"].append(c); json.dump(d, open(sys.argv[1] + ".two", "w"))
EOF
mv "$FAKE_GH/pr/7.json.two" "$t/two.json"
n="$(writes)"   # merge-ask never writes from here on

# --- merge-ask ---
body() { # complete section, overridable by env: HEADL ROWS BUILT FAILED REVIEW
  cat <<EOF
Closes #6

## Summary

Lane work.

## Merge ask

Head: ${HEADL-${H:0:12}}
Checks: check, ci/x pass on ${H:0:12}
| criterion | qc verdict | evidence |
|---|---|---|
${ROWS-| demo#acceptance-a | pass | qc report a1b2.json, cmd ok |
| acceptance-b | pass | qc report a1b2.json, cmd ok |}
Review verdict: ${REVIEW-$url}
Built: ${BUILT-demo#acceptance-a acceptance-b}
${FAILED-Failed: none}

## Notes

after the section
EOF
}
setpr() { # PYTHON edits d, the good PR (body from body())
  python3 - "$t/pr7.keep" "$FAKE_GH/pr/7.json" "$(body)" "${1:-}" <<'EOF'
import json, sys; d = json.load(open(sys.argv[1])); d["body"] = sys.argv[3]; exec(sys.argv[4]); json.dump(d, open(sys.argv[2], "w"))
EOF
}
bad() { # WANT_PATTERN [PY]: merge-ask exits 1 naming it
  setpr "${2:-}"; run 1 merge-ask 7 "${ST[@]}"
  grep -q -- "$1" <<<"$err" || fail "merge-ask did not say '$1': $err"
  [[ -z "$out" ]] || fail "a failing merge ask printed to stdout: $out"
}

setpr; run 0 merge-ask 7 "${ST[@]}"
[[ "$(head -1 <<<"$out")" == "## Merge ask" && "$(tail -1 <<<"$out")" == "Failed: none" ]] || fail "pass did not print the section: $out"
grep -q "Review verdict: $url" <<<"$out" && ! grep -q "Notes\|Summary" <<<"$out" || fail "printed more or less than the section: $out"
[[ "$(writes)" == "$n" ]] || fail "merge-ask wrote"
# the same PR through the qc judge's offline gh (snapshot layout of octo-feather-qc-ghsnap)
snap="$t/snap"; mkdir -p "$snap/pr"; echo '{"repo": "o/r", "counts": {}, "capped": []}' > "$snap/meta.json"; echo x > "$snap/fetched_at"
cp "$FAKE_GH/pr/7.json" "$snap/pr/7.json"
out="$(cd "$t" && OCTO_FEATHER_GHSNAP="$snap" PATH="$kit/scripts/qc-bin:$PATH" "$L" merge-ask 7 "${ST[@]}")" || fail "merge-ask under the offline gh failed"
[[ "$(head -1 <<<"$out")" == "## Merge ask" ]] || fail "offline gh pass: $out"
set +e; err="$(cd "$t" && OCTO_FEATHER_GHSNAP="$snap" PATH="$kit/scripts/qc-bin:$PATH" "$L" verdict 7 "$H" "$t/report2" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] && grep -q "was not updated.*offline read-only snapshot\|offline read-only snapshot.*was not updated" <<<"$err" || fail "verdict under the offline gh: $rc $err"
# a failed criterion with triage passes; Failed bullet forms
FAILED=$'Failed:\n- acceptance-c: outside the lane, the spec behaviour is untouched (reason)' \
  ROWS=$'| demo#acceptance-a | pass | r |\n| demo#acceptance-b | pass | r |\n| demo#acceptance-c | fail | r, output x |' setpr
run 0 merge-ask 7 "${ST[@]}"; grep -q "^- acceptance-c: outside" <<<"$out" || fail "triaged fail: $out"

# PR #16's real body: no section, each item named
cp "$kit/tests/fixtures/lane-merge-ask/pr16.json" "$FAKE_GH/pr/16.json"
run 1 merge-ask 16 --status "$kit/docs/specs/overview.status.json"
for item in '`## Merge ask` section' 'Head: missing' 'Checks: missing' 'criterion table: missing' 'Review verdict: missing' 'Built: missing' 'Failed: missing'; do
  grep -qF -- "  - $item" <<<"$err" || fail "PR #16: '$item' not named: $err"
done

# each single gap fails, naming it
HEADL="${OTHER:0:12}" bad "Head: names ${OTHER:0:12}, the PR's head is ${H:0:12} (stale)"
HEADL="" bad "Head: missing"
bad "Checks: failing on head .*: check failure" 'd["statusCheckRollup"][0]["conclusion"] = "FAILURE"'
bad "Checks: pending on head .*: check in_progress" 'd["statusCheckRollup"][0].update(status="IN_PROGRESS", conclusion="")'
bad "Checks: pending on head .*: ci/x pending" 'd["statusCheckRollup"][1]["state"] = "PENDING"'
bad "Checks: failing on head .*: ci/x error" 'd["statusCheckRollup"][1]["state"] = "ERROR"'
bad "Checks: none reported" 'd["statusCheckRollup"] = []'
ROWS='| demo#acceptance-a | pass | r |' bad "criterion row demo#acceptance-b: missing (it is in Built)"
ROWS=$'| demo#acceptance-a | pass | r |\n| demo#acceptance-b | pass | |' bad "criterion row demo#acceptance-b: no evidence"
ROWS=$'| demo#acceptance-a | pass | r |\n| demo#acceptance-b | ok | r |' bad "qc verdict 'ok'; write pass or fail"
ROWS=$'| demo#acceptance-a | pass | r |\n| demo#acceptance-b | pass | r |\n| demo#acceptance-zz | pass | r |' bad "acceptance-zz: no criterion"
BUILT='demo#acceptance-a' bad "Built: lists demo#acceptance-a, the status files hold built with PR #7: demo#acceptance-a demo#acceptance-b"
bad "the PR's .qc: built. commits passed acceptance-a; list exactly those" \
  'd["commits"][1]["messageHeadline"] = "qc: built acceptance-a (judged 0123456789ab)"'
bad "no .qc: built. commit on PR #7" 'd["commits"] = d["commits"][:1]'
# a headline GitHub cut with an ellipsis still counts as one qc commit
setpr 'd["commits"][1].update(messageHeadline="qc: built acceptance-a acceptance-\u2026", messageBody="\u2026b (judged 0123456789ab)")'
run 0 merge-ask 7 "${ST[@]}"
REVIEW="" bad "Review verdict: empty is not a comment on PR #7"
REVIEW="https://github.com/o/r/pull/8#issuecomment-1001" bad "is not a comment on PR #7"
REVIEW="${url%1001}4242" bad "comment 4242 not on PR #7"
bad "the comment names head $OTHER, not ${H:0:12}" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('$H', '$OTHER')"
bad "Review verdict: blocking, not clear" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Verdict: clear', 'Verdict: blocking')"
bad "is not a verdict comment (no marker)" "d['comments'][0]['body'] = 'Verdict: clear'"
ROWS=$'| demo#acceptance-a | pass | r |\n| demo#acceptance-b | pass | r |\n| demo#acceptance-c | fail | r |' bad "criterion row demo#acceptance-c: fail with no triage"
FAILED=$'Failed:\n- acceptance-c:' ROWS=$'| demo#acceptance-a | pass | r |\n| demo#acceptance-b | pass | r |\n| demo#acceptance-c | fail | r |' \
  bad "Failed: demo#acceptance-c has no triage"
FAILED=$'Failed:\n- acceptance-c: repair ticket #9' bad "criterion row demo#acceptance-c: missing (it is in Failed)"
FAILED='Failed: some' bad "Failed: 'some'; write"
# multi-spec lane: --status once per spec; a qc id with no --status file is named
python3 - "$t/pr7.keep" <<'EOF'
import json, sys; d = json.load(open(sys.argv[1])); d["commits"].append({"oid": "3", "messageHeadline": "qc: built acceptance-x (judged 0123456789ab)", "messageBody": ""})
json.dump(d, open(sys.argv[1], "w"))
EOF
bad "acceptance-x in no --status file: pass --status for its spec"
ROWS=$'| demo#acceptance-a | pass | r |\n| demo#acceptance-b | pass | r |\n| other#acceptance-x | pass | r |' BUILT='acceptance-a acceptance-b other#acceptance-x' setpr
run 0 merge-ask 7 "${ST[@]}" --status "$t/other.status.json"
# usage and execution failures
run 1 merge-ask 7; grep -q "name the lane's status file" <<<"$err" || fail "no --status: $err"
run 1 merge-ask 7 --status "$t/nope.json"; grep -q "not a readable status file" <<<"$err" || fail "bad --status: $err"
run 1 merge-ask 0 "${ST[@]}"; grep -q "positive integer" <<<"$err" || fail "PR 0: $err"
FAKE_GH_FAIL="read" run 1 merge-ask 7 "${ST[@]}"; grep -q "error connecting.*gh auth status" <<<"$err" || fail "failed read: $err"
echo '{"number": 7}' > "$FAKE_GH/pr/7.json"; run 1 merge-ask 7 "${ST[@]}"; grep -q "lacks fields" <<<"$err" || fail "short gh data: $err"
cp "$t/two.json" "$FAKE_GH/pr/7.json"; run 1 verdict 7 "$H" "$t/report"
grep -q "has 2 verdict comments.*delete all but one" <<<"$err" || fail "two marker comments: $err"
[[ "$(writes)" == "$n" ]] || fail "a merge-ask or refused verdict wrote"
echo "lane-merge-ask: ok (verdict create, update in place, unchanged, refusals and failed writes leave no comment; merge-ask pass prints the section, offline gh, PR #16 names each item, stale head, failing/pending/no checks, rows, Built vs status and qc commits, verdict link head/blocking/marker, untriaged fail, multi-spec)"
