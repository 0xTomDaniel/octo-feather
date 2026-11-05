#!/usr/bin/env bash
# Integration test for the tracker per target (spec skills#tracker, docs/adr/0004), offline:
#   default: a target with no .octo-feather.toml gets github-pr and github-issues from pi-role, not linear;
#   unknown: tracker = "jira" makes pi-role and octo-feather-start --issue N exit non-zero naming jira and
#            the kit's trackers, and no workspace or supervisor starts (fake herdr, tests/start.sh style);
#   scripts: check-skills (in `just check`) fails a tracker skill missing any tracker script, naming both;
#   github-issues: each tracker script runs against the offline fake gh (github-pr's scripts/gh), whose
#            refusal of writes passes through, and against a recording gh for the write arguments; issue-view
#            lists sub-issue keys as children and refuses a partial list;
#   linear: tracker = "linear" makes pi-role pass github-pr and linear to the supervisor, never github-issues, and
#            linear-cli to no role; each linear script reads and writes through the offline fake linear (linear's
#            scripts/linear, a JSON store), which refuses any other command; same output shapes as github-issues;
#            issue-done leaves an issue already done (Canceled) unchanged; the fake's api answers a query under any
#            operation name or none with only the selected fields (nested, aliased, paged by first) and refuses a
#            field outside Linear's schema by name, so issue-view's JSON proves what its query selects.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "tracker test: $*" >&2; exit 1; }
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
skills() { # DIR ROLE: the skill names pi-role passes, one line, or pi-role's failure in $err
  (cd "$1" && "$kit/scripts/pi-role" --json "$kit/agents/$2.md" 2>"$t/err") \
    | python3 -c 'import json,sys; a=json.load(sys.stdin)["args"]; print(" ".join(a[i+1].rsplit("/",1)[1] for i,x in enumerate(a) if x=="--skill"))'
}

# Default: no config, then an explicit github, from a subdirectory of the target.
g init -q "$t/target"; mkdir -p "$t/target/sub"
for case in none github; do
  [[ "$case" == none ]] || echo 'tracker = "github"' > "$t/target/.octo-feather.toml"
  got=" $(skills "$t/target/sub" supervisor) "
  [[ "$got" == *" github-pr "* && "$got" == *" github-issues "* && "$got" != *" linear "* && "$got" != *"{tracker}"* ]] \
    || fail "supervisor skills with tracker $case: $got"
done
got=" $(skills "$t/target" code-reviewer) "
[[ "$got" == " code-review github-pr tdd " ]] || fail "code-reviewer lists no {tracker} but got: $got"

# Unknown: pi-role refuses naming jira and github.
echo 'tracker = "jira"' > "$t/target/.octo-feather.toml"
set +e; out="$(cd "$t/target" && "$kit/scripts/pi-role" --json "$kit/agents/supervisor.md" 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 && "$out" == *"unknown tracker 'jira'"* && "$out" == *"the kit has: github"* && "$out" != *'"args"'* ]] \
  || fail "pi-role with tracker jira: rc=$rc $out"
# ... and octo-feather-start --issue starts nothing: no workspace, tab or agent in the fake herdr's log.
mkdir -p "$t/bin"
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG"
case "$1 ${2:-}" in
  "workspace list") echo '{"result":{"workspaces":[]}}' ;;
  "workspace create") echo '{"result":{"workspace":{"workspace_id":"w1"},"tab":{"tab_id":"t1"}}}' ;;
  "tab create") echo '{"result":{"tab":{"tab_id":"t2"},"root_pane":{"pane_id":"p2"}}}' ;;
esac
EOF
printf '#!/usr/bin/env bash\necho Linux\n' > "$t/bin/uname"
chmod +x "$t/bin/herdr" "$t/bin/uname"; : > "$t/log"
set +e; out="$(cd "$t" && env -u HERDR_SESSION -u HERDR_PANE_ID PATH="$t/bin:$PATH" FAKE_LOG="$t/log" \
  "$kit/scripts/octo-feather-start" --issue 5 --cwd "$t/target" 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 && "$out" == *"jira"* && "$out" == *"the kit has: github"* ]] || fail "octo-feather-start with tracker jira: rc=$rc $out"
