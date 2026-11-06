#!/usr/bin/env bash
# Integration test for herdr-spawn and pi-role vs Pi's project trust dialog
# (issue #3), and for resuming a parked agent through herdr-say (issue #9):
# drives herdr-spawn's CLI with a fake herdr first on PATH
# (tests/fixtures/herdr-spawn/), pi-role headless with a fake pi, and
# herdr-say and octo-feather-start with tests/fixtures/herdr-say/. No real
# herdr, pi or state dir. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
ident() { XDG_STATE_HOME="$1" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null; }   # the commit identity a role launch needs (#665)
export XDG_STATE_HOME="$t/state"; ident "$t/state"
mkdir -p "$t/bin" "$t/cwd" "$t/cache"
# mise's state its own, also run bare outside the gate: mise in $t/cwd's mise.toml records it there, never in the caller's (#664).
export MISE_STATE_DIR="$t/mise-state"
cp "$kit/tests/fixtures/herdr-spawn/"* "$t/bin/"
chmod +x "$t/bin/herdr"
fail() { echo "herdr-spawn test: $*" >&2; exit 1; }
# A failing-read case is vacuous unless herdr-spawn read up to the armed
# boundary: fewer reads than READS_OK means the failing read was never reachable.
# Reads past it must be recorded failures (the fake's failed-reads).
armed() { # $1: case dir, $2: READS_OK
  local r f=0; r="$(wc -l <"$t/$1/reads")"
  [[ ! -f "$t/$1/failed-reads" ]] || f="$(wc -l <"$t/$1/failed-reads")"
  ((r >= $2)) || fail "$1: $r pane reads < READS_OK=$2; the failing read was never reached, so this case proves nothing"
  ((r == $2 || f >= 1)) || fail "$1: $r reads past READS_OK=$2 but no failed read recorded"
}

spawn() { # $1: case dir; rest: env assignments
  local c="$t/$1"; shift; mkdir -p "$c"; rc=0
  env FAKE_HERDR_DIR="$c" PATH="$t/bin:$PATH" XDG_CACHE_HOME="$t/cache" HERDR_PANE_ID=w9:p0 \
    HERDR_SPAWN_TRUST_RETRIES=3 HERDR_SPAWN_READY_RETRIES=2 "$@" \
    "$kit/.agents/skills/herdr-comms/assets/herdr-spawn" --workspace w9 --name t1 --role implementer \
    --cwd "$t/cwd" >"$c/out" 2>"$c/err" || rc=$?
}

# 1. A plain spawn launches Pi with --approve, so no dialog opens and it succeeds.
spawn ok
grep -qx -- --approve "$t/ok/start-argv" || fail "agent start argv lacks --approve: $(tr '\n' ' ' <"$t/ok/start-argv")"
# The implementer lists web: its tab gets the kit's web list, not --no-mcp (#262, roles#launch-web).
for f in --no-skills --octo-feather-web-servers; do grep -qx -- "$f" "$t/ok/start-argv" || fail "pi-role --json args lost $f beside --approve"; done
[[ "$rc" == 0 ]] || fail "spawn exited $rc: $(cat "$t/ok/err")"
grep -q 'tab=w9:t1 pane=w9:p1' "$t/ok/out" || fail "spawn printed no tab and pane: $(cat "$t/ok/out")"
[[ ! -s "$t/ok/keys" ]] || fail "keys sent to a ready pane: $(cat "$t/ok/keys")"

# 1b. pi-role runs in --cwd, not the caller's directory: the tracker skill is the target's
#     (spec skills#tracker). A caller in a jira target spawning into $t/cwd (no config) gets
#     github-issues; spawning into the jira target from $t/cwd is refused before any tab.
mkdir -p "$t/jira"; git -C "$t/jira" init -q; echo 'tracker = "jira"' > "$t/jira/.octo-feather.toml"
spawn_from() { # $1: case dir, $2: caller dir, $3: --cwd
  local c="$t/$1"; mkdir -p "$c"; rc=0
  (cd "$2" && env FAKE_HERDR_DIR="$c" PATH="$t/bin:$PATH" XDG_CACHE_HOME="$t/cache" HERDR_PANE_ID=w9:p0 \
    HERDR_SPAWN_TRUST_RETRIES=3 HERDR_SPAWN_READY_RETRIES=2 \
    "$kit/.agents/skills/herdr-comms/assets/herdr-spawn" --workspace w9 --name t1 --role implementer \
    --cwd "$3" >"$c/out" 2>"$c/err") || rc=$?
}
spawn_from cwd-target "$t/jira" "$t/cwd"
[[ "$rc" == 0 ]] || fail "spawn into a no-config target from a jira caller: exit $rc: $(cat "$t/cwd-target/err")"
grep -q '/github-issues$' "$t/cwd-target/start-argv" || fail "spawn into a no-config target lacks github-issues: $(tr '\n' ' ' <"$t/cwd-target/start-argv")"
spawn_from cwd-jira "$t/cwd" "$t/jira"
[[ "$rc" == 65 ]] && grep -q "unknown tracker 'jira'" "$t/cwd-jira/err" || fail "spawn into a jira target: exit $rc: $(cat "$t/cwd-jira/err")"
[[ ! -s "$t/cwd-jira/start-argv" ]] || fail "spawn into a jira target started an agent"

