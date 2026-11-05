#!/usr/bin/env bash
# Integration test for octo-feather-lane post-merge step 5, teardown (owner ruling 2026-10-29 on issue 206; issue
# 399), offline: a throwaway target repo with a bare origin holds lane branch gh12, its worktree and its merge
# commit; a fake gh holds PR #12 merged there with a green push run and PR #13 based on gh12; a fake herdr-close and
# a fake herdr stand for Herdr (HERDR_SESSION unset); a throwaway state dir (XDG_STATE_HOME) holds the lane records,
# director.toml and the Spec Chat registries; a throwaway kit install clone (OCTO_FEATHER_KIT_INSTALL, never the
# live kit) of another repo, so step 3 leaves it unchanged. Not archived: steps 1-4 run, step 5 pending, exit 3.
# Archived: the lane's own space is closed (only its supervisor pane's tab when shared), its worktree removed, PRs
# based on its branch retargeted before the remote branch is deleted, the local branch deleted; a rerun prints
# already for each, on a repo with no workflow as with a green run. A dirty worktree, the kit install, the main worktree and a review row's root are kept, exit 1.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-post-merge-teardown test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" OCTO_FEATHER_KIT_INSTALL="$t/kit" GH_STORE="$t/gh.json" GH_LOG="$t/gh.log" \
  CLOSE_LOG="$t/close.log" HERDR_PANES="$t/panes" HERDR_SPACES="$t/spaces" ORIGIN="$t/origin.git" \
  GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
unset GH_REPO GH_TOKEN HERDR_SESSION OCTO_FEATHER_ROLE
mkdir -p "$HOME" "$t/bin"
st="$t/state/octo-feather" lanes="$t/state/octo-feather/lanes" reg="$t/state/spec-chat/hosting/s1"

# Fake gh: pr view 12, repo view, a green run list (with NO_CI set: no run, and the merge commit's tree has no .github,
# the no-CI fact), pr list --base <b> --state open (from .based), pr edit N --base B
# (logs whether gh12 is still on origin at that moment, then drops N from .based); anything else is refused.
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, subprocess, sys
a = sys.argv[1:]; db = json.load(open(os.environ["GH_STORE"]))
def opt(f): return a[a.index(f) + 1] if f in a else None
def log(s): open(os.environ["GH_LOG"], "a").write(s + "\n")
if a[:3] == ["pr", "view", "12"]:
    print(json.dumps({k: db["pr"][k] for k in opt("--json").split(",")})); sys.exit(0)
if a[:2] == ["repo", "view"] and opt("--json") == "nameWithOwner":
    print(json.dumps({"nameWithOwner": a[2].removeprefix("https://github.com/").removesuffix(".git")})); sys.exit(0)
if a[:2] == ["run", "list"] and os.environ.get("NO_CI"):
    print("[]"); sys.exit(0)
if a[:2] == ["api", f"repos/o/r/git/trees/{db['pr']['mergeCommit']['oid']}"] and os.environ.get("NO_CI"):
    log(" ".join(a)); print(json.dumps({"tree": [{"path": "a", "type": "blob", "sha": "x"}]})); sys.exit(0)
if a[:2] == ["run", "list"]:
    print(json.dumps([{"databaseId": 1, "status": "completed", "conclusion": "success", "workflowName": "check",
                       "url": "https://github.com/o/r/actions/runs/1"}])); sys.exit(0)
if a[:2] == ["pr", "list"] and opt("--state") == "open" and opt("--base"):
    log(f"pr list --base {opt('--base')}")
    print(json.dumps([{"number": n} for n in db["based"].get(opt("--base"), [])])); sys.exit(0)
if a[:2] == ["pr", "edit"] and opt("--base"):
    on = subprocess.run(["git", "--git-dir", os.environ["ORIGIN"], "rev-parse", "-q", "--verify", "refs/heads/gh12"],
                        capture_output=True).returncode == 0
    log(f"pr edit {a[2]} --base {opt('--base')} (gh12 on origin: {'yes' if on else 'no'})")
    for b in db["based"].values():
        if int(a[2]) in b: b.remove(int(a[2]))
    json.dump(db, open(os.environ["GH_STORE"], "w")); sys.exit(0)