! grep -qE '^(workspace create|tab create|agent start)' "$t/log" || fail "a workspace or agent started: $(cat "$t/log")"

# Scripts: a kit copy whose github-issues lacks one tracker script fails check-skills naming skill and script.
mkdir -p "$t/kit/scripts"
cp -r "$kit/agents" "$t/kit/"; cp -r "$kit/.agents" "$t/kit/"; cp "$kit/scripts/check-skills" "$kit/scripts/pi-role" "$t/kit/scripts/"; cp "$kit/web-mcp.json" "$t/kit/"; cp -r "$kit/extensions" "$t/kit/"
python3 "$t/kit/scripts/check-skills" >/dev/null || fail "check-skills fails on the kit copy itself"
out="$(python3 "$t/kit/scripts/check-skills")"; [[ "$out" == *"trackers github, linear)"* ]] || fail "check-skills covers both trackers: $out"
for sk in github-issues linear; do
  for s in lane-key key-from-branch issue-view issue-create issue-comment issue-done pr-line; do
    mv "$t/kit/.agents/skills/$sk/scripts/$s" "$t/held"
    set +e; out="$(python3 "$t/kit/scripts/check-skills" 2>&1)"; rc=$?; set -e
    [[ "$rc" == 1 && "$out" == *"tracker skill $sk: missing tracker script $s "* ]] || fail "check-skills without $sk $s: rc=$rc $out"
    mv "$t/held" "$t/kit/.agents/skills/$sk/scripts/$s"
  done
done
chmod -x "$t/kit/.agents/skills/linear/scripts/issue-done"
set +e; out="$(python3 "$t/kit/scripts/check-skills" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 && "$out" == *"tracker skill linear: tracker script issue-done is not executable"* ]] || fail "check-skills with linear issue-done not executable: rc=$rc $out"
chmod +x "$t/kit/.agents/skills/linear/scripts/issue-done"
chmod -x "$t/kit/.agents/skills/github-issues/scripts/pr-line"
set +e; out="$(python3 "$t/kit/scripts/check-skills" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 && "$out" == *"tracker script pr-line is not executable"* ]] || fail "check-skills with pr-line not executable: rc=$rc $out"

# github-issues against the offline fake gh: a snapshot of o/r with issue 3 (sub-issues 7, 8), 7 (parent 3, blocked
# by 4 and 5) and 8, and 9 whose sub-issue list gh pages (2 of 3 returned).
GI="$kit/.agents/skills/github-issues/scripts"
sn="$t/snap"; mkdir -p "$sn/issue" "$t/fake" "$t/rec"
echo '{"repo": "o/r", "fetched_at": "2026-10-22T00:00:00Z", "counts": {}, "capped": []}' > "$sn/meta.json"
issue() { # N PARENT BLOCKERS(json list of numbers) [STATE] [CHILDREN(json list of numbers)] [CHILD_TOTAL]
  local ch="${5:-[]}"
  cat > "$sn/issue/$1.json" <<EOF
{"number": $1, "title": "Issue $1", "body": "body $1", "state": "${4:-OPEN}", "url": "https://github.com/o/r/issues/$1",
 "parent": $2, "blockedBy": {"nodes": $(jq -c 'map({number: .})' <<<"$3"), "totalCount": $(jq length <<<"$3")},
 "subIssues": {"nodes": $(jq -c 'map({number: ., state: "OPEN", title: "t", url: "u"})' <<<"$ch"), "totalCount": ${6:-$(jq length <<<"$ch")}}}
EOF
}
issue 3 null '[]' OPEN '[7, 8]'
issue 9 null '[]' OPEN '[7, 8]' 3
issue 7 '{"number": 3, "title": "Parent", "url": "https://github.com/o/r/issues/3"}' '[4, 5]'
issue 8 null '[]' CLOSED
ln -s "$kit/.agents/skills/github-pr/scripts/gh" "$t/fake/gh"
ghdir="$t/fake"
off() { # WANT SCRIPT ARGS...: run with $ghdir's gh first on PATH; stdout in $out, stderr in $err
  local want="$1" script="$GI/$2" rc; shift 2
  set +e; out="$(cd "$t/target" && PATH="$ghdir:$PATH" OCTO_FEATHER_GHSNAP="$sn" "$script" "$@" 2>"$t/err")"; rc=$?; set -e; err="$(cat "$t/err")"
  [[ "$rc" == "$want" ]] || fail "${script##*/} $* under $ghdir/gh: want exit $want, got $rc: $out $err"
}
off 0 issue-view 7
[[ "$(jq -c . <<<"$out")" == '{"key":"7","title":"Issue 7","body":"body 7","state":"open","url":"https://github.com/o/r/issues/7","parent":"3","children":[],"blocked_by":["4","5"]}' ]] \
  || fail "issue-view 7: $out"
