#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane verdict, fields and merge-ask (spec issue-lifecycle
# #acceptance-merge-ask-evidence, issue #48), no network: a fake `gh` holds PR #7 of o/r and logs
# every call. `verdict` creates the one marker comment, updates it in place on rerun, and refuses a
# wrong head, a report with no verdict or no check classes (docs/adr/0008), a proxy check with a clear verdict
# and a failed write, leaving no comment behind. `merge-ask`
# passes a complete section and prints it, then labels each row with its latest qc result's decision source at the judged
# head (quality#acceptance-qc-fallback) (also through the qc judge's offline gh, github-pr/scripts/gh),
# fails PR #16's real body (fixture) naming each missing item, and fails each single gap: no parent line
# (the tracker skill's pr-line for the PR branch: Closes #6 on GitHub; a Linear target's lane passes with
# Tracks ENG-123 and no Closes line, and fails with one, spec #acceptance-pr-tracks), stale head,
# failing or pending check, missing row, Built unequal to the status file or to the qc commits,
# verdict link to another head or a blocking verdict, untriaged failed criterion. One judged head (spec
# #acceptance-one-head), on a real git lane: review on J plus qc's status commit H passes with the
# check's proof line; a non-status file after J fails naming it; a clean main merge keeps the qc
# verdict and prints its proof; a main merge touching a lane file or resolving a conflict fails.
# Full pass (#acceptance-merge-ask-full-proof): every merge ask needs a current recorded full gate pass.
# Gate time (#acceptance-merge-ask-gate-budget): the final head's full run against the budget, shown, never decided on.
# CI on a status-only head (#acceptance-ci-status-only): a check skipped there takes the judged head's CI, naming it;
# missing, pending, skipped or red there, or a code commit between them, refuses.
# Run by `just check`.
# criterion: issue-lifecycle#acceptance-merge-ask-full-proof
# criterion: issue-lifecycle#acceptance-ci-status-only
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-merge-ask test: $*" >&2; exit 1; }
export HOME="$t/home" FAKE_GH="$t/gh" FAKE_GH_LOG="$t/gh.log" XDG_STATE_HOME="$t/xdg"   # the state dir's check-runs.jsonl
unset HERDR_SESSION
export OCTO_FEATHER_QC_DIR="$t/qc"   # the qc reports merge-ask reads (octo-feather-qc --help, Report)
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
if a[0] == "api" and "-X" not in a and (r := re.fullmatch(r"repos/(?:\{owner\}/\{repo\}|o/r)/commits/([0-9a-f]+)/check-runs(\?.*)?", a[1])):
    p = f"{D}/runs/{r.group(1)}.json"   # a commit's check runs (REST), none when the file is absent
    print(open(p).read() if os.path.exists(p) else '{"total_count": 0, "check_runs": []}'); sys.exit(0)
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
printf 'budget_seconds = 150\ngrowth_share = 0.25\ntrend_runs = 3\n' > gate-budget.toml   # the repo's gate-time budget
printf '[demo."demo#acceptance-a"]\ncommand = "true"\n' > qc.toml   # the contract: a demo for acceptance-a only
echo '{"spec": "other.spec.html", "accepted_commit": "0123abc", "criteria": {"acceptance-x": {"status": "built", "pr": 7}}}' > docs/specs/other.status.json
B="$(commit base)"; git update-ref refs/remotes/origin/main "$B"; git checkout -q -b lane
sed -i 1s/.*/one/ app.py; J="$(commit "feat: x")"
G="$kit/scripts/octo-feather-gate"; "$G" record --reason "lane final head" --seconds 1 >/dev/null   # J's full gate pass
status built 7; H="$(commit "qc: built acceptance-a acceptance-b (judged ${J:0:12})")"
JS="${J:0:7}"
OTHER="$(printf 'ffee%.0s' 1 2 3 4 5 6 7 8 9 10)"
ST=(--status docs/specs/demo.status.json)
check_ok='[{"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"}, {"__typename": "StatusContext", "context": "ci/x", "state": "SUCCESS"}]'
commits="[{\"oid\": \"$J\", \"messageHeadline\": \"feat: x\", \"messageBody\": \"\"},
  {\"oid\": \"$H\", \"messageHeadline\": \"qc: built acceptance-a acceptance-b (judged ${J:0:12})\", \"messageBody\": \"\"}]"
printf '{"number": 7, "baseRefName": "main", "headRefName": "gh6", "headRefOid": "%s", "body": "", "statusCheckRollup": %s, "comments": [], "commits": %s}\n' "$H" "$check_ok" "$commits" > "$FAKE_GH/pr/7.json"
PROOF="${J:0:12} to ${H:0:12}: qc status commits ${H:0:12} change only docs/specs/demo.status.json"

run() { local want="$1"; shift; set +e; out="$("$L" "$@" 2>"$t/err")"; rc=$?; err="$(cat "$t/err")"; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"
  grep -q Traceback <<<"$err" && fail "'$*' printed a traceback: $err"; return 0; }
comments() { python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["comments"]))' "$FAKE_GH/pr/7.json"; }
writes() { grep -c '^api -X' "$FAKE_GH_LOG" || true; }   # a write; a GET (check runs) reads

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
# the verdict is the last line in the reader scope, .agents/skills/code-review/SKILL.md step 4 Report fields (review of 39515df, class verdict-parsing)
printf 'Ran the gate:\n```\nVerdict: clear\n```\n> Verdict: clear\n\nThe quoted run predates the fix commit.\nChecks: none\nVerdict: blocking\n' > "$t/fenced"
run 0 verdict 7 "$J" "$t/fenced"; grep -q "(blocking, head" <<<"$err" || fail "fenced Verdict: clear was taken: $err"
python3 -c 'import json,sys; b=json.load(open(sys.argv[1]))["comments"][0]["body"]; assert "\nVerdict: blocking\nChecks: none\n\n### Findings" in b, b' "$FAKE_GH/pr/7.json" \
  || fail "fenced report posted the wrong verdict"
