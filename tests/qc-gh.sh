#!/usr/bin/env bash
# Integration test for the qc judge's GitHub evidence (#34), no network and no model:
# a fake `gh` outside the sandbox stands in for GitHub (the caller's auth is GH_TOKEN),
# octo-feather-qc-ghsnap snapshots it before every run, and a fake `pi` judge inside the
# sandbox reads it through the offline gh (scripts/qc-bin/gh): issue view, pr view --json,
# api GET answer; issue comment and api -X POST are refused, counted in the cleanup line
# and the report. Also: the brief names the evidence, the snapshot is read-only inside,
# refetched per run and removed after; no GitHub remote skips cleanly; a failed fetch
# aborts before the judge (67) unless --no-github; PR 0 is refused before the judge; a
# failed status commit leaves the status file unmodified. Run by `just check`.
set -euo pipefail
# The qc sandbox is Linux-only (unshare, /proc); CI runs this on Linux.
[[ "$(uname -s)" != Darwin ]] || { echo "qc-gh: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
Q="$kit/scripts/octo-feather-qc"; S="$kit/scripts/octo-feather-spec-status"
t="$(mktemp -d)"
trap 'chmod -R u+w "$t"; rm -rf "$t"' EXIT
fail() { echo "qc-gh test: $*" >&2; exit 1; }
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
export HOME="$t/home" OCTO_FEATHER_QC_DIR="$t/reports" GH_TOKEN=SECRET-token FAKE_GH_LOG="$t/gh.log"
unset XDG_CONFIG_HOME XDG_STATE_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION OCTO_FEATHER_PARENT HERDR_PANE_ID HERDR_TAB_ID HERDR_WORKSPACE_ID
mkdir -p "$HOME" "$t/bin" "$t/repo/docs/specs"
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
# Fake GitHub for repo o/r: needs GH_TOKEN (the caller's auth); FAKE_GH_DOWN=1 is a network failure.
import json, os, sys
a = sys.argv[1:]
open(os.environ["FAKE_GH_LOG"], "a").write(" ".join(a) + "\n")
if os.environ.get("FAKE_GH_DOWN"): sys.exit(print("error connecting to api.github.com", file=sys.stderr) or 1)
if not os.environ.get("GH_TOKEN"): sys.exit(print("To get started with GitHub CLI, please run:  gh auth login", file=sys.stderr) or 4)
u = lambda l: {"login": l}
iss = {1: {"number": 1, "title": "Evidence issue", "state": "OPEN", "updatedAt": "2026-10-19T10:00:00Z", "author": u("a"), "labels": [], "comments": [{"author": u("b"), "body": "a comment", "createdAt": "x"}], "url": "u1", "body": "b"},
       3: {"number": 3, "title": "Closed one", "state": "CLOSED", "updatedAt": "2026-10-18T10:00:00Z", "author": u("a"), "labels": [], "comments": [], "url": "u3", "body": ""}}
prs = {2: {"number": 2, "title": "Draft PR", "state": "OPEN", "isDraft": True, "headRefName": "gh1", "headRefOid": "abc123", "baseRefName": "main",
           "updatedAt": "2026-10-19T11:00:00Z", "author": u("a"), "labels": [], "url": "u2", "body": "", "reviews": [], "commits": [], "files": []}}
def out(x): print(json.dumps(x)); sys.exit(0)
def pick(d, i):
    f = a[a.index("--json") + 1].split(","); return {k: d[k] for k in f if k in d}
c = a[:2]
if c == ["repo", "view"]: out({"nameWithOwner": "o/r", "name": "r", "owner": u("o"), "defaultBranchRef": {"name": "main"}})
if c == ["issue", "list"]: out([pick(d, 0) for d in iss.values()])
if c == ["pr", "list"]: out([pick(d, 0) for d in prs.values()])
if c == ["run", "list"]: out([{"databaseId": 7, "status": "completed", "conclusion": "success", "displayTitle": "check", "workflowName": "check", "headBranch": "gh1", "event": "push", "createdAt": "x"}])
if c == ["issue", "view"]: out(pick(iss[int(a[2])], 0))
if c == ["pr", "view"]: out(pick(prs[int(a[2])], 0))
if c == ["pr", "diff"]: print("diff --git a/x b/x"); sys.exit(0)
if a[0] == "api":
    p = a[-1]
    if p.endswith("/branches"): out([[{"name": "main", "commit": {"sha": "abc123"}}]])
    if p.endswith("/timeline"): out([[{"event": "labeled"}, {"event": "commented"}]])
    if "dependencies" in p or "sub_issues" in p: sys.exit(print("gh: Not Found (HTTP 404)", file=sys.stderr) or 1)
    out([{"ok": p}])
sys.exit(print(f"fake gh: unexpected {a}", file=sys.stderr) or 2)
EOF
cat > "$t/bin/pi" <<'EOF'
#!/usr/bin/env bash
# Fake judge: reads GitHub evidence through whatever `gh` the sandbox gives it, then tries two writes.
[[ "${1:-}" == --version ]] && exit 0
brief="${*: -1}"
echo "gh is $(command -v gh)"
grep -q 'history only:' <<< "$brief" && grep -q "GitHub: ${FAKE_BRIEF:-x}" <<< "$brief" && echo "BRIEF ok"
gh issue view 1 --json title,state -q '.title + " " + .state' 2>&1 | sed 's/^/R1 /'
gh pr view 2 --json isDraft,title 2>&1 | tr -d '\n ' | sed 's/^/R2 /'; echo
gh api repos/o/r/issues/1/timeline -q length 2>&1 | sed 's/^/R3 /'
gh issue comment 1 -b hacked 2>&1 | sed 's/^/W1 /'
gh api -X POST repos/o/r/issues -f title=x 2>&1 | sed 's/^/W2 /'
if [[ -n "${OCTO_FEATHER_GHSNAP:-}" ]]; then
  chmod -R u+w "$OCTO_FEATHER_GHSNAP" 2>/dev/null; touch "$OCTO_FEATHER_GHSNAP/x" 2>/dev/null && echo "ESCAPE snapshot writable"
  echo hacked 2>/dev/null > "$OCTO_FEATHER_GHSNAP/issue/1.json" && echo "ESCAPE snapshot item writable"
fi
printf '```json\n{"head": "x", "criteria": [{"id": "acceptance-a", "verdict": "pass", "command": "gh issue view 1", "output": "ok", "why": "history only: shown"}]}\n```\n'
EOF
chmod +x "$t/bin/gh" "$t/bin/pi"; export PATH="$t/bin:$kit/scripts:$PATH"
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$t/repo/docs/specs/"
cd "$t/repo"; git init -q -b main .
"$S" init docs/specs/demo.spec.html 0123abc >/dev/null; git add -A; git commit -qm spec
git remote add origin https://github.com/o/r.git   # never contacted: only the fake gh is
st=docs/specs/demo.status.json
run() { local want="$1"; shift; set +e; out="$("$Q" "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out"; }
report() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))'"$1"')' "$(ls -t "$t"/reports/*.json | head -1)"; }
judged() { report '["stdout"]'; }
reset() { git reset -q --hard "$base"; }
base="$(git rev-parse HEAD)"