off 0 issue-view '#8'
[[ "$(jq -c '[.key, .state, .parent, .blocked_by]' <<<"$out")" == '["8","done",null,[]]' ]] || fail "issue-view 8: $out"
off 0 issue-view 3; [[ "$(jq -c .children <<<"$out")" == '["7","8"]' ]] || fail "issue-view 3 children: $out"
off 1 issue-view 9; [[ -z "$out" && "$err" == *"partial or unreadable sub-issue list"* ]] || fail "issue-view 9, paged sub-issues: $out $err"
off 1 issue-view 10; [[ -z "$out" && "$err" == *"not in snapshot"* ]] || fail "issue-view 10 reason: $out $err"
off 1 issue-view ENG-1; [[ "$err" == *"not a GitHub issue key"* ]] || fail "issue-view ENG-1: $err"
for k in 82 '#82' gh82 https://github.com/o/r/issues/82; do off 0 lane-key "$k"; [[ "$out" == gh82 ]] || fail "lane-key $k: $out"; done
off 1 lane-key ENG-123; [[ -z "$out" && "$err" == *"not a GitHub issue number"* ]] || fail "lane-key ENG-123: $out $err"
for b in gh82 lanes/gh82 gh82-fix implementer-gh82 gh82-gh97; do off 0 key-from-branch "$b"; [[ "$out" == 82 ]] || fail "key-from-branch $b: $out"; done
off 1 key-from-branch main; [[ "$err" == *"names no GitHub issue"* ]] || fail "key-from-branch main: $err"
off 0 pr-line 82; [[ "$out" == "Closes #82" ]] || fail "pr-line 82: $out"
# Writes: the fake gh is read-only, so each write exits non-zero with its refusal and prints nothing.
echo hi > "$t/body"
off 1 issue-create --title T --body-file "$t/body"; [[ -z "$out" && "$err" == *"read-only snapshot"* ]] || fail "issue-create refusal: $out $err"
off 1 issue-comment 7 --body-file "$t/body"; [[ -z "$out" && "$err" == *"read-only snapshot"* ]] || fail "issue-comment refusal: $out $err"
off 1 issue-done 7; [[ -z "$out" && "$err" == *"read-only snapshot"* ]] || fail "issue-done refusal: $out $err"

# Writes against a recording gh: the one gh command each runs, and what it prints.
ghdir="$t/rec"
cat > "$ghdir/gh" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$GH_LOG"; [[ " $* " != *" --body-file - "* ]] || printf 'stdin=%s\n' "$(cat)" >> "$GH_LOG"
case "$1 $2" in
  "issue create") echo "https://github.com/o/r/issues/12" ;;
  "issue comment") echo "https://github.com/o/r/issues/$3#issuecomment-99" ;;
  "issue close") [[ "$3" == 6 ]] && echo "! Issue o/r#6 (x) is already closed" >&2 || echo "✓ Closed issue o/r#$3 (x)" ;;
esac
EOF
chmod +x "$ghdir/gh"; export GH_LOG="$t/gh.log"
off 0 issue-create --title "New one" --body-file "$t/body" --parent '#3' --blocked-by 4 --blocked-by 5
[[ "$out" == 12 && "$(tail -1 "$GH_LOG")" == "issue create --title New one --body-file $t/body --parent 3 --blocked-by 4,5" ]] \
  || fail "issue-create: $out; gh $(tail -1 "$GH_LOG")"