# 1c. remote#acceptance-linear-key-panes: LINEAR_API_KEY set in the caller reaches the tab's env (the fake
#     herdr's tab-env), no file the spawn writes (home, state, cache, worktree) holds it, and a ticket filed
#     from that env through the linear skill's issue-create reaches the fake linear, which takes it only
#     with the key. Unset in the caller: not set in the tab.
key="lin-test-$(od -An -N8 -tx8 /dev/urandom | tr -d ' ')"
lk="$t/lk"; mkdir -p "$lk/home" "$lk/state" "$lk/lbin"; ident "$lk/state"
spawn key LINEAR_API_KEY="$key" HOME="$lk/home" XDG_STATE_HOME="$lk/state"
[[ "$rc" == 0 ]] || fail "spawn with LINEAR_API_KEY: exit $rc: $(cat "$t/key/err")"
grep -qxF "LINEAR_API_KEY=$key" "$t/key/tab-env" || fail "tab env lacks LINEAR_API_KEY: $(cut -d= -f1 "$t/key/tab-env" | tr '\n' ' ')"
hits="$(grep -rlF -- "$key" "$lk" "$t/cache" "$t/cwd" "$t/key/out" "$t/key/err" 2>/dev/null || true)"
[[ -z "$hits" ]] || fail "files written by the spawn hold the Linear key: $hits"
printf '#!/usr/bin/env bash\n[[ "${LINEAR_API_KEY:-}" == %q ]] || { echo "linear: no API key" >&2; exit 1; }\nexec %q "$@"\n' \
  "$key" "$kit/.agents/skills/linear/scripts/linear" >"$t/key/linear"; chmod +x "$t/key/linear"
echo '{"workspace": "acme", "default_team": "ENG", "issues": {}}' >"$t/key/store.json"
mapfile -t tabenv <"$t/key/tab-env"
filed="$(echo body | env -i "${tabenv[@]}" PATH="$t/key:$(sed -n 's/^PATH=//p' "$t/key/tab-env")" \
  OCTO_FEATHER_LINEAR_STORE="$t/key/store.json" "$kit/.agents/skills/linear/scripts/issue-create" --title T --body-file -)" \
  || fail "issue-create from the tab env failed"
[[ "$filed" == ENG-1 && "$(jq -r '.issues["ENG-1"].title' "$t/key/store.json")" == T ]] || fail "ticket did not reach the fake linear: $filed"
unset LINEAR_API_KEY; spawn nokey
[[ "$rc" == 0 ]] || fail "spawn without LINEAR_API_KEY: exit $rc: $(cat "$t/nokey/err")"
! grep -q '^LINEAR_API_KEY=' "$t/nokey/tab-env" || fail "LINEAR_API_KEY set in a tab whose caller had none"
# 1d. #261: in a repo with its own mise.toml the tab's PATH is the kit dirs, then the caller's PATH with mise's
#     shims dir (as pi-role reports it, "path") just before its first system dir; in a repo without one (the cases
#     above: a repo the kit did not create) or with no mise on PATH, the caller's PATH as it was.
shims="$(mise doctor --json | jq -r .dirs.shims)"
kitpath="$kit/.agents/skills/herdr-comms/assets:$kit/scripts"; ub="$HOME/.local/bin"   # ub: the fallback, last
grep -qxF "PATH=$kitpath:$t/bin:$PATH:$ub" "$t/ok/tab-env" || fail "tab PATH in a repo without mise.toml changed: $(grep ^PATH= "$t/ok/tab-env")"
mkdir -p "$t/mbin"; ln -sf "$(command -v mise)" "$t/mbin/mise"; ln -sf "$(command -v jq)" "$t/mbin/jq"
printf '[tools]\n' >"$t/cwd/mise.toml"
spawn made PATH="$t/bin:$t/mbin:/usr/local/bin:/usr/bin:/bin"
[[ "$rc" == 0 ]] || fail "spawn in a mise.toml repo: exit $rc: $(cat "$t/made/err")"
grep -qxF "PATH=$kitpath:$t/bin:$t/mbin:$shims:/usr/local/bin:/usr/bin:/bin:$ub" "$t/made/tab-env" \
  || fail "tab PATH in a mise.toml repo lacks mise's shims $shims before the system dirs, after the caller's: $(grep ^PATH= "$t/made/tab-env")"