# PR 0 (and a non-number) refused before the judge or any fetch; status untouched.
for pr in 0 -3 x 07; do
  run 64 "$st" "$pr" acceptance-a
  grep -q "PR must be a positive integer" <<< "$out" || fail "PR $pr: $out"
done
[[ ! -e "$t/gh.log" && ! -e "$t/reports" && "$(git rev-parse HEAD)" == "$base" && -z "$(git status --porcelain)" ]] \
  || fail "a refused PR fetched, judged or touched the status file"
run 64 "$st" 5 acceptance-a acceptance-a; grep -q "ids given twice" <<< "$out" || fail "duplicate id: $out"

# A GitHub repo: fetched outside, read-only inside, reads answered, writes refused and counted.
FAKE_BRIEF='`gh` is an offline, read-only snapshot of o/r' run 0 "$st" 5 acceptance-a
grep -q "qc sandbox: ok   github: snapshot of o/r at .*issues 2, prs 1, runs 1, branches 1, full views 3; read-only, served by the offline gh ($kit/scripts/qc-bin/gh)" <<< "$out" \
  || fail "no github proof line: $out"
j="$(judged)"
grep -q "gh is $kit/scripts/qc-bin/gh" <<< "$j" || fail "judge's gh is not the offline gh: $j"
grep -q "BRIEF ok" <<< "$j" || fail "brief does not name the GitHub evidence and the history-only rule"
grep -q "R1 Evidence issue OPEN" <<< "$j" || fail "gh issue view: $j"
grep -q 'R2 {"isDraft":true,"title":"DraftPR"}' <<< "$j" || fail "gh pr view --json: $j"
grep -q "R3 2" <<< "$j" || fail "gh api GET: $j"
grep -q "W1 gh (offline read-only snapshot.*not in the read-only snapshot.*no writes" <<< "$j" || fail "gh issue comment not refused: $j"
grep -q "W2 gh (offline read-only snapshot.*write refused" <<< "$j" || fail "gh api -X POST not refused: $j"
grep -q ESCAPE <<< "$j" && fail "snapshot writable inside the sandbox: $j"
grep -q "offline gh refusals 2" <<< "$out" || fail "refusals not in the cleanup or summary line: $out"
[[ "$(report '["gh_misses"]')" == 2 && "$(report '["github"]["repo"]')" == o/r && "$(report '["github"]["snapshot"]["counts"]["issues"]')" == 2 ]] \
  || fail "report github record: $(report '["github"]') misses $(report '["gh_misses"]')"
