#!/usr/bin/env bash
# Integration test for octo-feather-lane post-merge step 4, tell supervisors (owner ruling 2026-10-29 on issue
# 206; issue 398), offline: a throwaway git repo holds the merge commit, a fake gh PR #7 merged there with a
# green push run, a fake herdr whose `agent get` finds only the live panes, a fake herdr-say that logs each send,
# and a throwaway state dir (XDG_STATE_HOME) holding the lane records and the director log. A live supervisor of
# the PR's repo gets one message naming the merge commit, PR, title and changed rule files; the --lane lane and a
# lane of another repo get none (unless the PR is the kit's own); a parked one is listed, never sent to. Each lane
# told gets one prod line in the director log, and a rerun sends nothing new. A failed send is named, writes no
# prod line, and stops the step after the rest are tried. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-post-merge-tell test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" GH_STORE="$t/gh.json" HERDR_LOG="$t/herdr.log" SAY_LOG="$t/say.log" \
  HERDR_LIVE="$t/live" SAY_RC="$t/say.rc" GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
unset GH_REPO GH_TOKEN HERDR_SESSION OCTO_FEATHER_ROLE
mkdir -p "$HOME" "$t/bin" "$t/state/octo-feather/lanes"
lanes="$t/state/octo-feather/lanes" dlog="$t/state/octo-feather/director.handoffs.jsonl"

# The PR's merge commit: its branch changed two rule files and one product file against main.
r="$t/repo"; git init -q -b main "$r"; cd "$r"
mkdir -p agents .agents/skills/foo src docs; echo a > agents/supervisor.md; echo a > src/app.py; echo a > docs/notes.md
git add -A; git commit -qm base
git checkout -qb gh7; echo b > agents/supervisor.md; echo b > .agents/skills/foo/SKILL.md; echo b > src/app.py
git add -A; git commit -qm change; H="$(git rev-parse HEAD)"
git checkout -q main; git merge -q --no-ff gh7 -m "Merge #7"; M="$(git rev-parse HEAD)"
# A second merge that touches no rule file (docs/notes.md is under no rule path).
git checkout -qb gh8; echo c > docs/notes.md; git commit -qam notes; H2="$(git rev-parse HEAD)"
git checkout -q main; git merge -q --no-ff gh8 -m "Merge #8"; M2="$(git rev-parse HEAD)"

cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]; db = json.load(open(os.environ["GH_STORE"]))
def opt(f): return a[a.index(f) + 1] if f in a else None
if a[:2] == ["pr", "view"] and a[2] in db["prs"]:
    print(json.dumps({k: db["prs"][a[2]][k] for k in opt("--json").split(",")})); sys.exit(0)
if a[:2] == ["run", "list"]:
    print(json.dumps([{"databaseId": 1, "status": "completed", "conclusion": "success", "workflowName": "check",
                       "url": "https://github.com/o/r/actions/runs/1"}])); sys.exit(0)
print(f"fake gh: refused {' '.join(a)}", file=sys.stderr); sys.exit(1)
EOF
# Fake herdr: `agent get PANE` finds only the panes listed in $HERDR_LIVE; anything else is refused.
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "$HERDR_LOG"
[[ "$1 $2" == "agent get" ]] || { echo "fake herdr: refused $*" >&2; exit 1; }
grep -qxF "$3" "$HERDR_LIVE" 2>/dev/null || { echo '{"error":{"code":"agent_not_found","message":"agent target '"$3"' not found"}}'; exit 1; }
printf '{"result":{"agent":{"pane_id":"%s","agent_status":"idle"},"type":"agent_info"}}\n' "$3"
EOF
# Fake herdr-say: logs "PANE<TAB>MESSAGE"; exits the code $SAY_RC names for the pane ("PANE RC" lines), else 0.
cat > "$t/bin/herdr-say" <<'EOF'
#!/usr/bin/env bash
printf '%s\t%s\n' "$1" "$2" >> "$SAY_LOG"
rc="$(awk -v p="$1" '$1 == p {print $2}' "$SAY_RC" 2>/dev/null)"
[[ "${rc:-0}" == 0 ]] || echo "herdr-say: $1 is blocked on interactive input; not delivered" >&2
exit "${rc:-0}"
EOF
chmod +x "$t/bin/"*
store() { # TITLE URL
  jq -n --arg h "$H" --arg m "$M" --arg h2 "$H2" --arg m2 "$M2" --arg ti "$1" --arg u "$2" \
    '{prs: {"7": {state: "MERGED", headRefOid: $h, mergeCommit: {oid: $m}, baseRefName: "main", headRefName: "gh7",
                  title: $ti, url: $u},
            "8": {state: "MERGED", headRefOid: $h2, mergeCommit: {oid: $m2}, baseRefName: "main", headRefName: "gh8",
                  title: "Notes", url: "https://github.com/o/r/pull/8"}}}' > "$GH_STORE"
}
lane() { # NAME PANE REPO ISSUE
  printf 'supervisor = "%s"\nrepository = "%s"\nissue = %s\ngoal = "g"\nstarted_at = "2026-10-29T00:00:00Z"\n' "$2" "$3" "$4" > "$lanes/$1.toml"
}
run() { # WANT ARGS...: the command, from the repo holding the merge, fakes first on PATH
  local want="$1" rc; shift
  set +e; out="$(PATH="$t/bin:$PATH" "$L" "$@" 2>"$t/err")"; rc=$?; set -e; err="$(cat "$t/err")"
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"
  ! grep -q Traceback <<<"$err" || fail "'$*' printed a traceback: $err"
  tell="$(grep '^step [0-9]* tell supervisors: ' <<<"$out")" || fail "'$*' printed no tell supervisors line: $out"
  last="$(tail -n1 <<<"$out")"
}
said() { cut -f1 "$SAY_LOG" 2>/dev/null | sort | tr '\n' ' '; }

