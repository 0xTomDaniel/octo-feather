#!/usr/bin/env bash
# Integration test for herdr-say's up-chain guard vs parked agents (issue #75):
# a supervisor may message its own parked worker (resumed, then messaged); a
# worker still may not reach a parked non-parent, nor a supervisor a parked
# worker of another lane (exit 77). Drives herdr-say's CLI with the fake herdr
# in tests/fixtures/herdr-say/ and a temp state dir per case; HERDR_* and
# OCTO_FEATHER_* are reset, so no live pane is reached. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
mkdir -p "$t/sbin" "$t/cwd"
cp "$kit/tests/fixtures/herdr-say/herdr" "$t/sbin/"; chmod +x "$t/sbin/herdr"
fail() { echo "herdr-say test: $*" >&2; exit 1; }

# One case: lane gh2 lives in workspace w5, its supervisor gh2 live at w5:p1
# (parent: the director w2:p1). Parked lines go into lanes/<lane>.handoffs.jsonl.
setup() { # $1: case
  c="$t/$1"; mkdir -p "$c/state/octo-feather/lanes"
  echo "gh2 w5" >"$c/spaces"; echo "gh2 w5:p1" >"$c/agents"
  XDG_STATE_HOME="$c/state" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null   # the commit identity a role launch needs (#665)
}
park() { # $1: lane, $2: pane, $3: name, $4: parent, $5: session
  printf '{"at":"2026-10-20T00:00:00Z","kind":"parked","pane":"%s","name":"%s","label":"%s","role":"implementer","parent":"%s","cwd":"%s","session":"%s"}\n' \
    "$2" "$3" "$3" "$4" "$t/cwd" "$5" >>"$c/state/octo-feather/lanes/$1.handoffs.jsonl"
}
say() { # $1: role, $2: caller pane, $3: caller parent; rest: herdr-say args
  local role="$1" me="$2" parent="$3"; shift 3; rc=0
  env -u HERDR_SESSION -u HERDR_TAB_ID -u OCTO_FEATHER_OPERATING_MODEL -u OCTO_FEATHER_SESSION_ID \
    FAKE_HERDR_DIR="$c" PATH="$t/sbin:$PATH" XDG_STATE_HOME="$c/state" \
    OCTO_FEATHER_ROLE="$role" OCTO_FEATHER_PARENT="$parent" HERDR_PANE_ID="$me" HERDR_WORKSPACE_ID=w5 \
    HERDR_SPAWN_TRUST_RETRIES=1 HERDR_SPAWN_READY_RETRIES=2 \
    "$kit/.agents/skills/herdr-comms/assets/herdr-say" "$@" >"$c/out" 2>"$c/err" || rc=$?
}
delivered() { awk -F'\t' -v p="$1" '$1 == p {print $2}' "$c/prompts" 2>/dev/null; }
resumed() { # $1: case label, $2: session. The fake call log shows a resume.
  grep -q '^tab create --workspace w5 ' "$c/argv" || fail "$1: no tab created in w5: $(cat "$c/argv")"
  grep -q -- "--session-id $2\b" "$c/argv" || fail "$1: not resumed with old session $2: $(cat "$c/argv")"
  grep -qx 'pane=w5:p9' "$c/out" || fail "$1: pane= not printed: $(cat "$c/out")"
  [[ "$(delivered w5:p9)" == "Resumed from park as pane=w5:p9. go on" ]] ||
    fail "$1: delivered '$(delivered w5:p9)', want the resume notice naming w5:p9"
}
refused() { # $1: case label
  [[ "$rc" == 77 ]] || fail "$1: exit $rc, want 77: $(cat "$c/err")"
  grep -q 'may message only up its chain' "$c/err" || fail "$1: no up-chain refusal on stderr: $(cat "$c/err")"
  grep -qE '^(tab|workspace) create|^agent (start|prompt)' "$c/argv" 2>/dev/null &&
    fail "$1: refused send still resumed or prompted: $(cat "$c/argv")"
  return 0
}

# 1. Supervisor gh2 -> its parked worker, found by its lane log (the line's
#    parent is a pane the supervisor had before its own park and resume).
setup lane
park gh2 w5:p3 impl1 w5:p0 S2
printf 'not JSON\n{"kind":\n42\n\377\n' >"$c/state/octo-feather/lanes/other.handoffs.jsonl"
say supervisor w5:p1 w2:p1 --parked impl1
[[ "$rc" == 0 ]] || fail "corrupt log lookup: exit $rc: $(cat "$c/err")"
jq -e '.session == "S2" and .name == "impl1"' "$c/out" >/dev/null || fail "lost parked record"
for n in 1 2 3 4; do
  grep -q "other.handoffs.jsonl:$n:" "$c/err" || fail "missing file:line diagnostic $n"
done
say supervisor w5:p1 w2:p1 impl1 "go on"
[[ "$rc" == 0 ]] || fail "lane log: exit $rc, want 0: $(cat "$c/err")"
resumed "lane log" S2

# 2. Supervisor -> a parked worker whose line names the caller as parent, the
#    caller's own name unknown to Herdr.
setup parent
: >"$c/agents"
park gh2 w5:p3 impl1 w5:p1 S3
say supervisor w5:p1 w2:p1 w5:p3 "go on"
[[ "$rc" == 0 ]] || fail "parent: exit $rc, want 0: $(cat "$c/err")"
resumed "parent" S3

# 3. Worker -> a parked pane that is not its parent (a sibling worker): 77.
setup sideways
echo "implementer-gh2 w5:p2" >>"$c/agents"
park gh2 w5:p3 impl1 w5:p1 S4
say implementer w5:p2 w5:p1 w5:p3 "hi"
refused "worker to parked sibling"

# 4. Supervisor gh2 -> a parked worker of lane gh3: 77.
setup other
park gh3 w6:p3 impl9 w6:p1 S5
say supervisor w5:p1 w2:p1 impl9 "hi"
refused "supervisor to other lane's parked worker"

echo "herdr-say: ok (supervisor resumes and messages its parked worker by lane log or parent, old session, pane= printed; worker to parked sibling and supervisor to another lane's parked worker exit 77, nothing resumed)"
