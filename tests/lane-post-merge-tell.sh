#!/usr/bin/env bash
# Integration test for octo-feather-lane post-merge step 4, tell supervisors (owner ruling 2026-10-29 on issue
# 206; issue 398), offline: a throwaway git repo holds the merge commit, a fake gh PR #7 merged there with a
# green push run, a fake herdr whose `agent get` finds only the live panes, a fake herdr-say that logs each send,
# a throwaway state dir (XDG_STATE_HOME) holding the lane records and the director log, and a throwaway kit
# install clone (OCTO_FEATHER_KIT_INSTALL, always set: never the live kit) whose origin is o/kit, so step 3 leaves
# it unchanged on an o/r PR and refreshes it with fake mise, just, uv and pnpm on an o/kit PR. A live supervisor of
# the PR's repo gets one message naming the merge commit, PR, title and changed rule files; the --lane lane and a
# lane of another repo get none (unless the PR is the kit's own); a parked one (its latest parked line names its
# pane) is listed not woken and a gone one (no such line, or one naming an older pane) listed gone, neither sent to
# nor stopping the step (owner ruling on issue 206, step 4; issue 458); any other herdr failure stops it. Each lane
# told gets one prod line in the director log, and a rerun sends nothing new. A failed send is named, writes no
# prod line, and stops the step after the rest are tried. Step 5 finds the lane unarchived: pending, exit 3; once
# archived its teardown runs, Herdr's workspace_not_found on stderr read as already closed. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-post-merge-tell test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" OCTO_FEATHER_KIT_INSTALL="$t/kit" GH_STORE="$t/gh.json" HERDR_LOG="$t/herdr.log" SAY_LOG="$t/say.log" \
  HERDR_LIVE="$t/live" HERDR_BROKEN="$t/broken" SAY_RC="$t/say.rc" GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
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
# The kit install: a clone of this repo at main, origin named o/kit (fetched from the local repo).
git clone -q "$r" "$t/kit"; git -C "$t/kit" remote set-url origin https://github.com/o/kit.git
git -C "$t/kit" config "url.$r.insteadOf" https://github.com/o/kit.git

cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]; db = json.load(open(os.environ["GH_STORE"]))
def opt(f): return a[a.index(f) + 1] if f in a else None
if a[:2] == ["pr", "view"] and a[2] in db["prs"]:
    print(json.dumps({k: db["prs"][a[2]][k] for k in opt("--json").split(",")})); sys.exit(0)
if a[:2] == ["repo", "view"] and opt("--json") == "nameWithOwner":
    print(json.dumps({"nameWithOwner": a[2].removeprefix("https://github.com/").removesuffix(".git")})); sys.exit(0)
if a[:2] == ["pr", "list"] and opt("--base"):
    print("[]"); sys.exit(0)
if a[:2] == ["run", "list"]:
    print(json.dumps([{"databaseId": 1, "status": "completed", "conclusion": "success", "workflowName": "check",
                       "url": "https://github.com/o/r/actions/runs/1"}])); sys.exit(0)
print(f"fake gh: refused {' '.join(a)}", file=sys.stderr); sys.exit(1)
EOF
# Fake herdr: `agent get PANE` finds only the panes listed in $HERDR_LIVE, `workspace get SPACE` no space. It prints
# exactly as real herdr 0.9.5 `agent get` / `workspace get` (captured 2026-10-30, ticket #458 comment): found, the
# result JSON on stdout, exit 0; not found, the error JSON on stderr, empty stdout, exit 1. A pane in $HERDR_BROKEN
# stands for any other herdr failure (plain text on stderr, exit 1); anything else is refused.
cat > "$t/bin/herdr" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "$HERDR_LOG"
[[ "$1 $2" == "workspace get" ]] \
  && { echo '{"error":{"code":"workspace_not_found","message":"workspace '"$3"' not found"},"id":"cli:workspace:get"}' >&2; exit 1; }
[[ "$1 $2" == "agent get" ]] || { echo "fake herdr: refused $*" >&2; exit 1; }
! grep -qxF "$3" "$HERDR_BROKEN" 2>/dev/null || { echo "herdr: server not reachable" >&2; exit 1; }
grep -qxF "$3" "$HERDR_LIVE" 2>/dev/null \
  || { echo '{"error":{"code":"agent_not_found","message":"agent target '"$3"' not found"},"id":"cli:agent:get"}' >&2; exit 1; }
