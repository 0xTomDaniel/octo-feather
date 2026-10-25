#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane judge and its line in merge-ask (spec judgment
# #acceptance-judge-advisory, #rule-advisory, issue #156), no network, no model: a fake `gh` holds PR #7 of
# o/r and logs every call; a stub `pi` runs the judge's classify extension command for real under node
# with stub classifiers at the model registry (the chosen model's id among them), in the qa sandbox, so
# it needs unprivileged user namespaces (`unshare -rm`) as tests/qa.sh does.
# Proves: `judge` refuses before the code review's verdict comment exists, an unknown question, an
# unreadable or empty state and an unavailable chosen model, writing nothing; it asks only the question's
# chosen model (its suite.json `chosen`) on the state file's text, posts one marked comment labelled a model
# judgment with the answer and its confidence, and updates it in place on rerun; merge-ask prints it
# beside the review verdict, and passes or fails exactly as without it (a blocking review still fails,
# whatever the judgment says; a malformed judgment comment changes nothing).
# Run by `just check`.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN   # a test harness: its judge runs start outside any check run
[[ "$(uname -s)" != Darwin ]] || { echo "lane-judge: skipped, not on macOS (the qa sandbox needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-judge test: $*" >&2; exit 1; }
export TMPDIR="$t/tmp"; mkdir "$TMPDIR"
export HOME="$t/home" FAKE_GH="$t/gh" FAKE_GH_LOG="$t/gh.log"
unset XDG_CONFIG_HOME XDG_STATE_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV
mkdir -p "$HOME" "$t/bin" "$FAKE_GH/pr"
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
# Fake GitHub for repo o/r: PRs in $FAKE_GH/pr/N.json; issue comments by POST, edits by PATCH.
import json, os, re, sys
a = sys.argv[1:]; D = os.environ["FAKE_GH"]
open(os.environ["FAKE_GH_LOG"], "a").write(" ".join(a) + "\n")
def die(m, rc=1): print(m, file=sys.stderr); sys.exit(rc)
def path(n): return f"{D}/pr/{n}.json"
if a[:2] == ["pr", "view"]:
    if not os.path.exists(path(a[2])): die(f"GraphQL: Could not resolve to a PullRequest with the number of {a[2]}.")
    d = json.load(open(path(a[2]))); f = a[a.index("--json") + 1].split(",")
    print(json.dumps({k: d[k] for k in f if k in d})); sys.exit(0)
if a[0] == "api":
    m, p = a[a.index("-X") + 1], a[a.index("-X") + 2].replace("{owner}/{repo}", "o/r")
    body = json.load(open(a[a.index("--input") + 1]))["body"]
    if m == "POST" and (r := re.fullmatch(r"repos/o/r/issues/(\d+)/comments", p)):
        n = r.group(1); d = json.load(open(path(n)))
        cid = 1001 + len(d["comments"])
        c = {"author": {"login": "sup"}, "body": body, "url": f"https://github.com/o/r/pull/{n}#issuecomment-{cid}"}
        d["comments"].append(c)
    elif m == "PATCH" and (r := re.fullmatch(r"repos/o/r/issues/comments/(\d+)", p)):
        n = "7"; d = json.load(open(path(n)))
        c = next((c for c in d["comments"] if c["url"].endswith(f"-{r.group(1)}")), None)
        if not c: die("gh: Not Found (HTTP 404)")
        c["body"] = body
    else: die(f"fake gh: unexpected {a}", 2)
    json.dump(d, open(path(n), "w")); print(c["url"]); sys.exit(0)
die(f"fake gh: unexpected {a}", 2)
EOF
cat > "$t/bin/pi" <<'EOF'
#!/usr/bin/env python3
# Stub pi: an extension command (-e EXT -p "/cmd args") runs for real under node with stub classifiers at the
# model registry: openrouter/respan/span-02 (test-quality's chosen model) and stub/other. Each picks the label
# after PICK= in the state at 0.87. A call to stub/other kills the run (only the chosen model may be asked); a
# state other than $STUB_WANT, when set, is refused (the state must be the file's text, unchanged). STUB_NO_CHOSEN=1
# lists only stub/other. As pi's print mode, an extension's process.stdout goes to stderr.
import subprocess, sys
a = sys.argv[1:]; prompt = a[a.index("-p") + 1]
if not (prompt.startswith("/") and "-e" in a):
    sys.exit("stub pi: only an extension command")
