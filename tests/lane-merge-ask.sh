#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane verdict and merge-ask (spec issue-lifecycle
# #acceptance-merge-ask-evidence, issue #48), no network: a fake `gh` holds PR #7 of o/r and logs
# every call. `verdict` creates the one marker comment, updates it in place on rerun, and refuses a
# wrong head, a report with no verdict or no check classes (docs/adr/0008), a proxy check with a clear verdict
# and a failed write, leaving no comment behind. `merge-ask`
# passes a complete section and prints it (also through the qc judge's offline gh, github-pr/scripts/gh),
# fails PR #16's real body (fixture) naming each missing item, and fails each single gap: no parent line
# (the tracker skill's pr-line for the PR branch: Closes #6 on GitHub; a Linear target's lane passes with
# Tracks ENG-123 and no Closes line, and fails with one, spec #acceptance-pr-tracks), stale head,
# failing or pending check, missing row, Built unequal to the status file or to the qc commits,
# verdict link to another head or a blocking verdict, untriaged failed criterion. One judged head (spec
# #acceptance-one-head), on a real git lane: review on J plus qc's status commit H passes with the
# check's proof line; a non-status file after J fails naming it; a clean main merge keeps the qc
# verdict and prints its proof; a main merge touching a lane file or resolving a conflict fails.
# Run by `just check`.
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

# The lane worktree: a git repo whose origin/main is B; the lane commits J (code, the judged head)
# and qc's status commit H (the PR head H'). merge-ask reads it from the current directory.
R="$t/repo"; mkdir -p "$R/docs/specs"; cd "$R"
git init -q -b main .; git config user.email t@example.com; git config user.name t; git config commit.gpgsign false
status() { # A_B_STATUS A_B_PR
  printf '{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {\n  "acceptance-a": {"status": "%s", "pr": %s}, "acceptance-b": {"status": "%s", "pr": %s},\n  "acceptance-c": {"status": "planned", "pr": null}, "acceptance-d": {"status": "built", "pr": 3}}}\n' "$1" "$2" "$1" "$2" > docs/specs/demo.status.json; }
commit() { git add -A; git commit -q -m "$1"; git rev-parse HEAD; }
status planned null; seq 1 20 > app.py; echo notes > notes.txt
echo '{"spec": "other.spec.html", "accepted_commit": "0123abc", "criteria": {"acceptance-x": {"status": "built", "pr": 7}}}' > docs/specs/other.status.json
B="$(commit base)"; git update-ref refs/remotes/origin/main "$B"; git checkout -q -b lane
sed -i 1s/.*/one/ app.py; J="$(commit "feat: x")"
status built 7; H="$(commit "qc: built acceptance-a acceptance-b (judged ${J:0:12})")"
JS="${J:0:7}"
OTHER="$(printf 'ffee%.0s' 1 2 3 4 5 6 7 8 9 10)"
ST=(--status docs/specs/demo.status.json)
check_ok='[{"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"}, {"__typename": "StatusContext", "context": "ci/x", "state": "SUCCESS"}]'
commits="[{\"oid\": \"$J\", \"messageHeadline\": \"feat: x\", \"messageBody\": \"\"},
  {\"oid\": \"$H\", \"messageHeadline\": \"qc: built acceptance-a acceptance-b (judged ${J:0:12})\", \"messageBody\": \"\"}]"
printf '{"number": 7, "headRefName": "gh6", "headRefOid": "%s", "body": "", "statusCheckRollup": %s, "comments": [], "commits": %s}\n' "$H" "$check_ok" "$commits" > "$FAKE_GH/pr/7.json"
PROOF="${J:0:12} to ${H:0:12}: qc status commits ${H:0:12} change only docs/specs/demo.status.json"

run() { local want="$1"; shift; set +e; out="$("$L" "$@" 2>"$t/err")"; rc=$?; err="$(cat "$t/err")"; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"
  grep -q Traceback <<<"$err" && fail "'$*' printed a traceback: $err"; return 0; }
comments() { python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["comments"]))' "$FAKE_GH/pr/7.json"; }
writes() { grep -c '^api' "$FAKE_GH_LOG" || true; }