spawn nomise PATH="$t/bin:/usr/bin:/bin"
[[ "$rc" == 0 ]] || fail "spawn without mise: exit $rc: $(cat "$t/nomise/err")"
grep -qxF "PATH=$kitpath:$t/bin:/usr/bin:/bin:$ub" "$t/nomise/tab-env" || fail "tab PATH without mise changed: $(grep ^PATH= "$t/nomise/tab-env")"
rm "$t/cwd/mise.toml"
# 1e. Owner ruling #261 (#437): a stub pi first on the caller's PATH beats the box's pi in ~/.local/bin in the tab's
#     PATH (a fake one under a throwaway HOME); a tool only ~/.local/bin holds is still found there (its fallback).
#     Resolved only (`command -v`), never run.
uh="$t/uh"; mkdir -p "$uh/.local/bin" "$t/stub"
for b in pi only-home; do printf '#!/bin/sh\necho "home %s"\n' "$b" >"$uh/.local/bin/$b"; chmod +x "$uh/.local/bin/$b"; done
printf '#!/bin/sh\necho "stub pi"\n' >"$t/stub/pi"; chmod +x "$t/stub/pi"
for mt in "" mise; do   # without and with a mise.toml (pi-role's "path")
  [[ -z "$mt" ]] || printf '[tools]\n' >"$t/cwd/mise.toml"
  spawn "stub$mt" HOME="$uh" PATH="$t/bin:$t/stub:$t/mbin:/usr/bin:/bin"
  [[ "$rc" == 0 ]] || fail "spawn with a stub pi${mt:+ in a mise.toml repo}: exit $rc: $(cat "$t/stub$mt/err")"
  tp="$(sed -n 's/^PATH=//p' "$t/stub$mt/tab-env")"
  [[ "$(PATH="$tp" command -v pi)" == "$t/stub/pi" ]] || fail "tab PATH${mt:+ (mise.toml)} finds pi at $(PATH="$tp" command -v pi), not the caller's stub: $tp"
  [[ "$(PATH="$tp" command -v only-home)" == "$uh/.local/bin/only-home" ]] || fail "tab PATH${mt:+ (mise.toml)} lost the ~/.local/bin fallback: $tp"
  rm -f "$t/cwd/mise.toml"
done

# 2. A trust dialog that opens anyway is never answered: exit 69, zero keys,
#    tab closed, pane text on stderr.
spawn dialog FAKE_HERDR_FORCE_DIALOG=1
[[ "$rc" == 69 ]] || fail "forced dialog: exit $rc, want 69: $(cat "$t/dialog/err")"
[[ ! -s "$t/dialog/keys" ]] || fail "forced dialog: keys sent: $(tr '\n' ' ' <"$t/dialog/keys")"
grep -qx 'w9:t1' "$t/dialog/closed" 2>/dev/null || fail "forced dialog: tab not closed"
grep -q 'Trust project folder?' "$t/dialog/err" || fail "forced dialog: pane text not on stderr: $(cat "$t/dialog/err")"

# 2b. Same when the pane read fails after the detecting read: the report shows
#     the text already read, and close and 69 still run.
spawn dialog-readfail FAKE_HERDR_FORCE_DIALOG=1 FAKE_HERDR_READS_OK=1
armed dialog-readfail 1
[[ "$rc" == 69 ]] || fail "dialog then failed read: exit $rc, want 69: $(cat "$t/dialog-readfail/err")"
[[ ! -s "$t/dialog-readfail/keys" ]] || fail "dialog then failed read: keys sent"
grep -qx 'w9:t1' "$t/dialog-readfail/closed" 2>/dev/null || fail "dialog then failed read: tab not closed"
grep -q 'Trust project folder?' "$t/dialog-readfail/err" || fail "dialog then failed read: detected text not on stderr"

