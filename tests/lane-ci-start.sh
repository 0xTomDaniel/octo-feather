#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane ci-start (spec issue-lifecycle #acceptance-ci-alongside; the rule: #lanes-one-head),
# no network: a fake `gh` holds draft PR #7 of o/r; `gh pr ready` makes it ready and GitHub's check run on its head
# appear queued (unless FAKE_GH_NO_RUN). ci-start refuses a local head that is not the PR head and a head with no
# recorded full gate pass, each before marking the PR ready; else marks it ready, waits for the check run on that head
# and prints it; refuses when none but a skipped one appears within --wait. Run by `just check`.
# criterion: issue-lifecycle#acceptance-ci-alongside
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-ci-start test: $*" >&2; exit 1; }
export HOME="$t/home" FAKE_GH="$t/gh" FAKE_GH_LOG="$t/gh.log" XDG_STATE_HOME="$t/xdg"
unset HERDR_SESSION
mkdir -p "$HOME" "$t/bin" "$FAKE_GH/runs"
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
# Fake GitHub for o/r PR #7 ($FAKE_GH/pr.json); check runs per commit in $FAKE_GH/runs/<sha>.json.
import json, os, re, sys
a = sys.argv[1:]; D = os.environ["FAKE_GH"]; P = f"{D}/pr.json"
open(os.environ["FAKE_GH_LOG"], "a").write(" ".join(a) + "\n")
d = json.load(open(P))
if a[:3] == ["pr", "view", "7"]:
    f = a[a.index("--json") + 1].split(","); print(json.dumps({k: d[k] for k in f})); sys.exit(0)
if a[:3] == ["pr", "ready", "7"]:
    d["isDraft"] = False; json.dump(d, open(P, "w"))
    if not os.environ.get("FAKE_GH_NO_RUN"):
        json.dump({"total_count": 1, "check_runs": [{"id": 9, "name": "check", "status": "queued", "conclusion": None,
                   "html_url": "https://github.com/o/r/actions/runs/1/job/9"}]}, open(f"{D}/runs/{d['headRefOid']}.json", "w"))
    print('✓ Pull request o/r#7 is marked as "ready for review"'); sys.exit(0)
if a[0] == "api" and (r := re.fullmatch(r"repos/(?:\{owner\}/\{repo\}|o/r)/commits/([0-9a-f]+)/check-runs(\?.*)?", a[1])):
    p = f"{D}/runs/{r.group(1)}.json"
    print(open(p).read() if os.path.exists(p) else '{"total_count": 0, "check_runs": []}'); sys.exit(0)
print(f"fake gh: unexpected {a}", file=sys.stderr); sys.exit(2)
EOF
chmod +x "$t/bin/gh"; export PATH="$t/bin:$PATH"

# The lane worktree: origin/main B, the lane's final head H.
R="$t/repo"; mkdir -p "$R"; cd "$R"
git init -q -b main .; git config user.email t@example.com; git config user.name t; git config commit.gpgsign false
echo one > app.py; git add -A; git commit -qm base; git update-ref refs/remotes/origin/main HEAD
git checkout -q -b gh6; echo two >> app.py; git commit -qam "feat: x"; H="$(git rev-parse HEAD)"
pr() { # HEAD DRAFT
  printf '{"number": 7, "isDraft": %s, "headRefOid": "%s", "baseRefName": "main", "headRefName": "gh6"}\n' "$2" "$1" > "$FAKE_GH/pr.json"
  rm -f "$FAKE_GH/runs/"*; : > "$FAKE_GH_LOG"; }
run() { local want="$1"; shift; set +e; out="$("$L" "$@" 2>"$t/err")"; rc=$?; err="$(cat "$t/err")"; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"
  grep -q Traceback <<<"$err" && fail "'$*' printed a traceback: $err"; return 0; }
unready() { ! grep -q '^pr ready' "$FAKE_GH_LOG" || fail "$1 marked the PR ready: $(cat "$FAKE_GH_LOG")"; }

# The local head is not the PR's head (not pushed): refused, the PR left a draft.
pr "$(git rev-parse HEAD~1)" true
run 1 ci-start 7; grep -q "local HEAD ${H:0:12} is not PR #7's head $(git rev-parse --short=12 HEAD~1): push it" <<<"$err" || fail "unpushed head: $err"
unready "an unpushed head"
# No recorded full gate pass on the head: refused, the PR left a draft.
pr "$H" true
run 1 ci-start 7; grep -q "head ${H:0:12} has no current recorded full gate pass" <<<"$err" || fail "no full pass: $err"
unready "a head with no full pass"
"$kit/scripts/octo-feather-gate" record --reason "lane final head" --seconds 1 >/dev/null   # H's full gate pass
# The final head: marked ready, CI's check run on it shown started.
pr "$H" true
run 0 ci-start 7
grep -q '^pr ready 7$' "$FAKE_GH_LOG" || fail "not marked ready: $(cat "$FAKE_GH_LOG")"
grep -qxF -- "- check queued on ${H:0:12}: https://github.com/o/r/actions/runs/1/job/9" <<<"$out" || fail "the started run not printed: $out"
# Already ready (a fix round): no ready call, the run on the new head printed.
pr "$H" false
printf '{"total_count": 1, "check_runs": [{"id": 4, "name": "check", "status": "in_progress", "conclusion": null, "html_url": "u"}]}\n' > "$FAKE_GH/runs/$H.json"
run 0 ci-start 7; unready "a ready PR"; grep -qxF -- "- check in_progress on ${H:0:12}: u" <<<"$out" || fail "ready PR: $out"
# No run but the draft's skipped one appears within --wait: refused naming it.
pr "$H" true
printf '{"total_count": 1, "check_runs": [{"id": 3, "name": "check", "status": "completed", "conclusion": "skipped", "html_url": "u"}]}\n' > "$FAKE_GH/runs/$H.json"
FAKE_GH_NO_RUN=1 run 1 ci-start 7 --wait 1
grep -q "no CI check run started on ${H:0:12} within 1s (GitHub shows: check skipped)" <<<"$err" || fail "no run: $err"
echo "lane-ci-start: ok (unpushed head and no full pass refused before ready; draft marked ready and its queued run printed; a ready PR's run printed; only a skipped run within --wait refused)"
