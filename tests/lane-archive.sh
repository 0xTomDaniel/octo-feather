#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane archive (spec comms #acceptance-lane-archive):
# seeds a temp state dir (default and named HERDR_SESSION), closes a lane through the
# command, and proves sha256 before = after (the hand-off log: its lines unchanged, then the lane
# reflection's line, spec comms #reflection-lane), lanes/ no longer lists it, archive/ holds both; a lane
# without a hand-off log; each refusal leaves every file in place. A stub pi stands in for the reflector's
# model (tests/lane-reflect.sh covers the reflection itself). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t"; rm -rf "$t"' EXIT
export HOME="$t/home" XDG_STATE_HOME="$t/state"   # never the real state dir
fail() { echo "lane-archive test: $*" >&2; exit 1; }
# Stub reflector model: no gap found; Herdr unreachable.
mkdir -p "$t/bin"
cat >"$t/bin/pi" <<'EOF'
#!/bin/sh
prompt="$(cat)"
case "$prompt" in
  *"Director reflection"*) echo "Questions: owner-asked, answered-from-memory, rework-decision, unblocking-first, outside-owner-gates, fact-already-recorded, writer-route, director-mechanical-step, director-reflection-missed" ;;
  *) echo "Questions: caught-by-hand, slow-or-from-memory, undetected-rule, check-misfired, mechanical-step, writer-mistake, reflection-missed" ;;
esac
echo "Findings: none"
EOF
printf '#!/bin/sh\nexit 1\n' >"$t/bin/herdr"; chmod +x "$t/bin/pi" "$t/bin/herdr"; export PATH="$t/bin:$kit/tests/fixtures/tracker-gh:$PATH" FAKE_GH_STORE="$t/gh.json"   # the offline gh (tests/lane-correction.sh)
unset HERDR_PANE_ID PI_SESSION_FILE OCTO_FEATHER_REFLECT_ARGS
reflected() { # ARCHIVED-LOG ORIGINAL-LOG-COPY: the original bytes, a newline if they lacked one, then one reflection line
  python3 - "$1" "$2" <<'PY'
import json, sys
got, orig = open(sys.argv[1], "rb").read(), open(sys.argv[2], "rb").read()
head = orig + (b"\n" if orig and not orig.endswith(b"\n") else b"")
assert got.startswith(head), "lane lines changed"
tail = got[len(head):].decode().splitlines()
assert len(tail) == 1 and json.loads(tail[0])["kind"] == "reflection" and json.loads(tail[0])["findings"] == 0, tail
PY
}
sums() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0r sha256sum); }
seed() { # DIR NAME [nolog]
  mkdir -p "$1"
  printf 'issue = "gh0"\nsupervisor = "w1:p2"\ngoal = "x \xc3\xa9"\n' >"$1/$2.toml"   # non-ASCII, no final edit
  [[ "${3:-}" == nolog ]] || printf '{"at":"2026-10-20T00:00:00Z","kind":"attempt"}\n{"kind":"integration"}' >"$1/$2.handoffs.jsonl"
}
archive_ok() { # LANES NAME SESSION: run, then check every claim
  local lanes="$1" name="$2" out rec log
  rec="$(sha256sum <"$lanes/$name.toml")"; rec="${rec%% *}"
  cp "$lanes/$name.handoffs.jsonl" "$t/orig.jsonl"
  out="$(HERDR_SESSION="$3" "$L" archive "$name")" || fail "archive $name failed"
  grep -qxF "archived: $lanes/archive/$name.toml sha256=$rec" <<<"$out" || fail "no record sha line: $out"
  log="$(sha256sum <"$lanes/archive/$name.handoffs.jsonl")"; log="${log%% *}"
  grep -qxF "archived: $lanes/archive/$name.handoffs.jsonl sha256=$log" <<<"$out" || fail "no log sha line: $out"
  [[ "$(sha256sum <"$lanes/archive/$name.toml")" == "$rec  -" ]] || fail "record bytes changed"
  reflected "$lanes/archive/$name.handoffs.jsonl" "$t/orig.jsonl" || fail "archived log is not the lane's bytes plus one reflection line"
  [[ -z "$(find "$lanes" -maxdepth 1 -name "$name.*")" ]] || fail "lanes/ still lists $name: $(ls "$lanes")"
}

# Default session (HERDR_SESSION empty): state at the top; a second lane is untouched.
top="$XDG_STATE_HOME/octo-feather/lanes"
seed "$top" gh0; seed "$top" gh1; other="$(sums "$top" | grep gh1)"
archive_ok "$top" gh0 ""
[[ "$(sums "$top" | grep ' ./gh1')" == "$other" ]] || fail "another lane changed"

# Named session: state under sessions/<key>; the default session's same-named lane stays.
named="$XDG_STATE_HOME/octo-feather/sessions/s1/lanes"
seed "$named" gh2; seed "$top" gh2
archive_ok "$named" gh2 s1
[[ -f "$top/gh2.toml" && ! -e "$top/archive/gh2.toml" ]] || fail "named session touched the default session"

