#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane ci-start (criterion below; the rule: issue-lifecycle #lanes-one-head),
# no network: a fake `gh` holds draft PR #7 of o/r and GitHub's workflow runs and jobs on its head (REST). ci-start
# refuses an unpushed head and a head with no recorded full gate pass before marking the PR ready; else marks it
# ready and succeeds only once CI's full run has started, as the head's workflow file and the run's jobs show.
# Run by `just check`.
# criterion: issue-lifecycle#acceptance-ci-alongside
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-ci-start test: $*" >&2; exit 1; }
export HOME="$t/home" FAKE_GH="$t/gh" FAKE_GH_LOG="$t/gh.log" XDG_STATE_HOME="$t/xdg"
unset HERDR_SESSION
mkdir -p "$HOME" "$t/bin" "$FAKE_GH/runs" "$FAKE_GH/jobs"
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
# Fake GitHub for o/r PR #7 ($FAKE_GH/pr.json). Workflow runs on a commit: $FAKE_GH/runs/<sha>.json; a run's jobs:
# $FAKE_GH/jobs/<id>.json, replaced by jobs/<id>.json.next once read (the run moving on while ci-start waits).
import json, os, re, sys
a = sys.argv[1:]; D = os.environ["FAKE_GH"]; P = f"{D}/pr.json"
open(os.environ["FAKE_GH_LOG"], "a").write(" ".join(a) + "\n")
d = json.load(open(P))
if a[:3] == ["pr", "view", "7"]:
    f = a[a.index("--json") + 1].split(","); print(json.dumps({k: d[k] for k in f})); sys.exit(0)
if a[:3] == ["pr", "ready", "7"]:
    d["isDraft"] = False; json.dump(d, open(P, "w")); print('✓ Pull request o/r#7 is marked as "ready for review"'); sys.exit(0)
api = r"repos/(?:\{owner\}/\{repo\}|o/r)/actions/"
if a[0] == "api" and (r := re.fullmatch(api + r"runs\?head_sha=([0-9a-f]+)&per_page=100", a[1])):
    p = f"{D}/runs/{r.group(1)}.json"
    print(open(p).read() if os.path.exists(p) else '{"total_count": 0, "workflow_runs": []}'); sys.exit(0)
if a[0] == "api" and (r := re.fullmatch(api + r"runs/([0-9]+)/jobs\?per_page=100", a[1])):
    p = f"{D}/jobs/{r.group(1)}.json"; print(open(p).read())
    if os.path.exists(p + ".next"): os.replace(p + ".next", p)
    sys.exit(0)
print(f"fake gh: unexpected {a}", file=sys.stderr); sys.exit(2)
EOF
chmod +x "$t/bin/gh"; export PATH="$t/bin:$PATH"

# The lane worktree: origin/main B, the lane's final head H; its workflow: a scope job, then check needing it.
R="$t/repo"; mkdir -p "$R/.github/workflows"; cd "$R"
git init -q -b main .; git config user.email t@example.com; git config user.name t; git config commit.gpgsign false
printf 'on: pull_request\njobs:\n  scope:\n    runs-on: x\n  check:\n    needs: scope\n    runs-on: x\n' > .github/workflows/ci.yml
echo one > app.py; git add -A; git commit -qm base; git update-ref refs/remotes/origin/main HEAD
git checkout -q -b gh6; echo two >> app.py; git commit -qam "feat: x"; H="$(git rev-parse HEAD)"
pr() { # HEAD DRAFT
  printf '{"number": 7, "isDraft": %s, "headRefOid": "%s", "baseRefName": "main", "headRefName": "gh6"}\n' "$2" "$1" > "$FAKE_GH/pr.json"
  rm -f "$FAKE_GH/runs/"* "$FAKE_GH/jobs/"*; : > "$FAKE_GH_LOG"; }
