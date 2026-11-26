#!/usr/bin/env bash
# Integration test for resuming a parked agent through herdr-say (issue #9; comms spec #roles-park,
# #acceptance-resume-live-space): drives herdr-say and octo-feather-start with the fake herdr of
# tests/fixtures/herdr-say/, a temp state dir per case. No real herdr, pi or state dir. Moved out of
# tests/herdr-spawn.sh (#1308: each item under the per-test CPU budget). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
# ident DIR: the commit identity a role launch needs (#665) in state dir DIR: set once through pi-role --set-identity,
# its file copied for each later DIR (one Python start, not one per case: the CPU budget).
ident() {
  [[ -f "$t/ident/octo-feather/onboarding.toml" ]] || XDG_STATE_HOME="$t/ident" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null
  mkdir -p "$1/octo-feather"; cp "$t/ident/octo-feather/onboarding.toml" "$1/octo-feather/"
}
export XDG_STATE_HOME="$t/state"; ident "$t/state"
mkdir -p "$t/cwd"
# mise's state its own, also run bare outside the gate: mise in $t/cwd's mise.toml records it there, never in the caller's (#664).
export MISE_STATE_DIR="$t/mise-state"
fail() { echo "herdr-say-resume test: $*" >&2; exit 1; }

# 4. Resuming a parked agent through herdr-say (comms spec #roles-park,
#    #acceptance-resume-live-space), with the fake herdr in
#    tests/fixtures/herdr-say/ and a temp state dir per case.
mkdir -p "$t/sbin"
cp "$kit/tests/fixtures/herdr-say/herdr" "$t/sbin/"; chmod +x "$t/sbin/herdr"
cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/sbin/busctl"; cp "$kit/tests/gate/kit/testkit/systemd.py" "$t/sbin/systemctl"   # systemd stood in: the scope is e2e

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

echo "herdr-say-resume: ok (live-space resume: parked supervisor resumes in a new tab of its live lane workspace, no exit 73; space gone opens a new lane workspace; resumed supervisor and worker told resumed with their new pane; fresh start on an existing workspace exits 73)"