# --- verdict: create once, update in place, refusals write nothing ---
printf 'Findings: none blocking.\nChecks: none\nVerdict: clear\n' > "$t/report"
: > "$FAKE_GH_LOG"
run 0 verdict 7 "$JS" "$t/report"   # the review judged J, while qc made H
url="$out"; [[ "$url" == "https://github.com/o/r/pull/7#issuecomment-1001" ]] || fail "verdict printed $url"
grep -q '^api -X POST repos/{owner}/{repo}/issues/7/comments ' "$FAKE_GH_LOG" || fail "no POST: $(cat "$FAKE_GH_LOG")"
[[ "$(comments)" == 1 ]] || fail "create made $(comments) comments"
printf 'Note: a nit.\nChecks: none\nVerdict: blocking\n' > "$t/report2"
run 0 verdict 7 "$J" "$t/report2"
[[ "$out" == "$url" && "$(comments)" == 1 ]] || fail "rerun did not update in place: $out, $(comments) comments"
grep -q '^api -X PATCH repos/{owner}/{repo}/issues/comments/1001 ' "$FAKE_GH_LOG" || fail "no PATCH of 1001: $(cat "$FAKE_GH_LOG")"
python3 - "$FAKE_GH/pr/7.json" "$J" "$H" <<'EOF' || fail "comment body after update"
import json, sys; b = json.load(open(sys.argv[1]))["comments"][0]["body"]
assert b.startswith("<!-- octo-feather-review-verdict -->") and f"Head: {sys.argv[2]}\nPR head: {sys.argv[3]}\n" in b and "Verdict: blocking\n" in b and "a nit" in b, b
EOF
run 0 verdict 7 "$J" - < "$t/report"   # stdin, back to clear
[[ "$(writes)" == 3 && "$(comments)" == 1 ]] || fail "third run: $(writes) writes, $(comments) comments"
run 0 verdict 7 "$J" "$t/report"; [[ "$(writes)" == 3 ]] || fail "unchanged rerun wrote"
grep -q unchanged <<<"$err" || fail "unchanged rerun not said: $err"
# the verdict is the last line outside fences and quotes (review of 39515df, class verdict-parsing)
printf 'Ran the gate:\n```\nVerdict: clear\n```\n> Verdict: clear\n\nThe quoted run predates the fix commit.\nChecks: none\nVerdict: blocking\n' > "$t/fenced"
run 0 verdict 7 "$J" "$t/fenced"; grep -q "(blocking, head" <<<"$err" || fail "fenced Verdict: clear was taken: $err"
python3 -c 'import json,sys; b=json.load(open(sys.argv[1]))["comments"][0]["body"]; assert "\nVerdict: blocking\nChecks: none\n\n### Findings" in b, b' "$FAKE_GH/pr/7.json" \
  || fail "fenced report posted the wrong verdict"
# #144, #121 D10: a blank line after a quote, then lazy continuation lines after quotes (below).
printf '> the implementer wrote:\n\nVerdict: blocking\nChecks: none\n' > "$t/lazyend"
run 0 verdict 7 "$J" "$t/lazyend"; grep -q "(blocking, head" <<<"$err" || fail "Verdict after a blank line ending the quote: $err"
printf '> > nested:\n~~~\nVerdict: clear\n~~~\nChecks: none\nVerdict: blocking\n' > "$t/qfence"   # a fence interrupts the quote, ~~~ fences
run 0 verdict 7 "$J" "$t/qfence"; grep -q "(blocking, head" <<<"$err" || fail "~~~ fence after a quote: $err"
# PR #140 review finding 2 (owner: CommonMark fenced code, #144): the literal report, its first line indented
# code, posts; in a list item the fence's indent counts from the item's content.
printf '    ```\n\nVerdict: clear\nChecks: none\n' > "$t/indented"; : > "$FAKE_GH_LOG"
run 0 verdict 7 "$J" "$t/indented"; grep -q "(clear, head" <<<"$err" && grep -q '^api -X PATCH' "$FAKE_GH_LOG" || fail "4-space indented backticks read as a fence: $err"
printf -- '- item:\n\n    ```\n    Verdict: clear\n    ```\nChecks: none\nVerdict: blocking\n' > "$t/itemfence"
run 0 verdict 7 "$J" "$t/itemfence"; grep -q "(blocking, head" <<<"$err" || fail "fence in a list item not read as one: $err"
# check classes (docs/adr/0008, issue #118): a proxy check posts only with a blocking verdict, in the header
printf 'Check: `scripts/check-x`: tests reach no internals (docs/adr/0002) | reads: code tokens in tests/*.sh | class: Proxy\nVerdict: blocking\n' > "$t/proxy"
run 0 verdict 7 "$J" "$t/proxy"
python3 -c 'import json,sys; b=json.load(open(sys.argv[1]))["comments"][0]["body"]; assert "\nVerdict: blocking\nCheck: scripts/check-x: tests reach no internals (docs/adr/0002) | reads: code tokens in tests/*.sh | class: proxy\n\n### Findings" in b, b' "$FAKE_GH/pr/7.json" \
  || fail "proxy check not in the verdict header"
