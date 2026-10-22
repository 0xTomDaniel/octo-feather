#!/usr/bin/env bash
# Integration test for the tracker per target (spec skills#tracker, docs/adr/0004), offline:
#   default: a target with no .octo-feather.toml gets github-pr and github-issues from pi-role, not linear;
#   unknown: tracker = "jira" makes pi-role and octo-feather-start --issue N exit non-zero naming jira and
#            the kit's trackers, and no workspace or supervisor starts (fake herdr, tests/start.sh style);
#   scripts: check-skills (in `just check`) fails a tracker skill missing any tracker script, naming both;
#   github-issues: each tracker script runs against the offline fake gh (github-pr's scripts/gh), whose
#            refusal of writes passes through, and against a recording gh for the write arguments.
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
[[ "$got" == " code-review github-pr " ]] || fail "code-reviewer lists no {tracker} but got: $got"

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
cp -r "$kit/agents" "$t/kit/"; cp -r "$kit/.agents" "$t/kit/"; cp "$kit/scripts/check-skills" "$kit/scripts/pi-role" "$t/kit/scripts/"
python3 "$t/kit/scripts/check-skills" >/dev/null || fail "check-skills fails on the kit copy itself"
for s in lane-key key-from-branch issue-view issue-create issue-comment issue-done pr-line; do
  mv "$t/kit/.agents/skills/github-issues/scripts/$s" "$t/held"
  set +e; out="$(python3 "$t/kit/scripts/check-skills" 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 && "$out" == *"tracker skill github-issues: missing tracker script $s "* ]] || fail "check-skills without $s: rc=$rc $out"
  mv "$t/held" "$t/kit/.agents/skills/github-issues/scripts/$s"
done
chmod -x "$t/kit/.agents/skills/github-issues/scripts/pr-line"
set +e; out="$(python3 "$t/kit/scripts/check-skills" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 && "$out" == *"tracker script pr-line is not executable"* ]] || fail "check-skills with pr-line not executable: rc=$rc $out"

# github-issues against the offline fake gh: a snapshot of o/r with issue 7 (parent 3, blocked by 4 and 5) and 8.
GI="$kit/.agents/skills/github-issues/scripts"
sn="$t/snap"; mkdir -p "$sn/issue" "$t/fake" "$t/rec"
echo '{"repo": "o/r", "fetched_at": "2026-10-22T00:00:00Z", "counts": {}, "capped": []}' > "$sn/meta.json"
issue() { # N PARENT BLOCKERS(json list of numbers) [STATE]
  cat > "$sn/issue/$1.json" <<EOF
{"number": $1, "title": "Issue $1", "body": "body $1", "state": "${4:-OPEN}", "url": "https://github.com/o/r/issues/$1",
 "parent": $2, "blockedBy": {"nodes": $(jq -c 'map({number: .})' <<<"$3"), "totalCount": $(jq length <<<"$3")}}
EOF
}
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
[[ "$(jq -c . <<<"$out")" == '{"key":"7","title":"Issue 7","body":"body 7","state":"open","url":"https://github.com/o/r/issues/7","parent":"3","blocked_by":["4","5"]}' ]] \
  || fail "issue-view 7: $out"
off 0 issue-view '#8'
[[ "$(jq -c '[.key, .state, .parent, .blocked_by]' <<<"$out")" == '["8","done",null,[]]' ]] || fail "issue-view 8: $out"
off 1 issue-view 9; [[ -z "$out" && "$err" == *"not in snapshot"* ]] || fail "issue-view 9 reason: $out $err"
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
echo "tracker: ok (no config and github: github-pr + github-issues, no linear; jira refused by pi-role and octo-feather-start, nothing started;" \
  "check-skills names each missing tracker script; github-issues scripts under the offline gh and a recording gh)"