# #144, #121 D10: a blank line after a quote, then lazy continuation lines after quotes (below).
printf '> the implementer wrote:\n\nVerdict: blocking\nChecks: none\n' > "$t/lazyend"
run 0 verdict 7 "$J" "$t/lazyend"; grep -q "(blocking, head" <<<"$err" || fail "Verdict after a blank line ending the quote: $err"
printf '> > nested:\n~~~\nVerdict: clear\n~~~\nChecks: none\nVerdict: blocking\n' > "$t/qfence"   # a fence interrupts the quote, ~~~ fences
run 0 verdict 7 "$J" "$t/qfence"; grep -q "(blocking, head" <<<"$err" || fail "~~~ fence after a quote: $err"
# PR #140 review rounds 2 and 3 (owner: markdown()'s scope, #144): the literal reports post.
printf '    ```\n\nVerdict: clear\nChecks: none\n' > "$t/indented"; : > "$FAKE_GH_LOG"
run 0 verdict 7 "$J" "$t/indented"; grep -q "(clear, head" <<<"$err" && grep -q '^api -X PATCH' "$FAKE_GH_LOG" || fail "4-space indented backticks read as a fence: $err"
printf -- '- item\n  > quote\n    ```\nVerdict: clear\nChecks: none\n' > "$t/itemquote"; : > "$FAKE_GH_LOG"
run 0 verdict 7 "$J" "$t/itemquote"; grep -q "(clear, head" <<<"$err" && grep -q '^api -X PATCH' "$FAKE_GH_LOG" || fail "indented quote and backticks in a list item hid the verdict: $err"
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

on() { # PARENT CMD...: run CMD on a detached checkout of PARENT, print the new HEAD, back on the lane
  git checkout -q --detach "$1"; shift; "$@" >/dev/null; git rev-parse HEAD; git checkout -q -f lane; }
pr_head() { # SHA SUBJECT: python making SHA the PR head, a commit of the PR
  echo "d['headRefOid'] = '$1'; d['commits'].append({'oid': '$1', 'messageHeadline': '$2', 'messageBody': ''})"; }
setpr; run 0 merge-ask 7 "${ST[@]}"
[[ "$(head -1 <<<"$out")" == "## Merge ask" ]] && grep -qx "Failed: none" <<<"$out" || fail "pass did not print the section: $out"
w="$(sed '/^Gate time (/,$d' <<<"$out")"   # the gate time block comes last (below)
[[ "$(tail -2 <<<"$w")" == $'Review check classes (from the verdict comment, docs/adr/0008):\n- Checks: none' ]] || fail "pass did not list the check classes: $out"
grep -q "Review verdict: $url" <<<"$out" && ! grep -q "Notes\|Summary" <<<"$out" || fail "printed more or less than the section: $out"
# quality#acceptance-qc-fallback: each row labelled with the decision source of its latest qc result at the judged head,
# never from qc.toml (which declares a demo for acceptance-a): none yet, then a report's tagged test and agent fallback.
src="Decision sources (the latest qc result at the judged head ${J:0:12}; quality spec #qc-results):"
[[ "$(grep -xF -A2 "$src" <<<"$out")" == "$src"$'\n- demo#acceptance-a: no qc result at the judged head\n- demo#acceptance-b: no qc result at the judged head' ]] \
  || fail "pass without a qc report did not say each row has no qc result: $out"
mkdir -p "$t/qc"; python3 - "$t/qc/$J-20261029T090000Z-src123.json" "$J" <<'EOF'
import json, sys; p, head = sys.argv[1:]
res = lambda i, d: {"id": i, "verdict": "pass", "evidence": "complete", "decision": d, "record": "r", "head": head}
json.dump({"head": head, "spec": "demo", "results": [res("acceptance-a", "tagged test assertions"), res("acceptance-b", "agent fallback")]}, open(p, "w"))
EOF
run 0 merge-ask 7 "${ST[@]}"
[[ "$(grep -xF -A2 "$src" <<<"$out")" == "$src"$'\n- demo#acceptance-a: tagged test assertions\n- demo#acceptance-b: agent fallback' ]] \
  || fail "pass did not label each row's decision source from the qc report: $out"