name, _, args = prompt[1:].partition(" ")
harness = """import {pathToFileURL} from "node:url";
const [ext, name, args] = process.argv.slice(1);
const cmds = {};
(await import(pathToFileURL(ext).href)).default({registerCommand: (n, d) => { cmds[n] = d; }});
const ids = (process.env.STUB_NO_CHOSEN ? [] : [["openrouter", "respan/span-02"]]).concat([["stub", "other"]]);
const models = ids.map(([provider, id]) => ({type: "classifier", provider, id, name: id, api: "stub", input: ["text"]}));
const modelRegistry = {
  getAvailableOfType: async (type) => (type === "classifier" ? models : []),
  classify: async (m, {state, questions}) => {
    if (m.id === "other") process.exit(5);
    if (process.env.STUB_WANT !== undefined && state !== process.env.STUB_WANT)
      return {provider: m.provider, model: m.id, answers: {}, stopReason: "error", errorMessage: "stub: state is not the file's text"};
    const answers = {};
    for (const [k, q] of Object.entries(questions)) {
      const L = Object.keys(q.criteria);
      const pick = state.split("PICK=")[1].split(/\\s/)[0];
      answers[k] = {type: "choice", choice: pick, confidence: 0.87,
                    probabilities: Object.fromEntries(L.map((l) => [l, l === pick ? 0.87 : 0.13 / (L.length - 1)]))};
    }
    return {provider: m.provider, model: m.id, answers, usage: {cost: {total: 0.001}}, stopReason: "stop"};
  },
};
process.stdout.write = process.stderr.write.bind(process.stderr);
await cmds[name].handler(args, {mode: "print", hasUI: false, modelRegistry});
"""
sys.exit(subprocess.run(["node", "--input-type=module", "-e", harness, "--", a[a.index("-e") + 1], name, args]).returncode)
EOF
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
# Fake Herdr (as tests/qa.sh's): a session's socket is a file under the config dir naming the session.
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 600;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
esac
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
[[ "${a[*]}" == "pane list" ]] && exit 0
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
chmod +x "$t/bin/gh" "$t/bin/pi" "$t/bin/herdr"; export PATH="$t/bin:$PATH"

# The lane worktree: origin/main B, the judged head J, qc's status commit H (the PR head).
R="$t/repo"; mkdir -p "$R/docs/specs"; cd "$R"
git init -q -b main .; git config user.email t@example.com; git config user.name t; git config commit.gpgsign false
status() { printf '{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {"acceptance-a": {"status": "%s", "pr": %s}}}\n' "$1" "$2" > docs/specs/demo.status.json; }
commit() { git add -A; git commit -q -m "$1"; git rev-parse HEAD; }
status planned null; seq 1 5 > app.py
B="$(commit base)"; git update-ref refs/remotes/origin/main "$B"; git checkout -q -b lane
sed -i 1s/.*/one/ app.py; J="$(commit "feat: x")"
status built 7; H="$(commit "qc: built acceptance-a (judged ${J:0:12})")"
ST=(--status docs/specs/demo.status.json)
commits="[{\"oid\": \"$J\", \"messageHeadline\": \"feat: x\", \"messageBody\": \"\"},
  {\"oid\": \"$H\", \"messageHeadline\": \"qc: built acceptance-a (judged ${J:0:12})\", \"messageBody\": \"\"}]"
printf '{"number": 7, "headRefName": "gh6", "headRefOid": "%s", "body": "", "statusCheckRollup": [{"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"}], "comments": [], "commits": %s}\n' "$H" "$commits" > "$FAKE_GH/pr/7.json"

run() { local want="$1"; shift; set +e; out="$("$L" "$@" 2>"$t/err")"; rc=$?; err="$(cat "$t/err")"; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"
  grep -q Traceback <<<"$err" && fail "'$*' printed a traceback: $err"; return 0; }
writes() { grep -c '^api' "$FAKE_GH_LOG" || true; }
judgments() { python3 -c 'import json,sys; print(sum(c["body"].startswith("<!-- octo-feather-model-judgment") for c in json.load(open(sys.argv[1]))["comments"]))' "$FAKE_GH/pr/7.json"; }
edit() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); exec(sys.argv[2]); json.dump(d,open(sys.argv[1],"w"))' "$FAKE_GH/pr/7.json" "$1"; }
printf 'Test:\ndef test_add():\n    assert add(1, 2) == add(1, 2)\nPICK=tautological\n' > "$t/state"
: > "$FAKE_GH_LOG"