run 0 verdict 7 "$J" "$t/report"   # back to clear
# refusals: each non-zero, fix named, no write
n="$(writes)"
run 1 verdict 7 "$OTHER" "$t/report"; grep -q "is not a commit of PR #7 (head ${H:0:12}): push the reviewed head" <<<"$err" || fail "wrong head: $err"
printf 'looks fine\n' > "$t/nov"; run 1 verdict 7 "$J" "$t/nov"; grep -q 'add a line `Verdict: clear`' <<<"$err" || fail "no verdict: $err"
for q in '> the implementer wrote:' '> > nested, quoted:' '> - a quoted item' '>     quoted code\n> the reply'; do   # D10: lazy continuation
  printf "$q"'\nVerdict: clear\nChecks: none\n' > "$t/lazy"; run 1 verdict 7 "$J" "$t/lazy"
  grep -q 'report names no verdict' <<<"$err" || fail "lazy Verdict line after '$q' counted: $err"
done
printf 'Verdict: clear\n> quoted:\nChecks: none\n' > "$t/lazycls"; run 1 verdict 7 "$J" "$t/lazycls"
grep -q 'report classifies no check' <<<"$err" || fail "lazy Checks line counted: $err"
printf 'Verdict: clear\nmore\nVerdict: blocking\n' > "$t/both"; run 1 verdict 7 "$J" "$t/both"
grep -q "verdicts that disagree (clear, blocking): keep one" <<<"$err" || fail "disagreeing verdicts: $err"
printf 'Verdict: clear\n```\nChecks: none\n```\n' > "$t/nocls"; run 1 verdict 7 "$J" "$t/nocls"
grep -q 'report classifies no check: add `Checks: none` when' <<<"$err" || fail "no classification (fenced one ignored): $err"
printf 'Check: scripts/check-x: tests reach no internals (docs/adr/0002) | reads: code tokens | class: proxy\nVerdict: clear\n' > "$t/mclear"; run 1 verdict 7 "$J" "$t/mclear"
grep -q 'with a proxy check (Check: scripts/check-x: .*): a proxy check blocks (docs/adr/0008)' <<<"$err" || fail "proxy + clear: $err"
printf 'Check: scripts/check-x: r (ADR 1) | reads: y | class: meaning\nVerdict: blocking\n' > "$t/badcls"; run 1 verdict 7 "$J" "$t/badcls"
grep -q "has class 'meaning'; write .class: exact. or .class: proxy." <<<"$err" || fail "bad class: $err"
printf 'Check: scripts/check-x is a fact\nVerdict: clear\n' > "$t/badshape"; run 1 verdict 7 "$J" "$t/badshape"
grep -q 'check line `Check: scripts/check-x is a fact` is not `Check: <path>' <<<"$err" || fail "malformed check line: $err"
# The rule names its owner (review of 2e1a0da, class unvalidated-input): none, or empty parentheses, refused.
for r in 'r' 'r ()' 'r (  )' '(ADR 1)'; do
  printf 'Check: scripts/x: %s | reads: y | class: exact\nVerdict: clear\n' "$r" > "$t/noowner"; run 1 verdict 7 "$J" "$t/noowner"
  grep -q 'check line for scripts/x names no owner: write its rule as stated where it is owned' <<<"$err" || fail "no owner ($r): $err"