print(f"fake gh: refused {' '.join(a)}", file=sys.stderr); sys.exit(1)
EOF
# Fake herdr: `agent get PANE` finds the panes in $HERDR_PANES ("PANE TAB"), `workspace get SPACE` the spaces in
# $HERDR_SPACES; others are not found. Each prints exactly as real herdr 0.9.5 `agent get` / `workspace get`
# (captured 2026-10-30, ticket #458 comment): found, the result JSON on stdout, exit 0; not found, the error JSON
# on stderr, empty stdout, exit 1.
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
case "$1 $2" in
  "agent get") tab="$(awk -v p="$3" '$1 == p {print $2}' "$HERDR_PANES")"
    [[ -n "$tab" ]] || { echo '{"error":{"code":"agent_not_found","message":"agent target '"$3"' not found"},"id":"cli:agent:get"}' >&2; exit 1; }
    printf '{"id":"cli:agent:get","result":{"agent":{"agent":"pi","agent_status":"working","cwd":"/tmp/fixture","focused":false,"foreground_cwd":"/tmp/fixture","interactive_ready":true,"name":"fixture","pane_id":"%s","revision":2,"state_change_seq":7969,"tab_id":"%s","terminal_id":"term_fixture","terminal_title":"π - fixture","terminal_title_stripped":"π - fixture","workspace_id":"%s"},"type":"agent_info"}}\n' "$3" "$tab" "${3%%:*}";;
  "workspace get") grep -qxF "$3" "$HERDR_SPACES" \
    || { echo '{"error":{"code":"workspace_not_found","message":"workspace '"$3"' not found"},"id":"cli:workspace:get"}' >&2; exit 1; }
    printf '{"id":"cli:workspace:get","result":{"type":"workspace_info","workspace":{"workspace_id":"%s"}}}\n' "$3";;
  *) echo "fake herdr: refused $*" >&2; exit 1;;
esac
EOF
# Fake herdr-close: logs its argument; closes a space or a pane's tab that exists, as herdr-close reports it.
cat > "$t/bin/herdr-close" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "$CLOSE_LOG"
if [[ "$1" == *:p* ]]; then
  tab="$(awk -v p="$1" '$1 == p {print $2}' "$HERDR_PANES")"
  [[ -n "$tab" ]] || { echo "herdr-close: cannot map pane $1 to its tab (no Herdr agent there); nothing closed" >&2; exit 65; }
  grep -v "^$1 " "$HERDR_PANES" > "$HERDR_PANES.n" || true; mv "$HERDR_PANES.n" "$HERDR_PANES"
  echo "tab=$tab tab_close_rc=0 killed=0"; exit 0
fi
grep -qxF "$1" "$HERDR_SPACES" || { echo "space=$1 space_close_rc=1 killed=0"; exit 1; }
grep -vxF "$1" "$HERDR_SPACES" > "$HERDR_SPACES.n" || true; mv "$HERDR_SPACES.n" "$HERDR_SPACES"
awk -v s="$1" 'index($1, s ":") != 1' "$HERDR_PANES" > "$HERDR_PANES.n"; mv "$HERDR_PANES.n" "$HERDR_PANES"
echo "space=$1 space_close_rc=0 killed=0"
EOF
printf '#!/bin/sh\nexit 0\n' > "$t/bin/herdr-say"
chmod +x "$t/bin/"*