# --- refusals before any classify call or write ---
run 1 judge 7 test-quality --state "$t/state"
grep -q "no code review verdict comment on PR #7: the judge answers beside the review; post it first with .octo-feather-lane verdict 7" <<<"$err" || fail "no verdict: $err"
printf 'Checks: none\nVerdict: clear\n' > "$t/report"
run 0 verdict 7 "${J:0:7}" "$t/report"; url="$out"
n="$(writes)"
run 1 judge 7 vibes --state "$t/state"
grep -q "no judgment question 'vibes': name one of call-evidence, exact-or-proxy, test-quality, ticket-slice (evals/judgment-<question>/)" <<<"$err" || fail "unknown question: $err"
run 1 judge 7 test-quality --state "$t/nope"; grep -q "cannot read state $t/nope" <<<"$err" || fail "missing state: $err"
: > "$t/empty"; run 1 judge 7 test-quality --state "$t/empty"; grep -q "state $t/empty is empty" <<<"$err" || fail "empty state: $err"
run 1 judge 7 test-quality; grep -q "usage: octo-feather-lane judge PR QUESTION --state FILE" <<<"$err" || fail "usage: $err"
STUB_NO_CHOSEN=1 run 1 judge 7 test-quality --state "$t/state"
grep -q "chosen model openrouter/respan/span-02 is not an available classifier (available: stub/other)" <<<"$err" || fail "chosen unavailable: $err"
[[ "$(writes)" == "$n" ]] || fail "a refusal wrote"

# --- the merge ask, ready without any judgment ---
cat > "$t/body" <<EOF
Closes #6

## Merge ask

Head: ${H:0:12}
Checks: check pass on ${H:0:12}
Judged: ${J:0:12} to ${H:0:12}: qc status commits ${H:0:12} change only docs/specs/demo.status.json
| criterion | qc verdict | judged | evidence |
|---|---|---|---|
| demo#acceptance-a | pass | judged ${J:0:9} | qc report, cmd ok |
Review verdict: $url
Built: demo#acceptance-a
Failed: none
EOF
edit "d['body'] = open('$t/body').read()"
run 0 merge-ask 7 "${ST[@]}"; without="$out"
grep -qi "model judgment" <<<"$without" && fail "a judgment shown with none posted: $without"

# --- judge: the chosen model alone answers the state file's text; one labelled comment ---
STUB_WANT="$(cat "$t/state"; echo .)"; STUB_WANT="${STUB_WANT%.}"; export STUB_WANT   # the text, its trailing newline kept
run 0 judge 7 test-quality --state "$t/state"
[[ "$out" == "https://github.com/o/r/pull/7#issuecomment-1002" ]] || fail "judge printed $out"
grep -q "judge: created (test-quality: tautological, confidence 0.870, model judgment by openrouter/respan/span-02)" <<<"$err" || fail "judge said: $err"
python3 - "$FAKE_GH/pr/7.json" "$H" "$J" <<'EOF' || fail "judgment comment body: $(cat "$FAKE_GH/pr/7.json")"
import json, sys; b = json.load(open(sys.argv[1]))["comments"][1]["body"]
for want in ("<!-- octo-feather-model-judgment: test-quality -->\n", "\nJudgment: model judgment", "\nQuestion: test-quality\n",
             "\nModel: openrouter/respan/span-02\n", "\nAnswer: tautological\n", "\nConfidence: 0.870\n",
             f"\nPR head: {sys.argv[2]}\n", f"\nReview head: {sys.argv[3]}\n", "assert add(1, 2) == add(1, 2)"):
    assert want in b, (want, b)