printf '{"id":"cli:agent:get","result":{"agent":{"agent":"pi","agent_status":"working","cwd":"/tmp/fixture","focused":false,"foreground_cwd":"/tmp/fixture","interactive_ready":true,"name":"fixture","pane_id":"%s","revision":2,"state_change_seq":7969,"tab_id":"%s:t1","terminal_id":"term_fixture","terminal_title":"π - fixture","terminal_title_stripped":"π - fixture","workspace_id":"%s"},"type":"agent_info"}}\n' "$3" "${3%%:*}" "${3%%:*}"
EOF
# Fake herdr-close (step 5): its target is gone already, as herdr-close reports a space it cannot close.
printf '#!/bin/sh\necho "space=$1 space_close_rc=1 killed=0"; exit 1\n' > "$t/bin/herdr-close"
# Fake herdr-say: logs "PANE<TAB>MESSAGE"; exits the code $SAY_RC names for the pane ("PANE RC" lines), else 0.
cat > "$t/bin/herdr-say" <<'EOF'
#!/usr/bin/env bash
printf '%s\t%s\n' "$1" "$2" >> "$SAY_LOG"
rc="$(awk -v p="$1" '$1 == p {print $2}' "$SAY_RC" 2>/dev/null)"
[[ "${rc:-0}" == 0 ]] || echo "herdr-say: $1 is blocked on interactive input; not delivered" >&2
exit "${rc:-0}"
EOF
printf '#!/bin/sh\nexit 0\n' > "$t/bin/tool"; for x in mise just uv pnpm; do ln -s tool "$t/bin/$x"; done   # step 3's refresh
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
parked() { # LANE PANE AT: a parked line in the lane's hand-off log
  printf '{"at": "%s", "kind": "parked", "pane": "%s", "name": "%s"}\n' "$3" "$2" "$1" >> "$lanes/$1.handoffs.jsonl"
}

store "Add foo" "https://github.com/o/r/pull/7"
lane gh7 w0:p1 o/r 7; lane live1 w1:p1 o/r 11; lane parked w2:p1 o/r 12; lane other w3:p1 x/y 13
parked parked w2:p0 2026-10-28T00:00:00Z; parked parked w2:p1 2026-10-29T00:00:00Z
printf '%s\n' w0:p1 w1:p1 w3:p1 > "$HERDR_LIVE"
echo '{"at": "2026-10-29T00:00:00+00:00", "kind": "prod", "issue": 11, "note": "earlier prod"}' > "$dlog"