store "Add foo" "https://github.com/o/r/pull/7"
lane gh7 w0:p1 o/r 7; lane live1 w1:p1 o/r 11; lane parked w2:p1 o/r 12; lane other w3:p1 x/y 13
printf '%s\n' w0:p1 w1:p1 w3:p1 > "$HERDR_LIVE"
echo '{"at": "2026-10-29T00:00:00+00:00", "kind": "prod", "issue": 11, "note": "earlier prod"}' > "$dlog"

# A live supervisor of the PR's repo gets one message; the merged lane, a parked one, another repo's: none.
run 0 post-merge 7 "$H" --lane gh7 --repo o/r --wait 0
[[ "$(said)" == "w1:p1 " ]] || fail "sent to $(said), want only w1:p1: $(cat "$SAY_LOG")"
want="main moved to ${M:0:12} (#7 Add foo); rule files changed: .agents/skills/foo/SKILL.md, agents/supervisor.md; re-read the changed ones before your next step."
[[ "$(cut -f2 "$SAY_LOG")" == "$want" ]] || fail "message: $(cut -f2 "$SAY_LOG")"
[[ "$tell" == *"told: live1 w1:p1"* && "$tell" == *"not woken: parked w2:p1"* ]] || fail "tell line: $tell"
[[ "$last" == *"tell supervisors ok" ]] || fail "summary: $last"
! grep -q 'agent get w3:p1' "$HERDR_LOG" || fail "another repo's lane was looked up: $(cat "$HERDR_LOG")"
# One prod line per lane told, canonical shape, after the director's own lines.
[[ "$(wc -l < "$dlog")" == 2 ]] || fail "director log: $(cat "$dlog")"
tail -n1 "$dlog" | jq -e --arg n "post-merge $M #7: main moved, told live1 to re-read .agents/skills/foo/SKILL.md, agents/supervisor.md" \
  '(keys == ["at", "issue", "kind", "note"]) and .kind == "prod" and .issue == 11 and .note == $n
   and (.at | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+\\+00:00$"))' >/dev/null || fail "prod line: $(tail -n1 "$dlog")"

# Rerun: the prod line names this merge for live1, so nothing new is sent or logged.
run 0 post-merge 7 "$H" --lane gh7 --repo o/r --wait 0
[[ "$(wc -l < "$SAY_LOG")" == 1 && "$(wc -l < "$dlog")" == 2 ]] || fail "rerun sent again: $(cat "$SAY_LOG") $(cat "$dlog")"
[[ "$tell" == *"already told: live1"* && "$tell" == *"not woken: parked w2:p1"* ]] || fail "rerun tell line: $tell"

# A merge touching no rule file: "none", and a new merge is told again.
run 0 post-merge 8 "$H2" --lane gh7 --repo o/r --wait 0
[[ "$(tail -n1 "$SAY_LOG" | cut -f2)" == "main moved to ${M2:0:12} (#8 Notes); rule files changed: none; re-read the changed ones before your next step." ]] \
  || fail "no rule files: $(tail -n1 "$SAY_LOG")"
tail -n1 "$dlog" | jq -e --arg n "post-merge $M2 #8: main moved, told live1 to re-read none" '.note == $n' >/dev/null || fail "none prod: $(tail -n1 "$dlog")"

# A kit PR: every lane runs kit roles, so another repo's live lane is told too.
kitrepo="$(git -C "$kit" remote get-url origin | sed -E 's#^.*github\.com[:/]##; s#\.git$##')"
store "Kit rule" "https://github.com/$kitrepo/pull/7"; : > "$SAY_LOG"; : > "$dlog"
run 0 post-merge 7 "$H" --lane gh7 --repo "$kitrepo" --wait 0
[[ "$(said)" == "w1:p1 w3:p1 " ]] || fail "kit PR sent to $(said), want w1:p1 w3:p1"
[[ "$(jq -r .issue "$dlog" | sort | tr '\n' ' ')" == "11 13 " ]] || fail "kit PR prod lines: $(cat "$dlog")"

# A failed send: named, no prod line for it, the rest still tried, the step stops (exit 1).
store "Add foo" "https://github.com/o/r/pull/7"; : > "$SAY_LOG"; : > "$dlog"
lane live2 w4:p1 o/r 14; echo w4:p1 >> "$HERDR_LIVE"; echo "w1:p1 75" > "$SAY_RC"
run 1 post-merge 7 "$H" --lane gh7 --repo o/r --wait 0
[[ "$(said)" == "w1:p1 w4:p1 " ]] || fail "failed send: tried $(said)"
[[ "$tell" == *"stopped: "*"herdr-say failed: live1 w1:p1 exit 75"* && "$tell" == *"told: live2 w4:p1"* ]] || fail "failed send line: $tell"
[[ "$(jq -r .issue "$dlog")" == 14 ]] || fail "failed send prod lines: $(cat "$dlog")"
[[ "$last" == *"tell supervisors stopped"* ]] || fail "failed send summary: $last"
rm "$SAY_RC"; run 0 post-merge 7 "$H" --lane gh7 --repo o/r --wait 0   # rerun tells only the one that failed
[[ "$(said)" == "w1:p1 w1:p1 w4:p1 " && "$(jq -r .issue "$dlog" | tr '\n' ' ')" == "14 11 " ]] || fail "retry: $(said) $(cat "$dlog")"
echo "lane-post-merge-tell: ok (live told once with merge, PR, title, rule files; merged lane, parked, other repo not sent;" \
  "kit PR tells every lane; one prod line per lane told; rerun sends nothing new; failed send named, no prod line, exit 1)"