# 2c. The "did not clear" path (a non-Pi dialog that stays open) keeps the same
#     guarantee when the pane read fails after the last detecting read.
spawn stuck FAKE_HERDR_FORCE_DIALOG=other HERDR_SPAWN_TRUST_RETRIES=1 FAKE_HERDR_READS_OK=4
armed stuck 4
[[ "$rc" == 69 ]] || fail "stuck dialog then failed read: exit $rc, want 69: $(cat "$t/stuck/err")"
grep -qx 'w9:t1' "$t/stuck/closed" 2>/dev/null || fail "stuck dialog then failed read: tab not closed"
grep -q 'Quick safety check' "$t/stuck/err" || fail "stuck dialog then failed read: detected text not on stderr"

# 3. Headless pi-role passes --approve too (fake pi records its argv).
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$@" >"%s/pi-argv"\n' "$t" >"$t/bin/pi"; chmod +x "$t/bin/pi"
(cd "$t/cwd" && PATH="$t/bin:$PATH" "$kit/scripts/pi-role" "$kit/agents/implementer.md" -p brief)
grep -qx -- --approve "$t/pi-argv" || fail "headless pi-role argv lacks --approve"

# 4. Resuming a parked agent through herdr-say (comms spec #roles-park,
#    #acceptance-resume-live-space), with the fake herdr in
#    tests/fixtures/herdr-say/ and a temp state dir per case.
mkdir -p "$t/sbin"
cp "$kit/tests/fixtures/herdr-say/herdr" "$t/sbin/"; chmod +x "$t/sbin/herdr"

# One case: a fresh fake herdr, workspaces $2 ("LABEL ID" lines), a lane gh2
# hand-off log holding parked line $3. The caller is the director in w2.
setup() { # $1: case, $2: spaces, $3: parked line
  c="$t/$1"; mkdir -p "$c/state/octo-feather/lanes"; ident "$c/state"
  printf '%s' "$2" >"$c/spaces"
  printf '%s\n' "$3" >"$c/state/octo-feather/lanes/gh2.handoffs.jsonl"
}
run() { # rest: command and args, run in the case
  rc=0
  env -u OCTO_FEATHER_ROLE -u OCTO_FEATHER_PARENT -u OCTO_FEATHER_OPERATING_MODEL -u HERDR_SESSION \
    FAKE_HERDR_DIR="$c" PATH="$t/sbin:$PATH" XDG_STATE_HOME="$c/state" \
    HERDR_PANE_ID=w2:p1 HERDR_WORKSPACE_ID="${space:-w2}" \
    HERDR_SPAWN_TRUST_RETRIES=1 HERDR_SPAWN_READY_RETRIES=2 \
    "$@" >"$c/out" 2>"$c/err" || rc=$?
}
say() { run "$kit/.agents/skills/herdr-comms/assets/herdr-say" "$@"; }
sup="{\"at\":\"2026-10-20T00:00:00Z\",\"kind\":\"parked\",\"pane\":\"w5:p1\",\"cwd\":\"$t/cwd\",\"session\":\"S1\",\"parent\":\"w2:p1\"}"
delivered() { # $1: pane. The message that pane got.
  awk -F'\t' -v p="$1" '$1 == p {print $2}' "$c/prompts" 2>/dev/null
}

# 4a. Live space (#acceptance-resume-live-space): the lane workspace gh2 (w5)
#    still holds a worker tab. The supervisor resumes in a new tab of w5, no 73.
setup live "gh2 w5"$'\n' "$sup"
printf 'unrelated corrupt log\n' >"$c/state/octo-feather/lanes/other.handoffs.jsonl"
say --parked gh2
[[ "$rc" == 0 ]] || fail "parked gh2: exit $rc: $(cat "$c/err")"
jq -e '.session == "S1" and .name == "gh2"' "$c/out" >/dev/null || fail "parked gh2: lost session"
grep -q 'other.handoffs.jsonl:1:' "$c/err" || fail "parked gh2: no corruption diagnostic"
printf 'herdr-say --parked gh2: %s\n' "$(cat "$c/out")"
printf 'diagnostic: %s\n' "$(cat "$c/err")"
say gh2 hello
[[ "$rc" == 0 ]] || fail "resume: live space: herdr-say exit $rc, want 0: $(cat "$c/err")"
grep -q '^workspace create' "$c/argv" && fail "resume: live space: a new workspace was created: $(cat "$c/argv")"
grep -q '^tab create --workspace w5 ' "$c/argv" || fail "resume: live space: no tab created in w5: $(cat "$c/argv")"
grep -qx 'gh2 w5:p9' "$c/agents" || fail "resume: live space: supervisor gh2 not started in w5: $(cat "$c/agents")"
grep -qx 'pane=w5:p9' "$c/out" || fail "resume: live space: new pane not printed: $(cat "$c/out")"
[[ "$(delivered w5:p9)" == "Resumed from park as pane=w5:p9. hello" ]] ||
  fail "resume: live space: delivered '$(delivered w5:p9)', want the resume notice naming w5:p9"
