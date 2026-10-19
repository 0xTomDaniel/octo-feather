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
mkdir -p "$t/bin" "$t/cwd" "$t/cache"
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
for f in --no-skills --no-mcp; do grep -qx -- "$f" "$t/ok/start-argv" || fail "pi-role --json args lost $f beside --approve"; done
[[ "$rc" == 0 ]] || fail "spawn exited $rc: $(cat "$t/ok/err")"
grep -q 'tab=w9:t1 pane=w9:p1' "$t/ok/out" || fail "spawn printed no tab and pane: $(cat "$t/ok/out")"
[[ ! -s "$t/ok/keys" ]] || fail "keys sent to a ready pane: $(cat "$t/ok/keys")"

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
  c="$t/$1"; mkdir -p "$c/state/octo-feather/lanes"
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
say w5:p1 hello
[[ "$rc" == 0 ]] || fail "resume: live space: herdr-say exit $rc, want 0: $(cat "$c/err")"
grep -q '^workspace create' "$c/argv" && fail "resume: live space: a new workspace was created: $(cat "$c/argv")"
grep -q '^tab create --workspace w5 ' "$c/argv" || fail "resume: live space: no tab created in w5: $(cat "$c/argv")"
grep -qx 'gh2 w5:p9' "$c/agents" || fail "resume: live space: supervisor gh2 not started in w5: $(cat "$c/agents")"
grep -qx 'pane=w5:p9' "$c/out" || fail "resume: live space: new pane not printed: $(cat "$c/out")"
[[ "$(delivered w5:p9)" == "Resumed from park as pane=w5:p9. hello" ]] ||
  fail "resume: live space: delivered '$(delivered w5:p9)', want the resume notice naming w5:p9"
[[ ! -s "$c/closed" ]] || fail "resume: live space: tabs closed in the live workspace: $(cat "$c/closed")"

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

echo "herdr-spawn: ok (pane and headless launch carry --approve; Pi trust dialog fails closed, exit 69, no key, also on a failed read; did-not-clear closes on a failed read; live-space resume: parked supervisor resumes in a new tab of its live lane workspace, no exit 73; space gone opens a new lane workspace; resumed supervisor and worker told resumed with their new pane; fresh start on an existing workspace exits 73)"
