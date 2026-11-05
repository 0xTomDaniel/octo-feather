#!/usr/bin/env bash
# Integration test for `scripts/octo-feather-lane intake` (spec comms #reflection-correction,
# #acceptance-correction-intake; the rule: issue-lifecycle #lanes-correction), run as a command over scratch lane
# logs and the offline fake gh (tests/fixtures/tracker-gh): nothing reaches GitHub, nothing is written.
# Proves: each open correction-lane issue under its class with its findings, blocking count, lanes and due or not;
# two open issues of one class grouped as duplicates; a closed one left out. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
export HOME="$t/home" XDG_STATE_HOME="$t/state" HERDR_SESSION="" FAKE_GH_STORE="$t/gh.json"
unset HERDR_PANE_ID GH_REPO
fail() { echo "lane-intake test: $*" >&2; exit 1; }
export PATH="$kit/tests/fixtures/tracker-gh:$PATH"
state="$XDG_STATE_HOME/octo-feather"; lanes="$state/lanes"; mkdir -p "$lanes/archive" "$HOME"; cd "$t"
f() { printf '{"at":"%s","kind":"finding","source":"%s","class":"%s","blocking":%s,"summary":"%s"}\n' "$@"; }
rec() { printf 'issue = "%s"\nrepository = "o/t"\nsupervisor = "w9:p2"\ngoal = "scratch"\n' "$1" >"$lanes/archive/$1.toml"; }
rec gh1; rec gh2
{ f 2026-10-20T00:00:00Z code-review dup-rule true "gh1 restated the merge rule"
  f 2026-10-20T01:00:00Z reflection refl-only false "gh1 reflection"
  f 2026-10-20T02:00:00Z code-review twice true "gh1 twice"; } >"$lanes/archive/gh1.handoffs.jsonl"
{ f 2026-10-21T00:00:00Z code-review dup-rule true "gh2 restated the gate rule"
  f 2026-10-21T01:00:00Z reflection refl-only false "gh2 reflection"; } >"$lanes/archive/gh2.handoffs.jsonl"
printf '%s\n' '{"at":"2026-10-22T00:00:00Z","kind":"finding","class":"twice","summary":"director saw twice"}' >"$state/director.handoffs.jsonl"
python3 - "$FAKE_GH_STORE" <<'PY'
import json, sys
i = lambda n, repo, cls, state="OPEN": {"number": n, "repo": repo, "title": f"[correction-lane {cls}] repeated finding class: {cls}",
                                         "body": "", "state": state, "closedAt": None if state == "OPEN" else "2026-10-01T00:00:00Z"}
json.dump({"issues": [i(901, "o/t", "dup-rule"), i(902, "o/t", "refl-only"), i(903, "o/t", "twice"),
                      i(904, "0xTomDaniel/octo-feather", "twice"), i(905, "o/t", "old", "CLOSED")]}, open(sys.argv[1], "w"))
PY
cp "$FAKE_GH_STORE" "$t/before.json"
out="$("$L" intake 2>&1)" || fail "intake failed: $out"
want='correction intake: 4 open correction-lane issue(s) in 3 class(es); trackers searched (github-issues): o/t, 0xTomDaniel/octo-feather; rule: issue-lifecycle #lanes-correction
class dup-rule: due yes; blocking 2 in 2 lane(s) (gh1, gh2); findings 2
  issue o/t#901: [correction-lane dup-rule] repeated finding class: dup-rule
  finding gh1 2026-10-20T00:00:00Z code-review blocking: gh1 restated the merge rule
  finding gh2 2026-10-21T00:00:00Z code-review blocking: gh2 restated the gate rule
class refl-only: due no; blocking 0 in 0 lane(s); findings 2
  issue o/t#902: [correction-lane refl-only] repeated finding class: refl-only
  finding gh1 2026-10-20T01:00:00Z reflection not blocking: gh1 reflection
  finding gh2 2026-10-21T01:00:00Z reflection not blocking: gh2 reflection
class twice: due no; blocking 1 in 1 lane(s) (gh1); findings 2
  issue o/t#903: [correction-lane twice] repeated finding class: twice
  issue 0xTomDaniel/octo-feather#904: [correction-lane twice] repeated finding class: twice
  duplicates: 2 open issues of class twice
  finding gh1 2026-10-20T02:00:00Z code-review blocking: gh1 twice
  finding director 2026-10-22T00:00:00Z director not blocking: director saw twice'
[[ "$out" == "$want" ]] || fail "intake report: want
$want
got
$out"
cmp -s "$FAKE_GH_STORE" "$t/before.json" || fail "intake wrote to the tracker"
"$L" intake extra >/dev/null 2>&1 && fail "intake took an argument"
echo "lane-intake: ok (each open correction-lane issue by class with findings, blocking count, lanes, due or not; duplicates grouped; closed left out; nothing written)"