[[ ! -s "$c/closed" ]] || fail "resume: live space: tabs closed in the live workspace: $(cat "$c/closed")"
grep -q -- '--session-id S1' "$c/argv" || fail "resume: supervisor lost original session"
printf 'herdr-say gh2 hello: %s; delivered=%s; session=S1\n' "$(cat "$c/out")" "$(delivered w5:p9)"

# 4b. Space gone (#roles-park): resume opens a new lane workspace gh2 and closes
#    only its seed tab.
setup gone "" "$sup"
say w5:p1 hello
[[ "$rc" == 0 ]] || fail "resume: space gone: herdr-say exit $rc, want 0: $(cat "$c/err")"
grep -q '^workspace create --label gh2 ' "$c/argv" || fail "resume: space gone: no lane workspace gh2 created: $(cat "$c/argv")"
grep -qx 'gh2 w8:p9' "$c/agents" || fail "resume: space gone: supervisor gh2 not started in w8: $(cat "$c/agents")"
grep -qx 'w8:t1' "$c/closed" || fail "resume: space gone: seed tab w8:t1 not closed"
[[ "$(delivered w8:p9)" == "Resumed from park as pane=w8:p9. hello" ]] ||
  fail "resume: space gone: delivered '$(delivered w8:p9)', want the resume notice naming w8:p9"

# 4c. A parked worker resumes in the caller's space, told it was resumed.
setup worker "gh2 w5"$'\n' "{\"at\":\"2026-10-20T00:00:00Z\",\"kind\":\"parked\",\"pane\":\"w5:p3\",\"name\":\"impl1\",\"label\":\"impl1\",\"role\":\"implementer\",\"cwd\":\"$t/cwd\",\"session\":\"S2\",\"parent\":\"w5:p1\"}"
space=w5 say impl1 "go on"
[[ "$rc" == 0 ]] || fail "resume: worker: herdr-say exit $rc, want 0: $(cat "$c/err")"
grep -qx 'impl1 w5:p9' "$c/agents" || fail "resume: worker: impl1 not started in w5: $(cat "$c/agents")"
[[ "$(delivered w5:p9)" == "Resumed from park as pane=w5:p9. go on" ]] ||
  fail "resume: worker: delivered '$(delivered w5:p9)', want the resume notice naming w5:p9"

# 4d. A live agent gets the message plain: no resume, no notice.
setup plain "gh2 w5"$'\n' "$sup"
echo "gh2 w5:p1" >"$c/agents"
say w5:p1 hello
[[ "$rc" == 0 && "$(delivered w5:p1)" == hello ]] || fail "resume: live agent: exit $rc, delivered '$(delivered w5:p1)', want plain hello"
grep -q '^tab create' "$c/argv" && fail "resume: live agent: a tab was created"

# 4e. A fresh start (no --resume) on an existing workspace still refuses with 73.
setup fresh "gh2 w5"$'\n' "$sup"
run "$kit/scripts/octo-feather-start" --issue 2 --cwd "$t/cwd"
[[ "$rc" == 73 ]] || fail "resume: fresh start on existing gh2: exit $rc, want 73: $(cat "$c/err")"
grep -qE '^(tab|workspace) create' "$c/argv" && fail "resume: fresh start on existing gh2: created a tab or workspace"

echo "herdr-spawn: ok (pane and headless launch carry --approve; pi-role runs in --cwd (its tracker, not the caller's); LINEAR_API_KEY reaches the tab only from the caller's env, mise's shims before the system dirs on the tab's PATH in a mise.toml repo (none elsewhere or without mise), the caller's stub pi before ~/.local/bin's (its fallback, last), in no written file, files a ticket in the fake linear; Pi trust dialog fails closed, exit 69, no key, also on a failed read; did-not-clear closes on a failed read; live-space resume: parked supervisor resumes in a new tab of its live lane workspace, no exit 73; space gone opens a new lane workspace; resumed supervisor and worker told resumed with their new pane; fresh start on an existing workspace exits 73)"