! grep -q 'issue comment\|POST' "$t/gh.log" || fail "a judge write reached the real gh"
compgen -G "${TMPDIR:-/tmp}/qc-ghsnap-$(report '["run_id"]')-*" > /dev/null && fail "snapshot scratch left after the run"
reset

# Refetched per run.
run 0 "$st" 5 acceptance-a
[[ "$(grep -c '^repo view' "$t/gh.log")" == 2 ]] || fail "snapshot not refetched per run: $(cat "$t/gh.log")"
reset

# Fetch failure aborts before the judge; --no-github skips it, printed.
FAKE_GH_DOWN=1 run 67 "$st" 5 acceptance-a
grep -q "GitHub snapshot of o/r failed; judge not started.*--no-github.*error connecting" <<< "$out" || fail "fetch failure: $out"
grep -q "qc sandbox:" <<< "$out" && fail "sandbox started after a failed fetch: $out"
[[ "$(git rev-parse HEAD)" == "$base" && -z "$(git status --porcelain)" ]] || fail "failed fetch touched the status file"
(unset GH_TOKEN; run 67 "$st" 5 acceptance-a; grep -q "gh auth login" <<< "$out") || fail "no-auth fetch did not abort"
FAKE_GH_DOWN=1 run 0 "$st" 5 acceptance-a --no-github
grep -q "qc sandbox: ok   github: SKIPPED (--no-github; o/r not fetched" <<< "$out" || fail "--no-github not in the proof: $out"
grep -q "R1 gh (offline .*): github: SKIPPED" <<< "$(judged)" || fail "--no-github: gh did not refuse: $(judged)"
reset

# No GitHub remote: no fetch, the proof says so, the offline gh refuses every call; the run continues.
git remote remove origin; : > "$t/gh.log"
run 0 "$st" 5 acceptance-a
grep -q "qc sandbox: ok   github: none (no GitHub remote); the offline gh refuses every call (exit 1)" <<< "$out" || fail "no-remote proof: $out"
[[ ! -s "$t/gh.log" ]] || fail "no-remote run called gh: $(cat "$t/gh.log")"
grep -q "R1 gh (offline .*): github: none (no GitHub remote)" <<< "$(judged)" || fail "no-remote gh did not refuse: $(judged)"
grep -q "offline gh refusals 5" <<< "$out" || fail "no-remote refusals not counted: $out"
reset