[[ "$(writes)" == "$n" ]] || fail "merge-ask wrote"
# issue-lifecycle#acceptance-merge-ask-gate-budget: the full gate's wall time on the final head (J's full run: H adds
# only qc's status commit) against gate-budget.toml at the head, flagged over the budget and grown past the share, beside
# the trend (passed full runs on the head's history: B's three; a subset run on H and a red full run on J stay out) and
# the slowest items. No gate on timing: the ask passes, or fails with the same items, as with no run recorded.
trend="$XDG_STATE_HOME/octo-feather/check-runs.jsonl"
gate_block() { sed -n '/^Gate time (/,/^$/p' <<<"$1" | sed -E 's/\(([0-9]+d)?([0-9]+h)?[0-9]+m ago\)/(AGE ago)/'; }
without() { sed '/^Gate time (/,/^$/d' <<<"$1"; }
none_out="$out"
[[ "$(gate_block "$out")" == "Gate time (the full gate on the final head against gate-budget.toml at ${H:0:12}; the code reviewer judges it, no gate reads it: issue-lifecycle #lanes-checkpoints):"$'\n'"  no gate run recorded ($trend: none)" ]] \
  || fail "no trend file: $(gate_block "$out")"
mkdir -p "$(dirname "$trend")"
run_line() { # START HEAD TOTAL EXIT TIER
  printf '{"start":"%s","repo":"%s","head":"%s","total_s":%s,"exit":%s,"tier":"%s","steps":[{"name":"tests/a.sh","seconds":%s,"result":"ok"},{"name":"tests/b.sh","seconds":20.5,"result":"ok"},{"name":"check-lint","seconds":1.0,"result":"ok"}]}\n' "$1" "$R" "$2" "$3" "$4" "$5" "$(( ${3%.*} - 30 ))" >> "$trend"; }
