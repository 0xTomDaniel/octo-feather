#!/usr/bin/env bash
# Integration test for `octo-feather-spec-status init` over an existing status file (issue-lifecycle
# #spec-status-file, #acceptance-revision-preserve, -remove, -repeat, -invalid), and `check` after it: one scratch
# git repo, a spec accepted with criteria a, b, c (tests/fixtures/spec-status/revision/accepted.spec.html), then
# revised to a, b, d (revised.spec.html). Run as a command, never loaded (docs/adr/0002).
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
S="$kit/scripts/octo-feather-spec-status"; F="$kit/tests/fixtures/spec-status/revision"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
fail() { echo "spec-revision-init test: $*" >&2; exit 1; }
r="$t/repo"; d="$r/docs/specs"; ST="$d/demo.status.json"; mkdir -p "$d"
git init -q "$r"
commit() { git -C "$r" add -A; git -C "$r" commit -qm "$1"; git -C "$r" rev-parse HEAD; }
init() { set +e; out="$("$S" init "$@" 2>&1)"; rc=$?; set -e; }
# row ID FILE: the text of criterion ID's row in a status file as written, its lines from `"ID": {` to its `}`.
row() { perl -0ne "print \$1 if /^(    \"$1\": \\{.*?^    \\})/ms" "$2"; }

# Fresh init: every criterion planned, in spec order (unchanged by a revision-aware init).
cp "$F/accepted.spec.html" "$d/demo.spec.html"; c1="$(commit accepted)"
init "$d/demo.spec.html" "$c1"; [[ "$rc" == 0 && "$out" == "$ST" ]] || fail "fresh init: exit $rc: $out"
want="$(printf '{\n  "spec": "demo.spec.html",\n  "accepted_commit": "%s",\n  "criteria": {\n' "$c1"
  for x in a b c; do printf '    "acceptance-%s": {\n      "status": "planned",\n      "pr": null\n    }%s\n' "$x" "$([[ $x == c ]] || echo ,)"; done
  printf '  }\n}')"
[[ "$(cat "$ST")" == "$want" ]] || fail "fresh init wrote: $(cat "$ST")"

# Built rows: a with an evidence link, b without (built before qc linked one); a logged call names c.
"$S" built "$ST" 7 acceptance-a --record 20261029T100000Z-0a0a0a0a --commit "$c1" --test tests/a.sh --test tests/a2.sh
"$S" built "$ST" 8 acceptance-b
call() { printf '{"at": "2026-10-21T10:00:00Z", "lane": "gh62", "role": "supervisor", "kind": "clarifies", "anchors": ["acceptance-%s"], "criteria": ["acceptance-%s"], "what": "w", "why": "y", "passes_as_written": false, "evidence": "e"}\n' "$1" "$1"; }
call c >"$d/demo.calls.jsonl"; commit built >/dev/null
ra="$(row acceptance-a "$ST")"; rb="$(row acceptance-b "$ST")"
[[ -n "$ra" && -n "$rb" ]] || fail "rows not found in: $(cat "$ST")"

# #acceptance-revision-preserve, -remove: the owner accepts a revision dropping c and adding d.
cp "$F/revised.spec.html" "$d/demo.spec.html"; c2="$(commit revised)"
init "$d/demo.spec.html" "$c2"; [[ "$rc" == 0 ]] || fail "revision init: exit $rc: $out"
[[ "$(row acceptance-a "$ST")" == "$ra" ]] || fail "row a not kept byte for byte: $(cat "$ST")"
[[ "$(row acceptance-b "$ST")" == "$rb" ]] || fail "row b not kept byte for byte: $(cat "$ST")"
python3 - "$ST" "$c2" <<'EOF' || fail "revision init wrote: $(cat "$ST")"
import json, sys
s = json.load(open(sys.argv[1]))
assert s["accepted_commit"] == sys.argv[2], s
assert list(s["criteria"]) == ["acceptance-a", "acceptance-b", "acceptance-d"], s
assert s["criteria"]["acceptance-d"] == {"status": "planned", "pr": None}, s
EOF
# -remove at `check`: a call already in the log at accepted_commit naming the dropped c passes; one added since fails.
commit "status of the revision" >/dev/null
"$S" check "$d" >/dev/null 2>"$t/err" || fail "check after revision init: $(cat "$t/err")"
call c >>"$d/demo.calls.jsonl"
"$S" check "$d" >/dev/null 2>"$t/err" && fail "check passed a call added since accepted_commit naming dropped c"
grep -qF "demo.calls.jsonl:2: call (lane gh62; anchors acceptance-c): criterion acceptance-c is in neither" "$t/err" \
  || fail "new call naming c not reported: $(cat "$t/err")"
git -C "$r" checkout -q -- docs/specs

# #acceptance-revision-repeat: a lane builds d with its evidence link; the same init again changes no byte.
"$S" built "$ST" 9 acceptance-d --record 20261030T100000Z-0d0d0d0d --commit "$c2" --test tests/d.sh
cp "$ST" "$t/before"
init "$d/demo.spec.html" "$c2"; [[ "$rc" == 0 ]] || fail "repeat init: exit $rc: $out"
cmp -s "$t/before" "$ST" || fail "repeat init changed the file: $(diff "$t/before" "$ST")"

# #acceptance-revision-invalid: invalid existing status refuses, naming the criterion and field; no byte written.
refuse() { # refuse CASE SPEC TEXT...: init exits non-zero naming each TEXT and leaves the status file as it was
  local name="$1" spec="$2"; shift 2; cp "$ST" "$t/before"
  init "$spec" "$c2"; [[ "$rc" != 0 ]] || fail "$name: init passed: $out"
  for w in "$@"; do grep -qF -- "$w" <<<"$out" || fail "$name: did not report: $w"$'\n'"$out"; done
  cmp -s "$t/before" "$ST" || fail "$name: status file changed: $(diff "$t/before" "$ST")"; }
perl -0pi -e 's/("acceptance-a": \{[^}]*?"record": "[^"]*"),\s*"commit": "[^"]*",\s*"tests": \[[^]]*\]/$1/s' "$ST"
if ! grep -q 20261029T100000Z-0a0a0a0a "$ST" || grep -q tests/a.sh "$ST"; then fail "partial link not made: $(cat "$ST")"; fi
refuse "partial link" "$d/demo.spec.html" "acceptance-a: names record without commit, tests"
printf '{"spec": ' >"$ST"; refuse "bad JSON" "$d/demo.spec.html" "demo.status.json"
git -C "$r" checkout -q -- docs/specs
perl -0pi -e 's/"status": "built"/"status": "done"/' "$ST"   # the first built row, a's
refuse "bad status" "$d/demo.spec.html" "acceptance-a: status must be planned or built, not 'done'"
git -C "$r" checkout -q -- docs/specs
# A spec init cannot read, or whose criteria are not one id each, writes nothing.
refuse "no spec" "$d/gone.spec.html" "gone.spec.html"
[[ ! -e "$d/gone.status.json" ]] || fail "no spec: wrote gone.status.json"
perl -pe 's/acceptance-d/acceptance-a/g' "$d/demo.spec.html" >"$d/dup.spec.html"
init "$d/dup.spec.html" "$c2"
if [[ "$rc" == 0 ]] || ! grep -qF "duplicate criterion id acceptance-a" <<<"$out"; then fail "duplicate id: exit $rc: $out"; fi
[[ ! -e "$d/dup.status.json" ]] || fail "duplicate id: wrote dup.status.json"

echo "spec-revision-init: ok (fresh, preserve, remove, check after remove, repeat, invalid: partial link, bad JSON, bad status, no spec, duplicate id)"