fresh() { # the target repo r (main merged gh12 at M, lane worktree wt on gh12), its origin, state, Herdr, gh store
  rm -rf "$t/r" "$t/wt" "$ORIGIN" "$t/kit" "$t/state" "$GH_LOG" "$CLOSE_LOG"
  git init -q --bare -b main "$ORIGIN"; git init -q -b main "$t/r"; cd "$t/r"; git remote add origin "$ORIGIN"
  echo a > a; git add a; git commit -qm base
  git checkout -qb gh12; echo b > b; git add b; git commit -qm lane; H="$(git rev-parse HEAD)"
  git checkout -q main; git merge -q --no-ff gh12 -m "Merge #12"; M="$(git rev-parse HEAD)"
  git push -q origin main gh12 2>/dev/null; git worktree add -q "$t/wt" gh12
  git clone -q "$t/r" "$t/kit"; git -C "$t/kit" remote set-url origin https://github.com/o/kit.git
  mkdir -p "$lanes/archive" "$reg"
  echo 'pane = "w1:p1"' > "$st/director.toml"
  printf '[[resource]]\nslug = "s"\nspec = "docs/s.spec.html"\nroot = "%s"\n' "$t/r" > "$reg/registry.toml"
  printf '%s\n' w1 w5 w6 > "$HERDR_SPACES"; printf '%s\n' "w1:p1 w1:t1" "w5:p1 w5:t1" "w6:p1 w6:t2" > "$HERDR_PANES"
  jq -n --arg h "$H" --arg m "$M" '{pr: {state: "MERGED", headRefOid: $h, mergeCommit: {oid: $m}, baseRefName: "main",
    headRefName: "gh12", title: "Lane 12", url: "https://github.com/o/r/pull/12"}, based: {gh12: [13]}}' > "$GH_STORE"
}
lane() { # FILE PANE PR: a lane record of issue 12
  printf 'supervisor = "%s"\nrepository = "o/r"\nissue = 12\npr = %s\ngoal = "g"\nstarted_at = "2026-10-29T00:00:00Z"\n' "$2" "$3" > "$1"
}
run() { # WANT: post-merge 12 H --lane gh12 from the target repo, fakes first on PATH
  local want="$1" rc
  set +e; out="$(cd "$t/r" && PATH="$t/bin:$PATH" "$L" post-merge 12 "$H" --lane gh12 --repo o/r --wait 0 2>"$t/err")"; rc=$?; set -e
  err="$(cat "$t/err")"
  [[ "$rc" == "$want" ]] || fail "want exit $want, got $rc: $out $err"
  ! grep -q Traceback <<<"$err" || fail "printed a traceback: $err"
  s5="$(grep '^step 5 teardown: ' <<<"$out")" || fail "no step 5 line: $out"
  last="$(tail -n1 <<<"$out")"
}
s4="post-merge gh12 PR #12: step 1 merged ok; step 2 main CI ok; step 3 kit refresh ok; step 4 tell supervisors ok"
kept() { # what step 5 must not have touched
  [[ -d "$t/wt" ]] && git -C "$t/r" rev-parse -q --verify refs/heads/gh12 >/dev/null \
    && git --git-dir "$ORIGIN" rev-parse -q --verify refs/heads/gh12 >/dev/null || fail "$1: worktree or branch gone"
}

# Not archived (the record is still open): steps 1-4 run, step 5 pending, exit 3, nothing closed or removed.
fresh; lane "$lanes/gh12.toml" w5:p1 12
run 3
[[ "$s5" == "step 5 teardown: pending: lane gh12 not archived; rerun on its close report" ]] || fail "pending line: $s5"
[[ "$last" == "$s4; step 5 teardown pending" && ! -e "$CLOSE_LOG" ]] || fail "pending: $out"
kept pending

# Archived with another PR: stop named, nothing torn down.
fresh; lane "$lanes/archive/gh12.toml" w5:p1 99
run 1
[[ "$s5" == "step 5 teardown: stopped: archived lane gh12 names PR #99, not #12"* && "$last" == "$s4; step 5 teardown stopped" ]] || fail "other pr: $out"
[[ ! -e "$CLOSE_LOG" ]] || fail "other pr closed: $(cat "$CLOSE_LOG")"; kept "other pr"

# Archived, its own space: the space closed, worktree removed, #13 retargeted while gh12 is still on origin, then the
# local and remote branch deleted; exit 0. A rerun prints already for each and changes nothing.
fresh; lane "$lanes/archive/gh12.toml" w5:p1 12; lane "$lanes/other.toml" w6:p1 14
run 0
[[ "$(cat "$CLOSE_LOG")" == w5 ]] || fail "own space: closed $(cat "$CLOSE_LOG")"
[[ "$s5" == "step 5 teardown: ok: space w5 closed; worktree $t/wt removed; PR #13 retargeted from gh12 to main; local branch gh12 deleted; remote branch gh12 deleted from origin" ]] || fail "teardown line: $s5"
[[ "$last" == "$s4; step 5 teardown ok" && ! -d "$t/wt" ]] || fail "teardown: $out"
! git rev-parse -q --verify refs/heads/gh12 >/dev/null || fail "local branch kept"
! git --git-dir "$ORIGIN" rev-parse -q --verify refs/heads/gh12 >/dev/null || fail "remote branch kept"
grep -qx "pr edit 13 --base main (gh12 on origin: yes)" "$GH_LOG" || fail "retarget not before the remote delete: $(cat "$GH_LOG")"
run 0
[[ "$s5" == "step 5 teardown: ok: space w5 already closed; worktree of gh12 already removed; no open PR based on gh12; local branch gh12 already deleted; remote branch gh12 already deleted from origin" ]] || fail "rerun: $s5"