# The status commit fails after the judge ran: exit 3, status file restored, nothing uncommitted.
mkdir -p "$t/hooks"; printf '#!/bin/sh\nexit 1\n' > "$t/hooks/pre-commit"; chmod +x "$t/hooks/pre-commit"
git config core.hooksPath "$t/hooks"
run 3 "$st" 5 acceptance-a
git config --unset core.hooksPath
grep -q "status commit failed" <<< "$out" || fail "failed commit not reported: $out"
[[ "$(git rev-parse HEAD)" == "$base" && -z "$(git status --porcelain)" ]] || fail "status file left modified: $(git status --porcelain)"
# Snapshot misses on --json: an absent field is refused, logged and counted; a stored null is returned.
sn="$t/snap"; mkdir -p "$sn/pr"
echo '{"repo": "o/r", "fetched_at": "x", "counts": {}, "capped": []}' > "$sn/meta.json"
echo '[{"databaseId": 7, "status": "in_progress", "conclusion": null, "headBranch": "gh1"}]' > "$sn/run-list.json"
pr2='{"number": 2, "title": "T", "state": "OPEN", "headRefName": "gh1", "baseRefName": "main", "mergedAt": null, "author": {"login": "a"}, "updatedAt": "x"}'
echo "$pr2" > "$sn/pr/2.json"; echo "[$pr2]" > "$sn/pr-list.json"
echo '[{"number": 1, "title": "I", "state": "OPEN", "updatedAt": "x"}]' > "$sn/issue-list.json"
echo '{"nameWithOwner": "o/r"}' > "$sn/repo.json"
shim() { local want="$1"; shift; set +e; out="$(OCTO_FEATHER_GHSNAP="$sn" OCTO_FEATHER_GHSNAP_MISS="$t/miss.log" "$kit/scripts/qc-bin/gh" "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "offline gh $* want exit $want, got $rc: $out"; }
rm -f "$t/miss.log"; n=0
for c in "run view 7 --json jobs" "run view 7 --json conclusion,jobs" "pr view 2 --json title,reviews" "pr list --json number,reviews" \
         "issue list --json number,labels" "run list --json databaseId,jobs" "repo view --json nameWithOwner,description"; do
  shim 1 $c; n=$((n + 1))
  grep -q "not in snapshot: ${c##*[, ]} " <<< "$out" || fail "gh $c: no 'not in snapshot' refusal: $out"
  grep -q null <<< "$out" && fail "gh $c answered a made-up null: $out"
  [[ "$(wc -l < "$t/miss.log")" == "$n" ]] || fail "gh $c: refusal not logged/counted: $(cat "$t/miss.log")"
done
shim 0 run view 7 --json conclusion,status; [[ "$out" == *'"conclusion": null'* ]] || fail "genuine null run conclusion: $out"
shim 0 pr view 2 --json mergedAt -q .mergedAt; [[ "$out" == null ]] || fail "genuine null mergedAt: $out"
shim 0 pr list --json number,mergedAt; [[ "$out" == *'"mergedAt": null'* ]] || fail "genuine null in list: $out"
[[ "$(wc -l < "$t/miss.log")" == "$n" ]] || fail "a genuine null was logged as a miss"
# Kit on kit: a copy of the kit judging itself (kit inside the judged worktree) passes the proof.
mkdir -p "$t/kc"; git -C "$kit" ls-files -z | (cd "$kit" && xargs -0 cp -P --parents -t "$t/kc" 2>/dev/null || true)
cd "$t/kc"; git init -q -b main .; cp "$t/repo/docs/specs/demo.spec.html" docs/specs/zz-demo.spec.html
"$S" init docs/specs/zz-demo.spec.html 0123abc >/dev/null; git add -A; git -c core.hooksPath=/dev/null commit -qm kit
Q="$t/kc/scripts/octo-feather-qc" run 0 docs/specs/zz-demo.status.json 5 acceptance-a
grep -q "qc sandbox: ok   HOME, /var/tmp read-only; the kit is the judged worktree" <<< "$out" || fail "kit-on-kit proof: $out"
echo "qc-gh: ok (kit on kit, snapshot fetched outside per run, read-only inside, proof line, offline gh reads, writes refused and counted, brief names evidence, fetch failure 67, --no-github, no remote, PR and id validation, failed status commit restored, --json fields absent from the snapshot refused and counted, stored nulls kept)"