set +e; out="$(cd "$t/target" && PATH="$ghdir:$PATH" "$GI/issue-comment" 7 <<<"a note" 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 && "$out" == "https://github.com/o/r/issues/7#issuecomment-99" && "$(tail -2 "$GH_LOG")" == $'issue comment 7 --body-file -\nstdin=a note' ]] \
  || fail "issue-comment from stdin: rc=$rc $out; gh $(tail -2 "$GH_LOG")"
off 0 issue-done 7; [[ -z "$out" && -z "$err" && "$(tail -1 "$GH_LOG")" == "issue close 7" ]] || fail "issue-done 7: $out $err"
off 0 issue-done 6; [[ -z "$out" && -z "$err" ]] || fail "issue-done on a closed issue printed: $out $err"
# Linear: a target whose config selects it gets github-pr and linear, never github-issues; no role gets linear-cli.
echo 'tracker = "linear"' > "$t/target/.octo-feather.toml"
got=" $(skills "$t/target/sub" supervisor) "
[[ "$got" == *" github-pr "* && "$got" == *" linear "* && "$got" != *" github-issues "* && "$got" != *" linear-cli "* ]] \
  || fail "supervisor skills with tracker linear: $got"
for r in "$kit"/agents/*.md; do
  r="$(basename "$r" .md)"; got=" $(skills "$t/target" "$r") "
  [[ "$got" != *" linear-cli "* && "$got" != *" github-issues "* ]] || fail "$r with tracker linear: $got"
done

# linear scripts against the offline fake linear: a store with ENG-7 (parent ENG-3, blocked by ENG-4 and ENG-5) and ENG-8 done.
LI="$kit/.agents/skills/linear/scripts"
export OCTO_FEATHER_LINEAR_STORE="$t/store.json"
cat > "$OCTO_FEATHER_LINEAR_STORE" <<'EOF'
{"workspace": "acme", "issues": {
 "ENG-3": {"title": "Parent", "description": "p", "state": "In Progress", "parent": null, "blocked_by": []},
 "ENG-4": {"title": "B4", "description": "b", "state": "Todo", "parent": null, "blocked_by": []},
 "ENG-5": {"title": "B5", "description": "b", "state": "Todo", "parent": null, "blocked_by": []},
 "ENG-7": {"title": "Issue 7", "description": "body 7", "state": "Todo", "parent": "ENG-3", "blocked_by": ["ENG-4", "ENG-5"]},
 "ENG-8": {"title": "Issue 8", "description": null, "state": "Canceled", "parent": null, "blocked_by": []}}}
EOF
lin() { # WANT SCRIPT ARGS...: run with the fake linear first on PATH; stdout in $out, stderr in $err
  local want="$1" script="$LI/$2" rc; shift 2
  set +e; out="$(cd "$t/target" && PATH="$LI:$PATH" "$script" "$@" 2>"$t/err")"; rc=$?; set -e; err="$(cat "$t/err")"
  [[ "$rc" == "$want" ]] || fail "linear ${script##*/} $*: want exit $want, got $rc: $out $err"
}
lin 0 issue-view ENG-7
[[ "$(jq -c . <<<"$out")" == '{"key":"ENG-7","title":"Issue 7","body":"body 7","state":"open","url":"https://linear.app/acme/issue/ENG-7/issue-7","parent":"ENG-3","children":[],"blocked_by":["ENG-4","ENG-5"]}' ]] \
  || fail "linear issue-view ENG-7: $out"