wf() { # SHA: the head's latest run 2 of the workflow, beside an earlier run 1 the draft skipped
  printf '{"total_count": 2, "workflow_runs": [{"id": 2, "workflow_id": 5, "path": ".github/workflows/ci.yml"}, {"id": 1, "workflow_id": 5, "path": ".github/workflows/ci.yml"}]}\n' > "$FAKE_GH/runs/$1.json"
  echo '{"total_count": 2, "jobs": [{"name": "scope", "status": "completed", "conclusion": "skipped", "html_url": "u1"}, {"name": "check", "status": "completed", "conclusion": "skipped", "html_url": "u1"}]}' > "$FAKE_GH/jobs/1.json"; }
jobs() { # FILE SCOPE_STATUS SCOPE_CONCLUSION [CHECK_STATUS CHECK_CONCLUSION]: run 2's jobs as GitHub lists them
  python3 - "$FAKE_GH/jobs/2.$1" "$2" "$3" "${4:-}" "${5:-}" <<'PY'
import json, sys; p, ss, sc, cs, cc = sys.argv[1:]
j = [{"name": "scope", "status": ss, "conclusion": sc or None, "html_url": "https://github.com/o/r/actions/runs/2/job/1"}]
j += [{"name": "check", "status": cs, "conclusion": cc or None, "html_url": "https://github.com/o/r/actions/runs/2/job/2"}] if cs else []
json.dump({"total_count": len(j), "jobs": j}, open(p, "w"))
PY
}
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
# The demo. The final head, a draft: marked ready. Its run's scope job runs and check is not created yet (GitHub
# creates a job waiting on needs once they finish): ci-start keeps waiting; then check is queued: started, printed.
pr "$H" true; wf "$H"; jobs json in_progress ""; jobs json.next completed success queued ""
run 0 ci-start 7 --wait 30
grep -q '^pr ready 7$' "$FAKE_GH_LOG" || fail "not marked ready: $(cat "$FAKE_GH_LOG")"
[[ "$(grep -c 'actions/runs/2/jobs' "$FAKE_GH_LOG")" == 2 ]] || fail "did not wait past scope running: $(cat "$FAKE_GH_LOG")"
[[ "$out" == *"- scope success on ${H:0:12}: https://github.com/o/r/actions/runs/2/job/1"$'\n'"- check queued on ${H:0:12}: https://github.com/o/r/actions/runs/2/job/2" ]] \
  || fail "the started run not printed: $out"
# Already ready (a fix round): no ready call; scope done, check running: started.
pr "$H" false; wf "$H"; jobs json completed success in_progress ""
run 0 ci-start 7; unready "a ready PR"
grep -qxF -- "- check in_progress on ${H:0:12}: https://github.com/o/r/actions/runs/2/job/2" <<<"$out" || fail "ready PR: $out"
# Not started within --wait, each refused naming why: scope running with check not created, or with check pending;
# check skipped (a status-only head); no run at all.
pr "$H" false; wf "$H"; jobs json in_progress ""
run 1 ci-start 7 --wait 1
grep -qF "CI's full run did not start on ${H:0:12} within 1s: run 2 lists 1 of the 2 jobs .github/workflows/ci.yml defines" <<<"$err" || fail "scope running, check absent: $err"
jobs json in_progress "" pending ""
run 1 ci-start 7 --wait 1; grep -qF "within 1s: run 2 job check pending" <<<"$err" || fail "check pending: $err"
jobs json completed success completed skipped
run 1 ci-start 7 --wait 1; grep -qF "within 1s: run 2 job check skipped" <<<"$err" || fail "check skipped: $err"
pr "$H" true
run 1 ci-start 7 --wait 1; grep -qF "within 1s: no workflow run on it yet" <<<"$err" || fail "no run: $err"
echo "lane-ci-start: ok (unpushed head and no full pass refused before ready; draft marked ready, waits past scope running until check is queued, prints the jobs; a ready PR's running check printed; scope running with check absent or pending, check skipped, no run: refused within --wait)"