EOF
[[ "$(writes)" == "$((n + 1))" ]] || fail "judge wrote $(( $(writes) - n )) times"

# --- merge-ask shows it beside the review verdict; ready the same ---
run 0 merge-ask 7 "${ST[@]}"; with="$out"
line="- test-quality: tautological, confidence 0.870 (model judgment by openrouter/respan/span-02, advisory: no gate reads it; PR head ${H:0:12}, review head ${J:0:12}): https://github.com/o/r/pull/7#issuecomment-1002"
grep -qxF -- "$line" <<<"$with" || fail "merge-ask did not show the judgment: $with"
python3 - "$with" "$without" "$line" <<'EOF' || fail "judgment not beside the review, or more changed: $with"
import sys; w, wo, line = sys.argv[1:]; ls = w.split("\n"); r = ls.index(line) - 1
assert ls[r] == "Model judgments (advisory, spec judgment#rule-advisory: no gate reads them; this merge ask is ready or not without them):", ls[r]
assert ls[r - 1] == "" and ls[r - 2].startswith("Failed:") and ls[r + 2] == "" and ls[r + 3].startswith("Review check classes"), ls
assert "\n".join(ls[:r - 1] + ls[r + 2:]) == wo, (w, wo)
EOF

# --- rerun: updated in place, one judgment comment ---
printf 'Test:\ndef test_add():\n    assert add(1, 2) == 3\nPICK=ok\n' > "$t/state2"
STUB_WANT="$(cat "$t/state2"; echo .)"; STUB_WANT="${STUB_WANT%.}"
run 1 judge 7 test-quality --state "$t/state"; grep -q "openrouter/respan/span-02 gave no answer (stub: state is not the file's text)" <<<"$err" || fail "stub state check: $err"
run 0 judge 7 test-quality --state "$t/state2"
[[ "$out" == "https://github.com/o/r/pull/7#issuecomment-1002" && "$(judgments)" == 1 ]] || fail "rerun not in place: $out, $(judgments)"
grep -q '^api -X PATCH repos/{owner}/{repo}/issues/comments/1002 ' "$FAKE_GH_LOG" || fail "no PATCH of 1002: $(cat "$FAKE_GH_LOG")"
run 0 merge-ask 7 "${ST[@]}"; grep -q "^- test-quality: ok, confidence 0.870 (model judgment" <<<"$out" || fail "updated judgment not shown: $out"

# --- no gate reads it: merge-ask's verdict is the same with and without, whatever it says ---
edit "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Verdict: clear', 'Verdict: blocking')"
run 1 merge-ask 7 "${ST[@]}"; with_err="$err"
keep="$(cat "$FAKE_GH/pr/7.json")"
edit "d['comments'] = d['comments'][:1]"
run 1 merge-ask 7 "${ST[@]}"; [[ "$err" == "$with_err" ]] || fail "a blocking review failed differently with the judgment: $with_err / $err"
printf '%s' "$keep" > "$FAKE_GH/pr/7.json"
edit "d['comments'][0]['body'] = d['comments'][0]['body'].replace('Verdict: blocking', 'Verdict: clear')"
edit "d['comments'][1]['body'] = '<!-- octo-feather-model-judgment: test-quality -->\ngarbage'"
run 0 merge-ask 7 "${ST[@]}"; grep -q "^- test-quality: unreadable judgment comment" <<<"$out" || fail "malformed judgment: $out"
echo "lane-judge: ok (refusals before a verdict comment, unknown question, missing or empty state, chosen model unavailable: no write; the chosen model alone answers the state file's text; one comment labelled model judgment with answer and confidence, updated in place; merge-ask shows it beside the review verdict and passes or fails the same without it; a malformed judgment comment changes nothing)"