# The no-CI fact (issue 569; exosurface, gh33): no push run and no .github at the merge commit: step 2 ok naming it, no
# wait, and the same teardown runs; a rerun prints already for each.
fresh; lane "$lanes/archive/gh12.toml" w5:p1 12
NO_CI=1 run 0
grep -qxF "step 2 main CI: ok: no CI: no workflow file under .github/workflows at merge commit ${M:0:12} (gh api repos/o/r/git/trees/${M:0:12}), so no push run can appear; nothing to wait for" <<<"$out" || fail "no CI step 2: $out"
[[ "$s5" == "step 5 teardown: ok: space w5 closed; worktree $t/wt removed; PR #13 retargeted from gh12 to main; local branch gh12 deleted; remote branch gh12 deleted from origin" && "$last" == "$s4; step 5 teardown ok" ]] || fail "no CI teardown: $out"
grep -qx "api repos/o/r/git/trees/$M" "$GH_LOG" || fail "no CI fact not read at the merge commit: $(cat "$GH_LOG")"
NO_CI=1 run 0
[[ "$s5" == "step 5 teardown: ok: space w5 already closed; worktree of gh12 already removed; no open PR based on gh12; local branch gh12 already deleted; remote branch gh12 already deleted from origin" && "$last" == "$s4; step 5 teardown ok" ]] || fail "no CI rerun: $out"

# Shared space: another open lane's supervisor, or the director's pane, has the prefix: only the supervisor's tab.
fresh; lane "$lanes/archive/gh12.toml" w6:p1 12; lane "$lanes/other.toml" w6:p3 14
run 0; [[ "$(cat "$CLOSE_LOG")" == w6:p1 && "$s5" == "step 5 teardown: ok: tab of w6:p1 closed in shared space w6; "* ]] || fail "shared lane: $(cat "$CLOSE_LOG") $s5"
grep -qx w6 "$HERDR_SPACES" || fail "shared space closed"
run 0; [[ "$s5" == "step 5 teardown: ok: tab of w6:p1 already closed; "* ]] || fail "shared rerun: $s5"
fresh; lane "$lanes/archive/gh12.toml" w1:p2 12; echo "w1:p2 w1:t2" >> "$HERDR_PANES"
run 0; [[ "$(cat "$CLOSE_LOG")" == w1:p2 ]] || fail "director's space: closed $(cat "$CLOSE_LOG")"

# Refused and kept, exit 1: a dirty worktree (git's words), a review row's root, the kit install, the main worktree.
refused() { # WHAT WANT
  run 1; [[ "$s5" == "step 5 teardown: stopped: "*"$2"* && "$last" == "$s4; step 5 teardown stopped" ]] || fail "$1: $s5"
  ! grep -q "pr edit" "$GH_LOG" 2>/dev/null || fail "$1 retargeted"; kept "$1"
}
fresh; lane "$lanes/archive/gh12.toml" w5:p1 12; echo x > "$t/wt/stray"
refused dirty "worktree $t/wt not removed (fatal: '$t/wt' contains modified or untracked files, use --force to delete it)"
fresh; lane "$lanes/archive/gh12.toml" w5:p1 12; sed -i "s|root = .*|root = \"$t/wt\"|" "$reg/registry.toml"
refused "review root" "worktree $t/wt kept: it is the root of Spec Chat review row s in $reg/registry.toml"
fresh; lane "$lanes/archive/gh12.toml" w5:p1 12
OCTO_FEATHER_KIT_INSTALL="$t/wt" refused "kit install" "worktree $t/wt kept: it is the kit install"
fresh; lane "$lanes/archive/gh12.toml" w5:p1 12; git worktree remove "$t/wt"; git checkout -q gh12; mkdir "$t/wt"
refused "main worktree" "worktree $t/r kept: it is the main worktree"

# A local branch past the merge commit: kept, named.
fresh; lane "$lanes/archive/gh12.toml" w5:p1 12; git -C "$t/wt" commit -q --allow-empty -m later; git worktree remove "$t/wt"; mkdir "$t/wt"
run 1; [[ "$s5" == "step 5 teardown: stopped: "*"local branch gh12 kept: it is not an ancestor of merge commit ${M:0:12}"* ]] || fail "unmerged: $s5"
kept unmerged
echo "lane-post-merge-teardown: ok (not archived pending exit 3; other PR stops; own space closed, shared only the tab;" \
  "worktree removed, PRs retargeted before the remote delete, branches deleted; rerun already; the same on a no-CI repo; dirty, review root," \
  "kit install, main worktree, unmerged branch kept, exit 1)"