lin 0 issue-view ENG-3; [[ "$(jq -c .children <<<"$out")" == '["ENG-7"]' ]] || fail "linear issue-view ENG-3 children: $out"
lin 0 issue-view eng-8
[[ "$(jq -c '[.key, .body, .state, .parent, .blocked_by]' <<<"$out")" == '["ENG-8","","done",null,[]]' ]] || fail "linear issue-view eng-8: $out"
# Same shape as github-issues' issue-view: the same keys, keys as strings.
[[ "$(jq -c 'keys' <<<"$out")" == '["blocked_by","body","children","key","parent","state","title","url"]' ]] || fail "linear issue-view keys: $out"
lin 1 issue-view ENG-9; [[ -z "$out" && "$err" == *"Entity not found"* ]] || fail "linear issue-view ENG-9: $out $err"
lin 1 issue-view 82; [[ "$err" == *"not a Linear issue key"* ]] || fail "linear issue-view 82: $err"
for k in ENG-123 eng-123 https://linear.app/acme/issue/ENG-123/some-title; do lin 0 lane-key "$k"; [[ "$out" == eng-123 ]] || fail "lane-key $k: $out"; done
lin 1 lane-key 82; [[ -z "$out" && "$err" == *"not a Linear issue key"* ]] || fail "linear lane-key 82: $out $err"
for b in eng-123 lanes/eng-123 eng-123-fix implementer-eng-123 code-reviewer-eng-123; do
  lin 0 key-from-branch "$b"; [[ "$out" == ENG-123 ]] || fail "linear key-from-branch $b: $out"
done
lin 1 key-from-branch main; [[ "$err" == *"names no Linear issue"* ]] || fail "linear key-from-branch main: $err"
lin 0 pr-line eng-123; [[ "$out" == "Tracks ENG-123" ]] || fail "linear pr-line: $out"
# Writes go to the fake's store and print what github-issues prints: the key, the comment url, nothing.
lin 0 issue-create --title "New one" --body-file "$t/body" --parent eng-3 --blocked-by ENG-4 --blocked-by ENG-5
[[ "$out" == ENG-9 ]] || fail "linear issue-create: $out"
lin 0 issue-view ENG-9
[[ "$(jq -c '[.title, .body, .state, .parent, .blocked_by]' <<<"$out")" == '["New one","hi\n","open","ENG-3",["ENG-4","ENG-5"]]' ]] || fail "linear new ENG-9: $out"
lin 1 issue-create --title T --body-file "$t/body"; [[ -z "$out" && "$err" == *"No team given"* ]] || fail "linear issue-create, no team: $out $err"
lin 1 issue-create --title T --body-file "$t/body" --parent ENG-3 --blocked-by ENG-99
[[ -z "$out" && "$err" == *"filed ENG-10, but marking it blocked by ENG-99 failed"* ]] || fail "linear issue-create, bad blocker: $out $err"
set +e; out="$(cd "$t/target" && PATH="$LI:$PATH" "$LI/issue-comment" ENG-7 <<<"a note" 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 && "$out" == "https://linear.app/acme/issue/ENG-7/issue-7#comment-c1" \
   && "$(jq -c '.issues["ENG-7"].comments' "$OCTO_FEATHER_LINEAR_STORE")" == '[{"id":"c1","body":"a note\n"}]' ]] \
  || fail "linear issue-comment from stdin: rc=$rc $out"
lin 0 issue-comment ENG-7 --body-file "$t/body"; [[ "$out" == *"#comment-c2" ]] || fail "linear issue-comment --body-file: $out"
lin 0 issue-done ENG-7; [[ -z "$out" && -z "$err" ]] || fail "linear issue-done ENG-7 printed: $out $err"
[[ "$(jq -r '.issues["ENG-7"].state' "$OCTO_FEATHER_LINEAR_STORE")" == Done ]] || fail "issue-done did not move ENG-7 to Done"
lin 0 issue-view ENG-7; [[ "$(jq -r .state <<<"$out")" == "done" ]] || fail "linear ENG-7 after issue-done: $out"
lin 0 issue-done ENG-7; [[ -z "$out" && -z "$err" ]] || fail "linear issue-done on a done issue printed: $out $err"
lin 1 issue-done ENG-99; [[ "$err" == *"not found"* ]] || fail "linear issue-done ENG-99: $err"
# An issue already done stays as it is: Canceled is done, so issue-done leaves it Canceled.
lin 0 issue-done ENG-8; [[ -z "$out" && -z "$err" && "$(jq -r '.issues["ENG-8"].state' "$OCTO_FEATHER_LINEAR_STORE")" == Canceled ]] \
  || fail "linear issue-done moved canceled ENG-8: $out $err $(jq -r '.issues["ENG-8"].state' "$OCTO_FEATHER_LINEAR_STORE")"