# A live supervisor of the PR's repo gets one message; the merged lane, a parked one, another repo's: none.
run 3 post-merge 7 "$H" --lane gh7 --repo o/r --wait 0
[[ "$(said)" == "w1:p1 " ]] || fail "sent to $(said), want only w1:p1: $(cat "$SAY_LOG")"
want="main moved to ${M:0:12} (#7 Add foo); rule files changed: .agents/skills/foo/SKILL.md, agents/supervisor.md; re-read the changed ones before your next step."
[[ "$(cut -f2 "$SAY_LOG")" == "$want" ]] || fail "message: $(cut -f2 "$SAY_LOG")"
[[ "$tell" == *"told: live1 w1:p1"* && "$tell" == *"not woken: parked w2:p1; gone: director to resume or archive: none" ]] || fail "tell line: $tell"
[[ "$last" == *"tell supervisors ok; step 5 teardown pending" ]] || fail "summary: $last"
! grep -q 'agent get w3:p1' "$HERDR_LOG" || fail "another repo's lane was looked up: $(cat "$HERDR_LOG")"
# One prod line per lane told, canonical shape, after the director's own lines.
[[ "$(wc -l < "$dlog")" == 2 ]] || fail "director log: $(cat "$dlog")"
tail -n1 "$dlog" | jq -e --arg n "post-merge $M #7: main moved, told live1 to re-read .agents/skills/foo/SKILL.md, agents/supervisor.md" \
  '(keys == ["at", "issue", "kind", "note"]) and .kind == "prod" and .issue == 11 and .note == $n
   and (.at | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+\\+00:00$"))' >/dev/null || fail "prod line: $(tail -n1 "$dlog")"

# Rerun: the prod line names this merge for live1, so nothing new is sent or logged.
run 3 post-merge 7 "$H" --lane gh7 --repo o/r --wait 0
[[ "$(wc -l < "$SAY_LOG")" == 1 && "$(wc -l < "$dlog")" == 2 ]] || fail "rerun sent again: $(cat "$SAY_LOG") $(cat "$dlog")"
[[ "$tell" == *"already told: live1"* && "$tell" == *"not woken: parked w2:p1"* ]] || fail "rerun tell line: $tell"

# A merge touching no rule file: "none", and a new merge is told again.
run 3 post-merge 8 "$H2" --lane gh7 --repo o/r --wait 0
[[ "$(tail -n1 "$SAY_LOG" | cut -f2)" == "main moved to ${M2:0:12} (#8 Notes); rule files changed: none; re-read the changed ones before your next step." ]] \
  || fail "no rule files: $(tail -n1 "$SAY_LOG")"
tail -n1 "$dlog" | jq -e --arg n "post-merge $M2 #8: main moved, told live1 to re-read none" '.note == $n' >/dev/null || fail "none prod: $(tail -n1 "$dlog")"

# A kit PR: every lane runs kit roles, so another repo's live lane is told too.
kitrepo=o/kit
store "Kit rule" "https://github.com/$kitrepo/pull/7"; : > "$SAY_LOG"; : > "$dlog"
run 3 post-merge 7 "$H" --lane gh7 --repo "$kitrepo" --wait 0
[[ "$(said)" == "w1:p1 w3:p1 " ]] || fail "kit PR sent to $(said), want w1:p1 w3:p1: $out"
[[ "$(jq -r .issue "$dlog" | sort | tr '\n' ' ')" == "11 13 " ]] || fail "kit PR prod lines: $(cat "$dlog")"

# A failed send: named, no prod line for it, the rest still tried, the step stops (exit 1).
store "Add foo" "https://github.com/o/r/pull/7"; : > "$SAY_LOG"; : > "$dlog"
lane live2 w4:p1 o/r 14; echo w4:p1 >> "$HERDR_LIVE"; echo "w1:p1 75" > "$SAY_RC"
run 1 post-merge 7 "$H" --lane gh7 --repo o/r --wait 0
[[ "$(said)" == "w1:p1 w4:p1 " ]] || fail "failed send: tried $(said)"
[[ "$tell" == *"stopped: "*"herdr-say failed: live1 w1:p1 exit 75"* && "$tell" == *"told: live2 w4:p1"* ]] || fail "failed send line: $tell"
[[ "$(jq -r .issue "$dlog")" == 14 ]] || fail "failed send prod lines: $(cat "$dlog")"
[[ "$last" == *"tell supervisors stopped"* ]] || fail "failed send summary: $last"
rm "$SAY_RC"; run 3 post-merge 7 "$H" --lane gh7 --repo o/r --wait 0   # rerun tells only the one that failed
[[ "$(said)" == "w1:p1 w1:p1 w4:p1 " && "$(jq -r .issue "$dlog" | tr '\n' ' ')" == "14 11 " ]] || fail "retry: $(said) $(cat "$dlog")"

# Demo (issue 458): --lane gh1 with a live, a parked and a gone lane (one never parked, one whose latest parked line
# names an older pane): only the live one told, the rest listed, step 4 ok, step 5 reached (pending: not archived).
rm -f "$lanes"/*; : > "$SAY_LOG"; : > "$dlog"; : > "$HERDR_LOG"; printf '%s\n' w1:p1 > "$HERDR_LIVE"
lane live1 w1:p1 o/r 11; lane parked w2:p1 o/r 12; lane gone w5:p1 o/r 15; lane moved w6:p1 o/r 16
parked parked w2:p1 2026-10-29T00:00:00Z; parked moved w6:p1 2026-10-28T00:00:00Z; parked moved w6:p0 2026-10-29T00:00:00Z
run 3 post-merge 7 "$H" --lane gh1 --repo o/r --wait 0
[[ "$(said)" == "w1:p1 " ]] || fail "demo sent to $(said), want only w1:p1"
[[ "$tell" == "step 4 tell supervisors: ok: "*"told: live1 w1:p1; already told: none; not woken: parked w2:p1; gone: director to resume or archive: gone w5:p1, moved w6:p1" ]] \
  || fail "demo tell line: $tell"
grep -qx "step 5 teardown: pending: lane gh1 not archived; rerun on its close report" <<<"$out" || fail "demo step 5: $out"
# Archived: step 5 runs; herdr-close fails and Herdr's workspace_not_found (stderr) reads as already closed.
mkdir -p "$lanes/archive"; echo 'pane = "w0:p9"' > "$t/state/octo-feather/director.toml"; git remote add origin "$r"
printf 'supervisor = "w9:p1"\nrepository = "o/r"\nissue = 1\npr = 7\ngoal = "g"\nstarted_at = "2026-10-29T00:00:00Z"\n' > "$lanes/archive/gh1.toml"
run 0 post-merge 7 "$H" --lane gh1 --repo o/r --wait 0
grep -qx "step 5 teardown: ok: space w9 already closed; worktree of gh1 already removed; no open PR based on gh1; local branch gh1 already deleted; remote branch gh1 already deleted from origin" <<<"$out" \
  || fail "demo teardown: $out"
grep -qx "workspace get w9" "$HERDR_LOG" || fail "demo teardown asked no workspace get: $(cat "$HERDR_LOG")"

# Any other herdr failure still stops step 4, named; the other lanes are still handled.
rm "$lanes/archive/gh1.toml"; echo w2:p1 > "$HERDR_BROKEN"
run 1 post-merge 7 "$H" --lane gh1 --repo o/r --wait 0
[[ "$tell" == "step 4 tell supervisors: stopped: parked w2:p1: herdr agent get w2:p1 failed (herdr: server not reachable)"*"gone: director to resume or archive: gone w5:p1, moved w6:p1" ]] \
  || fail "broken herdr: $tell"
echo "lane-post-merge-tell: ok (live told once with merge, PR, title, rule files; merged lane, parked, other repo not sent;" \
  "kit PR tells every lane; one prod line per lane told; rerun sends nothing new; failed send named, no prod line, exit 1;" \
  "parked and gone listed, step 4 ok, step 5 reached, teardown reads stderr; other herdr failure stops)"