done
printf 'Checks: fine\nVerdict: clear\n' > "$t/badnone"; run 1 verdict 7 "$J" "$t/badnone"
grep -q '`Checks: fine`; `Checks:` takes only `none`' <<<"$err" || fail "Checks: other: $err"
printf 'Checks: none\nCheck: scripts/check-x: r (ADR 1) | reads: y | class: exact\nVerdict: clear\n' > "$t/bothcls"; run 1 verdict 7 "$J" "$t/bothcls"
grep -q 'has `Checks: none` and `Check:` lines' <<<"$err" || fail "none and lines: $err"
run 1 verdict 7 "$J" "$t/missing"; grep -q "cannot read report" <<<"$err" || fail "missing report: $err"
: > "$t/empty"; run 1 verdict 7 "$J" "$t/empty"; grep -q "is empty" <<<"$err" || fail "empty report: $err"
run 1 verdict 7 xyz "$t/report"; grep -q "commit sha" <<<"$err" || fail "bad head: $err"
run 1 verdict 7 "$J"; grep -q usage <<<"$err" || fail "usage: $err"
run 1 verdict 9 "$J" "$t/report"; grep -q "check PR #9 exists" <<<"$err" || fail "unknown PR: $err"
[[ "$(writes)" == "$n" ]] || fail "a refusal wrote"
# execution failures: a failed create leaves no comment; a failed read names the fix
cp "$FAKE_GH/pr/7.json" "$t/pr7.keep"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); d["comments"]=[]; json.dump(d,open(sys.argv[1],"w"))' "$FAKE_GH/pr/7.json"
FAKE_GH_FAIL="write" run 1 verdict 7 "$J" "$t/report"
grep -q "was not created; fix the cause.*then rerun" <<<"$err" || fail "failed write: $err"
[[ "$(comments)" == 0 ]] || fail "failed create left a comment"
cp "$t/pr7.keep" "$FAKE_GH/pr/7.json"
FAKE_GH_FAIL="write" run 1 verdict 7 "$J" "$t/report2"; grep -q "was not updated" <<<"$err" || fail "failed update: $err"
grep -qF "Verdict: clear" <<<"$(cat "$FAKE_GH/pr/7.json")" || fail "failed update changed the comment"
FAKE_GH_FAIL="read" run 1 verdict 7 "$J" "$t/report"; grep -q "error connecting.*gh auth status" <<<"$err" || fail "failed read: $err"
python3 - "$FAKE_GH/pr/7.json" <<'EOF'   # a second marker comment: refused, nothing written
import json, sys; d = json.load(open(sys.argv[1])); c = dict(d["comments"][0]); c["url"] = c["url"][:-4] + "1099"
d["comments"].append(c); json.dump(d, open(sys.argv[1] + ".two", "w"))
EOF
mv "$FAKE_GH/pr/7.json.two" "$t/two.json"
n="$(writes)"   # merge-ask never writes from here on