# The fake's api answers any query document the way Linear's GraphQL API does: any operation name or none, only the
# fields selected (nested, aliased, connections paged by first), and a field outside Linear's schema refused by name.
fapi() { # WANT DOCUMENT [ARGS...]: the fake linear api, stdout and stderr in $out
  local want="$1" rc; shift
  set +e; out="$(PATH="$LI:$PATH" linear api --no-input "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "fake linear api $*: want exit $want, got $rc: $out"
}
for doc in 'query ReadTicket($id: String!) { issue(id: $id) { identifier title } }' 'query($id: String!) { issue(id: $id) { identifier title } }' \
           '{ issue(id: $id) { identifier title } }'; do
  fapi 0 --variable id=ENG-3 "$doc"
  [[ "$(jq -c . <<<"$out")" == '{"data":{"issue":{"identifier":"ENG-3","title":"Parent"}}}' ]] || fail "fake linear api, $doc: $out"
done
fapi 0 'query Lean { issue(id: "ENG-9") { identifier } }'
[[ "$(jq -c . <<<"$out")" == '{"data":{"issue":{"identifier":"ENG-9"}}}' ]] || fail "fake linear api returns only the selected fields: $out"
fapi 0 '{ issue(id: "ENG-9") { key: identifier state { type name } parent { identifier title }
  children(first: 1) { nodes { identifier } pageInfo { hasNextPage } } inverseRelations { nodes { type issue { identifier } } } } }'
[[ "$(jq -c . <<<"$out")" == '{"data":{"issue":{"key":"ENG-9","state":{"type":"unstarted","name":"Todo"},"parent":{"identifier":"ENG-3","title":"Parent"},"children":{"nodes":[],"pageInfo":{"hasNextPage":false}},"inverseRelations":{"nodes":[{"type":"blocks","issue":{"identifier":"ENG-4"}},{"type":"blocks","issue":{"identifier":"ENG-5"}}]}}}}' ]] \
  || fail "fake linear api, nested and aliased selection: $out"
fapi 0 '{ issue(id: "ENG-3") { children(first: 1) { nodes { identifier } pageInfo { hasNextPage } } } }'
[[ "$(jq -c .data.issue.children <<<"$out")" == '{"nodes":[{"identifier":"ENG-7"}],"pageInfo":{"hasNextPage":true}}' ]] || fail "fake linear api pages children by first: $out"
fapi 2 '{ issue(id: "ENG-3") { identifier bogus } }'
[[ "$out" == *'linear (offline fake): api: Cannot query field "bogus" on type "Issue"'* ]] || fail "fake linear api, unknown field: $out"
fapi 2 '{ issue(id: "ENG-3") { state { colour } } }'
[[ "$out" == *'Cannot query field "colour" on type "WorkflowState"'* ]] || fail "fake linear api, unknown nested field: $out"
fapi 2 '{ issue(id: "ENG-3") { state } }'
[[ "$out" == *'Field "state" of type "WorkflowState!" must have a selection of subfields'* ]] || fail "fake linear api, object with no selection: $out"
# The fake refuses every other command, and works only from its store.
for c in "issue list" "issue view ENG-7" "issue delete ENG-7" "api query{viewer{id}}" "issue update ENG-7 --label x"; do
  # shellcheck disable=SC2086 # $c is one command line, split into its words
  set +e; out="$(PATH="$LI:$PATH" linear $c 2>&1)"; rc=$?; set -e
  [[ "$rc" == 2 && "$out" == *"linear (offline fake)"* ]] || fail "fake linear $c: rc=$rc $out"
done
set +e; out="$(env -u OCTO_FEATHER_LINEAR_STORE PATH="$LI:$PATH" "$LI/issue-view" ENG-7 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 && "$out" == *"OCTO_FEATHER_LINEAR_STORE is unset"* ]] || fail "fake linear with no store: rc=$rc $out"
echo "tracker: ok (no config and github: github-pr + github-issues, no linear; jira refused by pi-role and octo-feather-start, nothing started;" \
  "check-skills names each missing tracker script in github-issues and linear; github-issues scripts under the offline gh and a recording gh;" \
  "linear: supervisor gets github-pr + linear, no role gets linear-cli; linear scripts read and write through the offline fake linear, whose api honours any query's selection)"