# No hand-off log: the reflection writes its first line, archived beside the record.
seed "$top" gh3 nolog
out="$(HERDR_SESSION='' "$L" archive gh3)" || fail "archive without a log failed"
grep -qF "archived: $top/archive/gh3.toml sha256=" <<<"$out" && grep -qF "archived: $top/archive/gh3.handoffs.jsonl sha256=" <<<"$out" || fail "no-log output: $out"
: >"$t/empty"; reflected "$top/archive/gh3.handoffs.jsonl" "$t/empty" || fail "no-log archive: log is not one reflection line"
[[ ! -e "$top/gh3.toml" && ! -e "$top/gh3.handoffs.jsonl" ]] || fail "no-log move wrong"

tree() { (cd "$1" && find . -printf '%p %y %n %l\n' | sort); sums "$1"; }   # entries, types, link counts, symlink targets, bytes
refuse() { # WANT NAME: non-zero, message, every entry under the state dir unchanged
  local before after out rc
  before="$(tree "$XDG_STATE_HOME")"
  set +e; out="$(HERDR_SESSION='' "$L" archive "$2" 2>&1)"; rc=$?; set -e
  [[ "$rc" != 0 ]] || fail "archive $2 did not refuse"
  grep -qF "$1" <<<"$out" || fail "refusal for $2 did not say '$1': $out"
  after="$(tree "$XDG_STATE_HOME")"
  [[ "$before" == "$after" ]] || fail "refusal for $2 moved or changed files: $(diff <(echo "$before") <(echo "$after"))"
  grep -q Traceback <<<"$out" && fail "refusal for $2 printed a traceback: $out"; :
}
# Missing record (a stray log of that name stays).
printf '{}\n' >"$top/gh4.handoffs.jsonl"
refuse "no lane record" gh4
# Archived record already there.
seed "$top" gh0; refuse "archive target exists: $top/archive/gh0.toml" gh0
# Archived log already there, record not.
seed "$top" gh5; printf 'old\n' >"$top/archive/gh5.handoffs.jsonl"
refuse "archive target exists: $top/archive/gh5.handoffs.jsonl" gh5
# Bad name.
refuse "usage" ../gh1
# Non-regular sources are refused before any move: symlinked record (review of a80d7b6),
# symlinked log, directory record, directory log.
printf 'issue = 0\n' >"$top/seed.toml"; ln -s seed.toml "$top/gh7.toml"; printf '{}\n' >"$top/gh7.handoffs.jsonl"
refuse "not a regular file: $top/gh7.toml" gh7
printf 'issue = 0\n' >"$top/gh8.toml"; printf '{}\n' >"$top/seed.jsonl"; ln -s seed.jsonl "$top/gh8.handoffs.jsonl"
refuse "not a regular file: $top/gh8.handoffs.jsonl" gh8
mkdir "$top/gh9.toml"; printf '{}\n' >"$top/gh9.handoffs.jsonl"
refuse "not a regular file: $top/gh9.toml" gh9
printf 'issue = 0\n' >"$top/gh10.toml"; mkdir "$top/gh10.handoffs.jsonl"
refuse "not a regular file: $top/gh10.handoffs.jsonl" gh10

# Execution failure (read-only lanes/: link into archive/ works, unlink of the source fails):
# no partial archive, no hard link left behind; a retry after restoring permissions succeeds.
ro="read-only lanes/: skipped (uid 0 ignores chmod)"
if [[ "$(id -u)" != 0 ]]; then
  ro_lanes="$XDG_STATE_HOME/octo-feather/sessions/ro/lanes"
  seed "$ro_lanes" gh6; mkdir -p "$ro_lanes/archive"
  chmod 555 "$ro_lanes"
  before="$(sums "$ro_lanes")"
  set +e; out="$(HERDR_SESSION=ro "$L" archive gh6 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 ]] || fail "read-only lanes/: exit $rc, want 1: $out"
  grep -qF "move failed" <<<"$out" || fail "read-only lanes/: no move-failed message: $out"
  [[ "$(sums "$ro_lanes")" == "$before" ]] || fail "read-only lanes/: partial archive: $(sums "$ro_lanes")"
  [[ -z "$(ls -A "$ro_lanes/archive")" ]] || fail "read-only lanes/: archive/ not empty"
  [[ "$(stat -c %h "$ro_lanes/gh6.toml")" == 1 ]] || fail "read-only lanes/: record still hard-linked"
  # No archive/ yet and lanes/ read-only: mkdir fails, refused cleanly, nothing created.
  chmod 755 "$ro_lanes"; rmdir "$ro_lanes/archive"; chmod 555 "$ro_lanes"
  set +e; out="$(HERDR_SESSION=ro "$L" archive gh6 2>&1)"; rc=$?; set -e
  [[ "$rc" == 1 ]] && grep -qF "move failed" <<<"$out" || fail "read-only lanes/, no archive/: $rc $out"
  [[ ! -e "$ro_lanes/archive" && "$(sums "$ro_lanes")" == "$before" ]] || fail "read-only lanes/, no archive/: files changed"
  chmod 755 "$ro_lanes"
  archive_ok "$ro_lanes" gh6 ro
  ro="read-only lanes/ rolls back, retry succeeds"
fi
echo "lane-archive: ok (default + named session, sha256 before = after; no log (reflection line archived); refusals: missing record, archived record, archived log, bad name, symlinked record, symlinked log, directory record, directory log; $ro)"