run_line 2026-10-01T10:00:00Z "$B" 100 0 full; run_line 2026-10-02T10:00:00Z "$B" 120 0 full; run_line 2026-10-03T10:00:00Z "$B" 110 0 full
run_line 2026-10-04T10:00:00Z "$J" 90 1 full; run_line 2026-10-04T11:00:00Z "$J" 200.5 0 full; run_line 2026-10-04T12:00:00Z "$H" 5 0 subset
run 0 merge-ask 7 "${ST[@]}"
[[ "$(gate_block "$out")" == "Gate time (the full gate on the final head against gate-budget.toml at ${H:0:12}; the code reviewer judges it, no gate reads it: issue-lifecycle #lanes-checkpoints):
  full gate: 200.5s, head ${J:0:12}, started 2026-10-04T11:00:00Z (AGE ago): OVER BUDGET by 50.5s (budget 150s)
  growth: +82.3% over the trend's median 110s (the 3 passed full runs before it); set share 25%: GROWN
  trend: 100s ${B:0:12} 2026-10-01T10:00:00Z, 120s ${B:0:12} 2026-10-02T10:00:00Z, 110s ${B:0:12} 2026-10-03T10:00:00Z, 200.5s ${J:0:12} 2026-10-04T11:00:00Z (passed full runs, oldest first)
  slowest: tests/a.sh 170s, tests/b.sh 20.5s, check-lint 1s" ]] || fail "over budget: $(gate_block "$out")"
[[ "$(without "$out")" == "$(without "$none_out")" ]] || fail "the gate time changed the merge ask: $out"
# a refusal: the same items with or without the run, the gate time on stderr only
setpr 'd["statusCheckRollup"][0]["conclusion"] = "FAILURE"'; run 1 merge-ask 7 "${ST[@]}"
[[ -z "$out" ]] && grep -qF "  full gate: 200.5s, head ${J:0:12}" <<<"$err" || fail "refusal over budget: $out $err"
over_err="$(sed -n '/merge ask incomplete/,$p' <<<"$err")"; mv "$trend" "$trend.keep"
run 1 merge-ask 7 "${ST[@]}"; [[ "$(sed -n '/merge ask incomplete/,$p' <<<"$err")" == "$over_err" ]] || fail "the gate time changed the refusal: $err"
mv "$trend.keep" "$trend"; setpr
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
# insufficient evidence (quality spec #qc-results, #acceptance-qc-insufficient) is never triaged: merge-ask fails naming
# it, from its row or from the latest qc report at the judged head, until a rerun gives it pass or fail
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | insufficient evidence | judged '"$JS"$' | r |' \
  bad "criterion row demo#acceptance-b: insufficient evidence is never triaged; rerun just qc on it until it gives pass or fail"
qcrep() { # STAMP VERDICT_OF_B: a qc report at J as octo-feather-qc writes it (spec slug, one result per criterion)
  mkdir -p "$t/qc"; python3 - "$t/qc/$J-$1-abc123.json" "$J" "$2" <<'EOF'
import json, sys; p, head, vb = sys.argv[1:]
short = {"missing": ["demo did not run to its end (exit 77, a step it needs could not run here): needs GitHub"]}
res = lambda i, v: {"id": i, "verdict": v, "evidence": "incomplete" if v == "insufficient evidence" else "complete",
                    "decision": "demo checks", "record": "r", "head": head} | (short if v == "insufficient evidence" else {})
json.dump({"head": head, "spec": "demo", "results": [res("acceptance-a", "pass"), res("acceptance-b", vb)]}, open(p, "w"))
EOF
}
qcrep 20261029T100000Z "insufficient evidence"
bad "criterion demo#acceptance-b: insufficient evidence at the judged head ${J:0:12} (demo did not run to its end (exit 77, a step it needs could not run here): needs GitHub; qc report $J-20261029T100000Z-abc123.json): never triaged"
qcrep 20261029T110000Z pass; setpr; run 0 merge-ask 7 "${ST[@]}"   # the rerun at that head gave it pass
rm -r "$t/qc"

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
for item in "PR commits: PR #16's head f5f90b85a488 is not a commit in this repo: run it in the lane worktree after git fetch origin" '`## Merge ask` section' 'Head: missing' 'Checks: missing' 'criterion table: missing' 'Review verdict: missing' 'Built: missing' 'Failed: missing'; do
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
# issue-lifecycle#acceptance-ci-status-only: qc's status-only commit H after the CI-green judged head J starts no CI full
# run (check.yml skips its check job: SKIPPED on H); the Checks item takes J's CI, naming J, and refuses when J's CI is
# missing, pending or red, or a code commit sits between them.
skipped='d["statusCheckRollup"][0]["conclusion"] = "SKIPPED"'
mkdir -p "$FAKE_GH/runs"
runs() { # SHA JSON-RUNS: the commit's check runs (REST check-runs API)
  printf '{"total_count": 1, "check_runs": %s}\n' "$2" > "$FAKE_GH/runs/$1.json"; }
skip="Checks: check skipped on head ${H:0:12} (status-only commits after ${J:0:12}: no CI full run)"
bad "$skip and ${J:0:12} has no check run" "$skipped"
runs "$J" '[{"id": 2, "name": "check", "status": "in_progress", "conclusion": null}]'
bad "$skip and pending on ${J:0:12}: check in_progress" "$skipped"
runs "$J" '[{"id": 2, "name": "check", "status": "completed", "conclusion": "failure"}]'
bad "$skip and failing on ${J:0:12}: check failure" "$skipped"
runs "$J" '[{"id": 2, "name": "check", "status": "completed", "conclusion": "skipped"}]'   # J's own run skipped (a draft PR)
bad "$skip and skipped on ${J:0:12} too: CI never ran there" "$skipped"
# the demo: J's latest check run passed (an earlier one skipped while the PR was a draft): passes, naming J
runs "$J" '[{"id": 3, "name": "check", "status": "completed", "conclusion": "success"}, {"id": 1, "name": "check", "status": "completed", "conclusion": "skipped"}]'
setpr "$skipped"; run 0 merge-ask 7 "${ST[@]}"
grep -qxF -- "- check: skipped on ${H:0:12}; success on ${J:0:12}, the head its status-only commits follow" <<<"$out" \
  || fail "a status-only head did not pass on the judged head's CI, naming it: $out"
grep -q "api repos/{owner}/{repo}/commits/$J/check-runs" "$FAKE_GH_LOG" || fail "J's check runs not read from GitHub: $(cat "$FAKE_GH_LOG")"
# a code commit C between J and the status-only head S: S's skipped check takes C's CI, none here, and Judged refuses C
C="$(on "$H" sh -c 'echo fix >> app.py; git commit -qam "fix: y"')"
S="$(on "$C" git commit -q --allow-empty -m "qc: built acceptance-a acceptance-b (judged ${J:0:12})")"
HEADL="${S:0:12}" bad "Checks: check skipped on head ${S:0:12} (status-only commits after ${C:0:12}: no CI full run) and ${C:0:12} has no check run" \
  "$skipped; $(pr_head "$C" "fix: y"); $(pr_head "$S" x)"
grep -q "Judged: commit ${C:0:12} 'fix: y' after the judged head ${J:0:12} changes app.py" <<<"$err" || fail "a code commit before the status-only head: $err"
rm -r "$FAKE_GH/runs"
ROWS="| demo#acceptance-a | pass | judged $JS | r |" bad "criterion row demo#acceptance-b: missing (it is in Built)"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | |' bad "criterion row demo#acceptance-b: no evidence"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | ok | judged '"$JS"$' | r |' bad "qc verdict 'ok'; write pass or fail"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |\n| demo#acceptance-zz | pass | judged '"$JS"$' | r |' bad "acceptance-zz: no criterion"
BUILT='demo#acceptance-a' bad "Built: lists demo#acceptance-a, the status files hold built with PR #7: demo#acceptance-a demo#acceptance-b"
# The PR's commits and their subjects come from git (BASE..head), so each case below is a real lane head.
# a Built id the status file holds but no qc: built commit names fails: qc's commit H, subject naming acceptance-a only
QA="$(on "$H" git commit -q --amend -m "qc: built acceptance-a (judged ${J:0:12})")"
HEADL="${QA:0:12}" JUDGEDL="${J:0:12} to ${QA:0:12}: qc status commits ${QA:0:12} change only docs/specs/demo.status.json" \
  bad "Built: demo#acceptance-b in no .qc: built. commit of PR #7 (they passed acceptance-a); built only by just qc" "$(pr_head "$QA" x)"
# built by an earlier qc run, reset to planned by a later one (PR #49: ac060f9, a56de61): not demanded, passes
Q1="$(on "$J" git commit -q --allow-empty -m "qc: built acceptance-a acceptance-c (judged 0123456789ab)")"
Q2="$(on "$Q1" sh -c "git checkout -q $H -- docs/specs/demo.status.json && git commit -qm 'qc: built acceptance-a acceptance-b (judged ${J:0:12})'")"
HEADL="${Q2:0:12}" JUDGEDL="${J:0:12} to ${Q2:0:12}: qc status commits ${Q1:0:12} ${Q2:0:12} change only docs/specs/demo.status.json" \
  setpr "$(pr_head "$Q2" x)"
run 0 merge-ask 7 "${ST[@]}"
QN="$(on "$H" git commit -q --amend -m "chore: status")"
HEADL="${QN:0:12}" bad "no .qc: built. commit on PR #7" "$(pr_head "$QN" x)"
REVIEW="" bad "Review verdict: empty is not a comment on PR #7"
REVIEW="https://github.com/o/r/pull/8#issuecomment-1001" bad "is not a comment on PR #7"
REVIEW="${url%1001}4242" bad "comment 4242 not on PR #7"
bad "the comment names head $OTHER, not the judged head ${J:0:12}" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Head: $J', 'Head: $OTHER')"
bad "Review verdict: blocking, not clear" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Verdict: clear', 'Verdict: blocking')"
bad "Review verdict: the comment carries no usable check classification (report classifies no check" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('\\nChecks: none\\n', '\\n')"
bad "Review verdict: clear with a proxy check (Check: scripts/x: r (ADR 1) | reads: y | class: proxy): a proxy check blocks" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Checks: none', 'Check: scripts/x: r (ADR 1) | reads: y | class: proxy')"
setpr "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Checks: none', 'Check: scripts/x: r (ADR 1) | reads: y | class: exact')"
run 0 merge-ask 7 "${ST[@]}"; w="$(sed '/^Gate time (/,$d' <<<"$out")"; [[ "$(tail -1 <<<"$w")" == "- Check: scripts/x: r (ADR 1) | reads: y | class: exact" ]] || fail "exact check not listed: $out"
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
F="$(on "$H" sh -c 'echo two >> app.py; git commit -qam "feat: after qc"')"
on "$F" "$G" record --reason "lane final head" --seconds 1 >/dev/null
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
# issue-lifecycle#acceptance-merge-ask-full-proof (rule: #lanes-checkpoints): the passes above stand on J's recorded full
# pass (H adds only qc's status commit). A head with no recorded full pass refuses, naming it and the missing pass, the
# section otherwise complete; a pass whose gate configuration is not the head's (main brought a justfile) is stale.
E="$(on "$H" sh -c 'echo e >> app.py; git commit -qam "feat: no full pass"')"
HEADL="${E:0:12}" JUDGEDL="${E:0:12} is the PR head" ROWS=$'| demo#acceptance-a | pass | judged '"${E:0:9}"$' | r |\n| demo#acceptance-b | pass | judged '"${E:0:9}"' | r |' \
  setpr "$(pr_head "$E" "feat: no full pass"); d['comments'][0]['body'] = d['comments'][0]['body'].replace('Head: $J', 'Head: $E')"
run 1 merge-ask 7 "${ST[@]}"
[[ "$err" == *"(1 item), head ${E:0:12}:"$'\n'"  - Full pass: head ${E:0:12} has no current recorded full gate pass for that head and its gate configuration; the full pass recorded at ${J:0:12} does not carry over: commit ${E:0:12} 'feat: no full pass' after the full pass ${J:0:12} changes app.py"* ]] \
  || fail "a head with no full pass: $err"
M4="$(on "$M1" sh -c 'printf "check:\n    true\n" > justfile; git add justfile; git commit -qm "main: a gate"')"; git update-ref refs/remotes/origin/main "$M4"
R5="$(on "$H" git merge -q --no-edit "$M4")"
HEADL="${R5:0:12}" bad "Full pass: head ${R5:0:12} has no current recorded full gate pass for that head and its gate configuration; the full pass recorded at ${J:0:12} does not carry over: its gate_config [0-9a-f]\{12\} is not the head's current [0-9a-f]\{12\} (octo-feather-gate config ${R5:0:12}): stale" "$(pr_head "$R5" "Merge main")"
M5="$(on "$M1" sh -c 'echo machinery > shared-machinery.txt; git add shared-machinery.txt; git commit -qm "main: a shared-machinery list"')"; git update-ref refs/remotes/origin/main "$M5"
R6="$(on "$H" git merge -q --no-edit "$M5")"   # a checkpoint: the list changed, J's pass was recorded against none
HEADL="${R6:0:12}" bad "Full pass: head ${R6:0:12} has no current recorded full gate pass for that head and its gate configuration; the full pass recorded at ${J:0:12} does not carry over: its list absent is not the head's current [0-9a-f]\{12\} (octo-feather-gate config ${R6:0:12}): stale" "$(pr_head "$R6" "Merge main")"
git update-ref refs/remotes/origin/main "$M1"
# a pass recorded on a dirty tree (an untracked file beside the gate) proves nothing
D="$(on "$H" sh -c 'echo d >> app.py; git commit -qam "feat: dirty pass"; echo x > dirt; "$0" record --reason dirty --seconds 1 >/dev/null; rm dirt' "$G")"
HEADL="${D:0:12}" JUDGEDL="${D:0:12} is the PR head" ROWS=$'| demo#acceptance-a | pass | judged '"${D:0:9}"$' | r |\n| demo#acceptance-b | pass | judged '"${D:0:9}"' | r |' \
  setpr "$(pr_head "$D" "feat: dirty pass"); d['comments'][0]['body'] = d['comments'][0]['body'].replace('Head: $J', 'Head: $D')"
run 1 merge-ask 7 "${ST[@]}"
[[ "$err" == *"(1 item), head ${D:0:12}:"$'\n'"  - Full pass: head ${D:0:12} has no current recorded full gate pass for that head and its gate configuration; the full pass recorded at ${D:0:12} does not carry over: it was recorded on a dirty tree (clean false): it proves nothing"* ]] \
  || fail "a pass recorded on a dirty tree: $err"
ROWS=$'| demo#acceptance-a | pass | judged deadbee | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |' bad "criterion row demo#acceptance-a: judged deadbee is not a commit of PR #7; name the head qc and the review judged"
ROWS=$'| demo#acceptance-a | pass | yesterday | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |' bad "judged 'yesterday'; write .judged <sha>."
python3 - "$t/pr7.keep" "$(body)" <<'PY' > "$t/old.body"
import sys; print(sys.argv[2].replace("| criterion | qc verdict | judged | evidence |", "| criterion | qc verdict | evidence |"))
PY
bad "criterion table: no judged column" "d['body'] = open('$t/old.body').read()"
# multi-spec lane: --status once per spec; a qc id outside the --status files is not demanded
QX="$(on "$H" git commit -q --allow-empty -m "qc: built acceptance-x (judged 0123456789ab)")"
HEADL="${QX:0:12}" JUDGEDL="${J:0:12} to ${QX:0:12}: qc status commits ${H:0:12} ${QX:0:12} change only docs/specs/demo.status.json" \
  setpr "$(pr_head "$QX" x)"; run 0 merge-ask 7 "${ST[@]}"
ROWS=$'| demo#acceptance-a | pass | judged '"$JS"$' | r |\n| demo#acceptance-b | pass | judged '"$JS"$' | r |\n| other#acceptance-x | pass | judged '"$JS"$' | r |' BUILT='acceptance-a acceptance-b other#acceptance-x' \
  HEADL="${QX:0:12}" JUDGEDL="${J:0:12} to ${QX:0:12}: qc status commits ${H:0:12} ${QX:0:12} change only docs/specs/demo.status.json" \
  setpr "$(pr_head "$QX" x)"
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

# a lane that builds no criterion (spec #lanes-one-head, #acceptance-merge-ask-no-criterion): PR #8, commit N
# off main, no qc commit; Built: none, Failed: none, no rows: passes on head, checks, parent line and the
# review verdict alone, --status optional; the verdict's head is the judged head
N="$(on "$B" sh -c 'sed -i 2s/.*/two/ app.py; git commit -qam "fix: a rule"')"
on "$N" "$G" record --reason "lane final head" --seconds 1 >/dev/null
pr8() { # HEAD EXTRA_COMMITS_JSON BODY [PY]
  python3 - "$FAKE_GH/pr/8.json" "$t/pr8.keep" "$1" "$2" "$3" "$check_ok" "$N" "${4:-}" <<'EOF'
import json, os, sys; p, keep, head, extra, body, checks, n, py = sys.argv[1:]
d = json.load(open(keep)) if os.path.exists(keep) else {"comments": []}
d.update(number=8, baseRefName="main", headRefName="gh6", headRefOid=head, body=body, statusCheckRollup=json.loads(checks),
         commits=[{"oid": n, "messageHeadline": "fix: a rule", "messageBody": ""}] + json.loads(extra or "[]"))
exec(py); json.dump(d, open(p, "w"))
EOF
}
nbody() { # section of a no-criterion lane, overridable: HEADL JUDGEDL TABLE BUILT FAILED
  cat <<EOF
Closes #6

## Merge ask

Head: ${HEADL-${N:0:12}}
Checks: check, ci/x pass
${JUDGEDL-}
${TABLE-}
Review verdict: ${url8-}
Built: ${BUILT-none}
${FAILED-Failed: none}
EOF
}
pr8 "$N" "" "$(nbody)"; run 0 verdict 8 "$N" "$t/report"; url8="$out"; cp "$FAKE_GH/pr/8.json" "$t/pr8.keep"   # PR #8 with its clear verdict
HDR=$'| criterion | qc verdict | judged | evidence |\n|---|---|---|---|'
for tbl in "" "$HDR"; do
  for st in "" "${ST[*]}"; do
    TABLE="$tbl" pr8 "$N" "" "$(TABLE="$tbl" nbody)"; run 0 merge-ask 8 $st
    [[ "$(head -1 <<<"$out")" == "## Merge ask" ]] && grep -qx "Built: none" <<<"$out" || fail "no-criterion lane (table '${tbl:0:5}', status '$st') did not pass: $out"
  done
done
# each item still checked: head, checks, parent line, review verdict
HEADL="${OTHER:0:12}" pr8 "$N" "" "$(HEADL="${OTHER:0:12}" nbody)"; run 1 merge-ask 8; grep -q "Head: names ${OTHER:0:12}" <<<"$err" || fail "no-criterion stale head: $err"
pr8 "$N" "" "$(nbody)" 'd["statusCheckRollup"][0]["conclusion"] = "FAILURE"'; run 1 merge-ask 8; grep -q "Checks: failing" <<<"$err" || fail "no-criterion failing check: $err"
pr8 "$N" "" "$(nbody | sed 1d)"; run 1 merge-ask 8; grep -q "parent line: missing" <<<"$err" || fail "no-criterion parent line: $err"
pr8 "$N" "" "$(nbody)" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Verdict: clear', 'Verdict: blocking')"
run 1 merge-ask 8; grep -q "Review verdict: blocking, not clear" <<<"$err" || fail "no-criterion blocking verdict: $err"
pr8 "$N" "" "$(nbody)" "d['comments'][0]['body'] = d['comments'][0]['body'].replace('\\nChecks: none\\n', '\\n')"
run 1 merge-ask 8; grep -q "carries no usable check classification" <<<"$err" || fail "no-criterion unclassified verdict: $err"
! grep -q "criterion table\|qc: built" <<<"$err" || fail "no-criterion lane asked for a table or a qc commit: $err"
# the verdict names another head: a code commit after it has no proof; a clean main merge needs its proof line
NF="$(on "$N" sh -c 'echo three >> app.py; git commit -qam "fix: more"')"
HEADL="${NF:0:12}" pr8 "$NF" "[{\"oid\": \"$NF\", \"messageHeadline\": \"fix: more\", \"messageBody\": \"\"}]" "$(HEADL="${NF:0:12}" nbody)"
run 1 merge-ask 8; grep -q "Judged: commit ${NF:0:12} 'fix: more' after the judged head ${N:0:12} changes app.py" <<<"$err" || fail "no-criterion verdict on another head passed: $err"
NM="$(on "$N" git merge -q --no-edit "$M1")"
HEADL="${NM:0:12}" pr8 "$NM" "[{\"oid\": \"$NM\", \"messageHeadline\": \"Merge main\", \"messageBody\": \"\"}]" "$(HEADL="${NM:0:12}" nbody)"
run 1 merge-ask 8; grep -q "Judged: missing; add the check's proof line .Judged: ${N:0:12} to ${NM:0:12}: no qc status commit; clean merge of main ${NM:0:12}: lane diff identical" <<<"$err" || fail "no-criterion merge without proof: $err"
proof8="$(sed -n 's/.*add the check.s proof line `Judged: \(.*\)`$/\1/p' <<<"$err")"
HEADL="${NM:0:12}" pr8 "$NM" "[{\"oid\": \"$NM\", \"messageHeadline\": \"Merge main\", \"messageBody\": \"\"}]" "$(HEADL="${NM:0:12}" JUDGEDL="Judged: $proof8" nbody)"
run 0 merge-ask 8; grep -qF "Judged: $proof8" <<<"$out" || fail "no-criterion clean merge with proof: $out"
# a lane building no criterion is checked the same: its head without a recorded full pass refuses
N2="$(on "$N" sh -c 'echo four >> app.py; git commit -qam "fix: no full pass"')"
HEADL="${N2:0:12}" pr8 "$N2" "[{\"oid\": \"$N2\", \"messageHeadline\": \"fix: no full pass\", \"messageBody\": \"\"}]" "$(HEADL="${N2:0:12}" nbody)" \
  "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Head: $N', 'Head: $N2')"
run 1 merge-ask 8; [[ "$err" == *"(1 item), head ${N2:0:12}:"$'\n'"  - Full pass: head ${N2:0:12} has no current recorded full gate pass"* ]] || fail "no-criterion lane without a full pass: $err"
# a lane that claims a criterion with no rows is still refused naming the table (#acceptance-merge-ask-evidence)
NQ="$(on "$N" git commit -q --allow-empty -m "qc: built acceptance-a (judged 0123456789ab)")"   # a qc commit on the lane
for tbl in "" "$HDR"; do
  want="criterion table: $([[ -z "$tbl" ]] && echo missing || echo 'no rows')"
  HEADL="${NQ:0:12}" pr8 "$NQ" "" "$(HEADL="${NQ:0:12}" TABLE="$tbl" nbody)"; run 1 merge-ask 8 "${ST[@]}"; grep -q "$want" <<<"$err" || fail "qc commit, no rows ('$want'): $err"
  pr8 "$N" "" "$(TABLE="$tbl" BUILT=demo#acceptance-a nbody)"; run 1 merge-ask 8 "${ST[@]}"; grep -q "$want" <<<"$err" || fail "Built id, no rows ('$want'): $err"
  pr8 "$N" "" "$(TABLE="$tbl" FAILED=$'Failed:\n- acceptance-c: repair ticket #9' nbody)"; run 1 merge-ask 8 "${ST[@]}"; grep -q "$want" <<<"$err" || fail "Failed id, no rows ('$want'): $err"
  sed 's/"planned", "pr": null/"built", "pr": 8/' docs/specs/demo.status.json > "$t/s8.json"
  pr8 "$N" "" "$(TABLE="$tbl" nbody)"; run 1 merge-ask 8 --status "$t/s8.json"; grep -q "$want" <<<"$err" || fail "status entry built with the PR, no rows ('$want'): $err"
done
pr8 "$N" "" "$(BUILT=acceptance-a nbody)"; run 1 merge-ask 8; grep -q "name the lane's status file" <<<"$err" || fail "criterion lane with no --status: $err"
# More than 100 commits: `gh pr view --json commits` lists at most 100, so the PR's commits are read from git
# (BASE..head). PR #8's head NL is the 101st commit off main; the fake gh lists only the first 100, as GitHub does.
# verdict accepts NL and merge-ask passes on it.
NL="$(on "$B" sh -c 'for i in $(seq 1 101); do echo "$i" > many.txt; git add many.txt; git commit -qm "chore: step $i"; done')"
on "$NL" "$G" record --reason "lane final head" --seconds 1 >/dev/null
CAP="$(git rev-list --reverse "$B..$NL" | head -100 | python3 -c 'import json, sys; print(json.dumps([{"oid": l.strip(), "messageHeadline": "chore", "messageBody": ""} for l in sys.stdin]))')"
export CAP
HEADL="${NL:0:12}" pr8 "$NL" "" "$(HEADL="${NL:0:12}" nbody)" "d['commits'] = json.loads(os.environ['CAP'])"
[[ "$(python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); print(len(d["commits"]), d["headRefOid"] in {c["oid"] for c in d["commits"]})' "$FAKE_GH/pr/8.json")" == "100 False" ]] \
  || fail "the 101-commit PR fixture does not cap its commits at 100 without its head"
run 0 verdict 8 "$NL" "$t/report"; grep -q "(clear, head ${NL:0:12})" <<<"$err" || fail "verdict on the 101st commit of a PR: $err"
run 0 merge-ask 8; [[ "$(head -1 <<<"$out")" == "## Merge ask" ]] || fail "merge-ask on a PR of 101 commits did not pass: $out"
unset CAP
# fields: a label of words one space apart is a field (Prior art: code-review step 4, Report fields); two spaces is not.
printf 'Checks: none\nPrior art: PyYAML 6.0.2 | license: MIT\nPrior  art: x\n' > "$t/fields"
run 0 fields "$t/fields"
python3 -c 'import json, sys; f = json.loads(sys.argv[1])["fields"]; assert f == {"Prior art": ["PyYAML 6.0.2 | license: MIT"]}, f' "$out" \
  || fail "fields: Prior art not read as one field: $out"
echo "lane-merge-ask: ok (fields reads a two-word label; verdict create, update in place, unchanged, refusals and failed writes leave no comment; merge-ask pass prints the section and each row's decision source (the latest qc result at the judged head, none without one), offline gh, PR #16 names each item, parent line (GitHub Closes #6 required, a prefix, another closing line, a closing link after it on its line or an issue URL fails; a Linear lane passes on Tracks ENG-123, fails without it or with a Closes line, own or on its line), stale head, failing/pending/no checks, rows, Built = status and named by a qc commit, read from git (built-then-reset passes), verdict link head/blocking/marker, untriaged fail, multi-spec; verdict ignores fenced and quoted lines (#144 cases), disagreeing verdicts refused; check classes: proxy posts only as blocking, missing, malformed, no owner, other class, Checks: other, none plus lines refused, merge-ask lists them and refuses an unclassified or clear-with-proxy comment; one judged head: rows on two heads, a code commit after qc, a qc commit with a non-status file, a hand status edit, a sha not in the PR and an old table fail; exact-head rerun passes; a clean main merge passes with its proof line; a main merge touching a lane file, a resolved conflict or another branch fails; a no-criterion lane passes with no table or a header, with or without --status, on its verdict's head or a proven clean merge, and fails a code commit after it or a merge without the proof line; a criterion lane (qc commit, Built or Failed id, status entry built with the PR) with no rows is refused naming the table; full pass: a head with none refuses naming it, one before qc's status commit or a clean main merge keeps it, a main merge changing the gate configuration or the shared-machinery list makes it stale, one recorded on a dirty tree refuses, a no-criterion lane alike; gate time: the final head's full run over its budget and grown past the share, with trend and slowest items, the ask passing or failing the same without it; a PR of 101 commits (gh lists 100): verdict on its head, merge-ask passes)"