# --- merge-ask ---
body() { # complete section, overridable by env: PARENTL HEADL JUDGEDL ROWS BUILT FAILED REVIEW
  cat <<EOF
${PARENTL-Closes #6}

## Summary

Lane work.

## Merge ask

Head: ${HEADL-${H:0:12}}
Checks: check, ci/x pass on ${H:0:12}
Judged: ${JUDGEDL-$PROOF}
| criterion | qc verdict | judged | evidence |
|---|---|---|---|
${ROWS-| demo#acceptance-a | pass | judged $JS | qc report a1b2.json, cmd ok |
| acceptance-b | pass | judged $JS | qc report a1b2.json, cmd ok |}
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
[[ "$(head -1 <<<"$out")" == "## Merge ask" ]] && grep -qx "Failed: none" <<<"$out" || fail "pass did not print the section: $out"
[[ "$(tail -2 <<<"$out")" == $'Review check classes (from the verdict comment, docs/adr/0008):\n- Checks: none' ]] || fail "pass did not list the check classes: $out"
grep -q "Review verdict: $url" <<<"$out" && ! grep -q "Notes\|Summary" <<<"$out" || fail "printed more or less than the section: $out"
[[ "$(writes)" == "$n" ]] || fail "merge-ask wrote"
# the same PR through the qc judge's offline gh (snapshot layout of octo-feather-qc-ghsnap)
snap="$t/snap"; mkdir -p "$snap/pr"; echo '{"repo": "o/r", "counts": {}, "capped": []}' > "$snap/meta.json"; echo x > "$snap/fetched_at"
cp "$FAKE_GH/pr/7.json" "$snap/pr/7.json"
out="$(cd "$R" && OCTO_FEATHER_GHSNAP="$snap" PATH="$kit/.agents/skills/github-pr/scripts:$PATH" "$L" merge-ask 7 "${ST[@]}")" || fail "merge-ask under the offline gh failed"
[[ "$(head -1 <<<"$out")" == "## Merge ask" ]] || fail "offline gh pass: $out"
set +e; err="$(cd "$R" && OCTO_FEATHER_GHSNAP="$snap" PATH="$kit/.agents/skills/github-pr/scripts:$PATH" "$L" verdict 7 "$H" "$t/report2" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] && grep -q "was not updated.*offline read-only snapshot\|offline read-only snapshot.*was not updated" <<<"$err" || fail "verdict under the offline gh: $rc $err"
# a failed criterion with triage passes; Failed bullet forms
FAILED=$'Failed:\n- acceptance-c: outside the lane, the spec behaviour is untouched (reason)' \
  ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |\n| demo#acceptance-c | fail | judged '"$JS"$' | r, output x |' setpr
run 0 merge-ask 7 "${ST[@]}"; grep -q "^- acceptance-c: outside" <<<"$out" || fail "triaged fail: $out"

# the parent line (spec #gates-pr-line): the tracker skill's pr-line for the key the PR branch names
PARENTL="" bad "parent line: missing; add the line \`Closes #6\` (the tracker skill's pr-line 6)"
PARENTL="Closes #60" bad "parent line: missing; add the line \`Closes #6\`"
PARENTL=$'Closes #6\nAlso fixes #9' bad "parent line: \`Also fixes #9\` closes GitHub issue #9, not the lane's parent line \`Closes #6\`"
# only the parent's own closing link is exempt, never the rest of its line; an issue URL closes too
PARENTL="Closes #6, fixes #9" bad "parent line: \`Closes #6, fixes #9\` closes GitHub issue #9, not the lane's parent line \`Closes #6\`"
PARENTL="Closes #6 closes o/r#6" bad "parent line: \`Closes #6 closes o/r#6\` closes GitHub issue #6"
PARENTL=$'Closes #6\nResolves https://github.com/o/r/issues/9' bad "parent line: \`Resolves https://github.com/o/r/issues/9\` closes GitHub issue #9"
bad "parent line: cannot name it for branch 'main'" 'd["headRefName"] = "main"'
# a Linear target's lane (its .octo-feather.toml): Tracks ENG-123 for branch eng-123, no Closes line, passes
echo 'tracker = "linear"' > .octo-feather.toml
PARENTL="Tracks ENG-123" setpr 'd["headRefName"] = "eng-123"'; run 0 merge-ask 7 "${ST[@]}"
[[ "$(head -1 <<<"$out")" == "## Merge ask" ]] || fail "Linear lane with Tracks ENG-123 did not pass: $out"
bad "parent line: missing; add the line \`Tracks ENG-123\` (the tracker skill's pr-line ENG-123)" 'd["headRefName"] = "eng-123"'
PARENTL=$'Tracks ENG-123\nCloses #6' bad "parent line: \`Closes #6\` closes GitHub issue #6, not the lane's parent line \`Tracks ENG-123\`" 'd["headRefName"] = "eng-123"'
PARENTL="Tracks ENG-123; Closes #6" bad "parent line: \`Tracks ENG-123; Closes #6\` closes GitHub issue #6, not the lane's parent line \`Tracks ENG-123\`" 'd["headRefName"] = "eng-123"'
PARENTL="Tracks ENG-1234" bad "parent line: missing; add the line \`Tracks ENG-123\`" 'd["headRefName"] = "eng-123"'
rm .octo-feather.toml

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
ROWS="| demo#acceptance-a | pass | judged $JS | r |" bad "criterion row demo#acceptance-b: missing (it is in Built)"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | |' bad "criterion row demo#acceptance-b: no evidence"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | ok | judged '"$JS"$' | r |' bad "qc verdict 'ok'; write pass or fail"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |\n| demo#acceptance-zz | pass | judged '"$JS"$' | r |' bad "acceptance-zz: no criterion"
BUILT='demo#acceptance-a' bad "Built: lists demo#acceptance-a, the status files hold built with PR #7: demo#acceptance-a demo#acceptance-b"
# a Built id the status file holds but no qc: built commit names fails
bad "Built: demo#acceptance-b in no .qc: built. commit of PR #7 (they passed acceptance-a); built only by just qc" \
  'd["commits"][1]["messageHeadline"] = "qc: built acceptance-a (judged 0123456789ab)"'
# built by an earlier qc run, reset to planned by a later one (PR #49: ac060f9, a56de61): not demanded, passes
setpr 'd["commits"].insert(1, {"oid": "c0ffee0000000000000000000000000000000000", "messageHeadline": "qc: built acceptance-a acceptance-c (judged 0123456789ab)", "messageBody": ""})'
run 0 merge-ask 7 "${ST[@]}"
bad "no .qc: built. commit on PR #7" 'd["commits"] = d["commits"][:1]'
# a headline GitHub cut with an ellipsis still counts as one qc commit
setpr 'd["commits"][1].update(messageHeadline="qc: built acceptance-a acceptance-\u2026", messageBody="\u2026b (judged 0123456789ab)")'
run 0 merge-ask 7 "${ST[@]}"
REVIEW="" bad "Review verdict: empty is not a comment on PR #7"
REVIEW="https://github.com/o/r/pull/8#issuecomment-1001" bad "is not a comment on PR #7"
REVIEW="${url%1001}4242" bad "comment 4242 not on PR #7"
bad "the comment names head $OTHER, not the judged head ${J:0:12}" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Head: $J', 'Head: $OTHER')"
bad "Review verdict: blocking, not clear" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Verdict: clear', 'Verdict: blocking')"
bad "Review verdict: the comment carries no usable check classification (report classifies no check" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('\\nChecks: none\\n', '\\n')"
bad "Review verdict: clear with a proxy check (Check: scripts/x: r (ADR 1) | reads: y | class: proxy): a proxy check blocks" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Checks: none', 'Check: scripts/x: r (ADR 1) | reads: y | class: proxy')"
setpr "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Checks: none', 'Check: scripts/x: r (ADR 1) | reads: y | class: exact')"
run 0 merge-ask 7 "${ST[@]}"; [[ "$(tail -1 <<<"$out")" == "- Check: scripts/x: r (ADR 1) | reads: y | class: exact" ]] || fail "exact check not listed: $out"
bad "is not a verdict comment (no marker)" "d['comments'][0]['body'] = 'Verdict: clear'"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |\n| demo#acceptance-c | fail | judged '"$JS"$' | r |' bad "criterion row demo#acceptance-c: fail with no triage"
FAILED=$'Failed:\n- acceptance-c:' ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |\n| demo#acceptance-c | fail | judged '"$JS"$' | r |' \
  bad "Failed: demo#acceptance-c has no triage"
FAILED=$'Failed:\n- acceptance-c: repair ticket #9' bad "criterion row demo#acceptance-c: missing (it is in Failed)"
FAILED='Failed: some' bad "Failed: 'some'; write"
# one judged head (spec #acceptance-one-head): review and qc judged J; H' may add only qc's status
# commit and clean merges of main that leave the lane's own diff identical, each with the check's proof
setpr; run 0 merge-ask 7 "${ST[@]}"; grep -qF "Judged: $PROOF" <<<"$out" || fail "pass did not print the proof: $out"
JUDGEDL="" bad "Judged: names ''; add the check's proof line \`Judged: $PROOF\`"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"${H:0:7}"$' | r |' bad "rows name 2 judged heads"
on() { # PARENT CMD...: run CMD on a detached checkout of PARENT, print the new HEAD, back on the lane
  git checkout -q --detach "$1"; shift; "$@" >/dev/null; git rev-parse HEAD; git checkout -q -f lane; }
pr_head() { # SHA SUBJECT: python making SHA the PR head, a commit of the PR
  echo "d['headRefOid'] = '$1'; d['commits'].append({'oid': '$1', 'messageHeadline': '$2', 'messageBody': ''})"; }
F="$(on "$H" sh -c 'echo two >> app.py; git commit -qam "feat: after qc"')"
HEADL="${F:0:12}" bad "Judged: commit ${F:0:12} 'feat: after qc' after the judged head ${J:0:12} changes app.py, not only the status file qc writes (docs/specs/demo.status.json): run just qc and the review again, in parallel, on ${F:0:12}" "$(pr_head "$F" "feat: after qc")"
# qc's own commit carrying a non-status file fails, naming the file
Q="$(on "$J" sh -c 'sed -i "s/\"planned\", \"pr\": null}, \"acceptance-b/\"built\", \"pr\": 7}, \"acceptance-b/" docs/specs/demo.status.json; echo x > stray.txt; git add -A; git commit -qm "qc: built acceptance-a (judged '"${J:0:12}"')"')"
HEADL="${Q:0:12}" bad "commit ${Q:0:12} 'qc: built acceptance-a (judged ${J:0:12})' after the judged head ${J:0:12} changes stray.txt, not only" "$(pr_head "$Q" "qc: built acceptance-a (judged ${J:0:12})")"
S="$(on "$H" sh -c 'sed -i s/acceptance-d/acceptance-d/ docs/specs/demo.status.json; echo " " >> docs/specs/demo.status.json; git commit -qam "fix status"')"
HEADL="${S:0:12}" bad "commit ${S:0:12} 'fix status' after the judged head ${J:0:12} is not a .qc: built" "$(pr_head "$S" "fix status")"
# qc reran at the exact head, nothing to flip: no status commit, passes
HEADL="${F:0:12}" JUDGEDL="${F:0:12} is the PR head" ROWS=$'| demo#acceptance-a | pass | judged '"${F:0:9}"$' | r |\n| demo#acceptance-b | pass | judged '"${F:0:9}"' | r |' \
  setpr "$(pr_head "$F" "feat: after qc"); d['comments'][0]['body'] = d['comments'][0]['body'].replace('Head: $J', 'Head: $F')"
run 0 merge-ask 7 "${ST[@]}"
# a clean main merge keeps the qc verdict: the check prints its proof line
M1="$(on "$B" sh -c 'echo main >> notes.txt; git commit -qam "main: notes"')"; git update-ref refs/remotes/origin/main "$M1"
R1="$(on "$H" git merge -q --no-edit "$M1")"
HEADL="${R1:0:12}" bad "add the check's proof line .Judged: ${J:0:12} to ${R1:0:12}: qc status commits ${H:0:12} change only docs/specs/demo.status.json; clean merge of main ${R1:0:12}: lane diff identical (1 file, sha256 [0-9a-f]\{12\})." "$(pr_head "$R1" "Merge main")"
proof="$(sed -n 's/.*add the check.s proof line `Judged: \(.*\)`$/\1/p' <<<"$err")"
HEADL="${R1:0:12}" JUDGEDL="$proof" setpr "$(pr_head "$R1" "Merge main")"
run 0 merge-ask 7 "${ST[@]}"; grep -qF "Judged: $proof" <<<"$out" || fail "clean refresh: proof not in the section: $out"
# a main merge touching a lane file, resolving a conflict, or merging another branch: qc reruns
M2="$(on "$M1" sh -c 'sed -i 20s/.*/twenty/ app.py; git commit -qam "main: app tail"')"; git update-ref refs/remotes/origin/main "$M2"
R2="$(on "$H" git merge -q --no-edit "$M2")"
HEADL="${R2:0:12}" bad "Judged: after merging origin/main, the lane's own diff changed in app.py (main touched a lane file, or the lane's diff moved): the qc verdict does not carry over; run just qc and the review again, in parallel, on ${R2:0:12}" "$(pr_head "$R2" "Merge main")"
M3="$(on "$M1" sh -c 'sed -i 1s/.*/uno/ app.py; git commit -qam "main: app head"')"; git update-ref refs/remotes/origin/main "$M3"
R3="$(on "$H" sh -c "git merge -q --no-edit $M3 2>/dev/null; git checkout -q --ours app.py; git commit -qam 'Merge main, conflict resolved'")"
HEADL="${R3:0:12}" bad "Judged: merge ${R3:0:12} 'Merge main, conflict resolved' resolved a conflict with origin/main: the qc verdict does not carry over" "$(pr_head "$R3" "Merge main, conflict resolved")"
git update-ref refs/remotes/origin/main "$M1"
X="$(on "$B" sh -c 'echo side > side.txt; git add side.txt; git commit -qm side')"
R4="$(on "$H" git merge -q --no-edit "$X")"
HEADL="${R4:0:12}" bad "Judged: merge ${R4:0:12} .* brings in ${X:0:12}, not origin/main: only a merge of main keeps the qc verdict" "$(pr_head "$R4" "Merge side")"
ROWS=$'| demo#acceptance-a | pass | judged deadbee | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |' bad "criterion row demo#acceptance-a: judged deadbee is not a commit of PR #7; name the head qc and the review judged"
ROWS=$'| demo#acceptance-a | pass | yesterday | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |' bad "judged 'yesterday'; write .judged <sha>."
python3 - "$t/pr7.keep" "$(body)" <<'PY' > "$t/old.body"
import sys; print(sys.argv[2].replace("| criterion | qc verdict | judged | evidence |", "| criterion | qc verdict | evidence |"))
PY
bad "criterion table: no judged column" "d['body'] = open('$t/old.body').read()"
# multi-spec lane: --status once per spec; a qc id outside the --status files is not demanded
python3 - "$t/pr7.keep" <<'EOF'
import json, sys; d = json.load(open(sys.argv[1])); d["commits"].append({"oid": "3333333333333333333333333333333333333333", "messageHeadline": "qc: built acceptance-x (judged 0123456789ab)", "messageBody": ""})
json.dump(d, open(sys.argv[1], "w"))
EOF
setpr; run 0 merge-ask 7 "${ST[@]}"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |\n| other#acceptance-x | pass | judged '"$JS"$' | r |' BUILT='acceptance-a acceptance-b other#acceptance-x' setpr
run 0 merge-ask 7 "${ST[@]}" --status docs/specs/other.status.json
# usage and execution failures
run 1 merge-ask 7; grep -q "name the lane's status file" <<<"$err" || fail "no --status: $err"
run 1 merge-ask 7 --status "$t/nope.json"; grep -q "not a readable status file" <<<"$err" || fail "bad --status: $err"
run 1 merge-ask 0 "${ST[@]}"; grep -q "positive integer" <<<"$err" || fail "PR 0: $err"
FAKE_GH_FAIL="read" run 1 merge-ask 7 "${ST[@]}"; grep -q "error connecting.*gh auth status" <<<"$err" || fail "failed read: $err"
echo '{"number": 7}' > "$FAKE_GH/pr/7.json"; run 1 merge-ask 7 "${ST[@]}"; grep -q "lacks fields" <<<"$err" || fail "short gh data: $err"
cp "$t/two.json" "$FAKE_GH/pr/7.json"; run 1 verdict 7 "$H" "$t/report"
grep -q "has 2 verdict comments.*delete all but one" <<<"$err" || fail "two marker comments: $err"
[[ "$(writes)" == "$n" ]] || fail "a merge-ask or refused verdict wrote"
echo "lane-merge-ask: ok (verdict create, update in place, unchanged, refusals and failed writes leave no comment; merge-ask pass prints the section, offline gh, PR #16 names each item, parent line (GitHub Closes #6 required, a prefix, another closing line, a closing link after it on its line or an issue URL fails; a Linear lane passes on Tracks ENG-123, fails without it or with a Closes line, own or on its line), stale head, failing/pending/no checks, rows, Built = status and named by a qc commit (built-then-reset passes), verdict link head/blocking/marker, untriaged fail, multi-spec; verdict ignores fenced and quoted lines (#144 cases), disagreeing verdicts refused; check classes: proxy posts only as blocking, missing, malformed, no owner, other class, Checks: other, none plus lines refused, merge-ask lists them and refuses an unclassified or clear-with-proxy comment; one judged head: rows on two heads, a code commit after qc, a qc commit with a non-status file, a hand status edit, a sha not in the PR and an old table fail; exact-head rerun passes; a clean main merge passes with its proof line; a main merge touching a lane file, a resolved conflict or another branch fails)"
