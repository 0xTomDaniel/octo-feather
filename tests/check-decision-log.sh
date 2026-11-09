#!/usr/bin/env bash
# Integration test for the check-decision-log gate (quality #acceptance-decision-log-schema):
# in a throwaway git copy of the kit's tracked files, a planted tracked decisions.jsonl
# (at the root or nested) with a bad line makes `just check-decision-log` fail naming FILE:LINE
# and the field; a valid log, an untracked log and no log pass (#231: the recipe under test, not
# the whole gate per case); one case runs `just check` to prove the gate includes
# check-decision-log. Run by `just check`.
set -euo pipefail
# The one `just check` case in the copy runs this test there too (its tests/*.sh step): stop there, nested.
[[ -z "${CHECK_DECISION_LOG_TEST_COPY:-}" ]] || { echo "check-decision-log test: nested run in a copy (a planted log passed check-decision-log)" >&2; exit 1; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t" "$t.home" "$t.schema" "$t.bin"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
schema=schemas/decision-log.schema.json
cp "$t/$schema" "$t.schema"
# A repo with no tracked decisions.jsonl passes.
set +e; out="$(cd "$t" && just check-decision-log 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 ]] && grep -qF 'decision-log: ok (0 files)' <<<"$out" || { echo "check-decision-log test: clean copy with no log is not green" >&2; echo "$out" >&2; exit 1; }
# Planted logs: tracked unless the third argument is "untracked".
plant() { mkdir -p "$t/$(dirname "$1")"; printf '%b' "$2" > "$t/$1"; [[ "${3:-}" == untracked ]] || g add -f "$1"; }
unplant() { g rm -qf --cached "$1" >/dev/null 2>&1 || true; rm -f "$t/$1"; [[ "$1" != */* ]] || rmdir -p "$t/$(dirname "$1")" 2>/dev/null || true; }
# run RECIPE: the command `just RECIPE` runs (the justfile's check-decision-log: python3 "$root/scripts/check-decision-log"),
# the copy's scripts/RECIPE, in the copy into $out and $rc: one just evaluation per answer, not one per case (#507);
# the clean copy, the broken tools and the gate case run `just check-decision-log` itself.
run() { set +e; out="$(cd "$t" && "$t/scripts/$1" 2>&1)"; rc=$?; set -e; }
# expect RECIPE FILE CONTENT REPORT...: a tracked FILE holding CONTENT makes `just RECIPE` fail
# with each REPORT line ("FILE:LINE: problem") printed after "check-decision-log: ".
expect() {
  local recipe="$1" f="$2" c="$3"; shift 3
  plant "$f" "$c"; run "$recipe"; unplant "$f"
  [[ "$rc" != 0 ]] || { echo "check-decision-log test: $f with '$c' passed just $recipe" >&2; exit 1; }
  for r in "$@"; do
    grep -qF "check-decision-log: $r" <<<"$out" || { echo "check-decision-log test: $f with '$c' did not report: $r" >&2; echo "$out" >&2; exit 1; }
  done
  ! grep -qF 'decision-log: ok' <<<"$out" || { echo "check-decision-log test: $f with '$c' printed decision-log: ok" >&2; exit 1; }
}
# allow FILE CONTENT [untracked]: FILE holding CONTENT keeps `just check-decision-log` green.
allow() {
  plant "$1" "$2" "${3:-}"; run check-decision-log; unplant "$1"
  [[ "$rc" == 0 ]] && grep -qF 'decision-log: ok' <<<"$out" || { echo "check-decision-log test: '$2' in $1 failed check-decision-log" >&2; echo "$out" >&2; exit 1; }
}
head='"ts":"2026-10-19T00:00:00Z","agent":"implementer","phase":"handoff","decision":"ready"'
tail='"evidence":"just check","result":"pending"'
ok="{$head,\"why\":\"gate green\",$tail}"
L=decisions.jsonl; N=docs/lane/run/decisions.jsonl
# The criterion cases: missing why, invalid JSON, non-object, nested path.
expect check-decision-log "$L" "{$head,$tail}\n" "$L:1: missing why"
expect check-decision-log "$L" "$ok\n{$head,\"why\":\"x\",$tail\n" "$L:2: invalid JSON"
expect check-decision-log "$L" "[\"why\"]\n" "$L:1: not a JSON object"
expect check-decision-log "$N" "$ok\n$ok\n{$head,$tail}\n" "$N:3: missing why"
# Valid logs pass: one line, several, nested, no final newline, CRLF, any key order, unicode text.
allow "$L" "$ok\n"
allow "$N" "$ok\n$ok\n$ok\n"
allow "$L" "$ok"
allow "$L" "$ok\r\n$ok\r\n"
allow "$L" "{\"result\":\"r\",\"why\":\"w\",\"evidence\":\"e\",\"decision\":\"d\",\"phase\":\"p\",\"agent\":\"a\",\"ts\":\"t\"}\n"
allow "$L" "{$head,\"why\":\"tab\\\\tand newline\\\\n, caf\xc3\xa9\",$tail}\n"
# Untracked logs and other names are out of scope (exact name decisions.jsonl, tracked only).
allow "$L" "{$head,$tail}\n" untracked
allow decisions.jsonl.bak "{$head,$tail}\n"
allow Decisions.jsonl "{$head,$tail}\n"
allow docs/my-decisions.jsonl "not json\n"
# Mixed good and bad lines in one file: only the bad lines are named, each with its field.
plant "$L" "$ok\n{$head,$tail}\n$ok\n{$head,\"why\":\"\",$tail}\n$ok\n"; run check-decision-log; unplant "$L"
[[ "$rc" != 0 ]] && grep -qF "check-decision-log: $L:2: missing why" <<<"$out" && grep -qF "check-decision-log: $L:4: empty why" <<<"$out" \
  && [[ "$(grep -c 'check-decision-log: ' <<<"$out")" == 2 ]] || { echo "check-decision-log test: mixed log not reported as lines 2 and 4 only" >&2; echo "$out" >&2; exit 1; }
# A good and a bad log together: only the bad one is named.
plant "$L" "$ok\n"; plant "$N" "$ok\n$ok\n[]\n"; run check-decision-log; unplant "$L"; unplant "$N"
[[ "$rc" != 0 ]] && grep -qF "check-decision-log: $N:3: not a JSON object" <<<"$out" && [[ "$(grep -c 'check-decision-log: ' <<<"$out")" == 1 ]] \
  || { echo "check-decision-log test: good and bad logs not reported as the bad one" >&2; echo "$out" >&2; exit 1; }
# Adversarial forms: case and spelling variants of why, empty, blank, null and non-string values,
# a duplicate key, an extra field (the schema forbids extras), every non-object JSON value,
# a blank or whitespace line, a BOM, a NaN, non-UTF-8 bytes, an empty object.
expect check-decision-log "$L" "{$head,\"Why\":\"x\",$tail}\n" "$L:1: missing why" "$L:1: unknown field Why"
expect check-decision-log "$L" "{$head,\"why \":\"x\",$tail}\n" "$L:1: missing why"
expect check-decision-log "$L" "{$head,\"whys\":\"x\",$tail}\n" "$L:1: missing why"
expect check-decision-log "$L" "{$head,\"why\":\"\",$tail}\n" "$L:1: empty why"
expect check-decision-log "$L" "{$head,\"why\":\"  \\\\t \",$tail}\n" "$L:1: why does not match"
expect check-decision-log "$L" "{$head,\"why\":null,$tail}\n" "$L:1: why must be a string"
expect check-decision-log "$L" "{$head,\"why\":1,$tail}\n" "$L:1: why must be a string"
expect check-decision-log "$L" "{$head,\"why\":[\"x\"],$tail}\n" "$L:1: why must be a string"
expect check-decision-log "$L" "{$head,\"why\":{\"why\":\"x\"},$tail}\n" "$L:1: why must be a string"
expect check-decision-log "$L" "{$head,\"why\":\"x\",\"why\":\"\",$tail}\n" "$L:1: invalid JSON: duplicate key why"
expect check-decision-log "$L" "{$head,\"why\":\"x\",$tail,\"note\":\"y\"}\n" "$L:1: unknown field note"
expect check-decision-log "$L" "\"why\"\n" "$L:1: not a JSON object"
expect check-decision-log "$L" "null\n" "$L:1: not a JSON object"
expect check-decision-log "$L" "42\n" "$L:1: not a JSON object"
expect check-decision-log "$L" "$ok\n\n$ok\n" "$L:2: invalid JSON"
expect check-decision-log "$L" "$ok\n  \n" "$L:2: invalid JSON"
expect check-decision-log "$L" "\xef\xbb\xbf$ok\n" "$L:1: invalid JSON"
expect check-decision-log "$L" "{$head,\"why\":\"x\",$tail,\"n\":NaN}\n" "$L:1: invalid JSON"
expect check-decision-log "$L" "{$head,\"why\":\"\xff\",$tail}\n" "$L:1: not UTF-8"
expect check-decision-log "$L" "$ok $ok\n" "$L:1: invalid JSON"
expect check-decision-log "$L" "{}\n" "$L:1: missing ts" "$L:1: missing why" "$L:1: missing result"
# Pattern dialect: schemas/decision-log.schema.json's $schema (#142, #121 D9). \S on U+FEFF, U+3000 U+00A0
# U+2028 U+000B (fail) and U+001C..U+001F, U+0085, U+200B, U+180E (pass).
expect check-decision-log "$L" "{$head,\"why\":\"x\",\"evidence\":\"e\",\"result\":\"\\\\ufeff\"}\n" "$L:1: result does not match"
expect check-decision-log "$L" "{$head,\"why\":\"\\\\u3000\\\\u00a0\\\\u2028\\\\u000b\",$tail}\n" "$L:1: why does not match"
for c in 001c 001d 001e 001f 0085 200b 180e; do allow "$L" "{$head,\"why\":\"\\\\u$c\",$tail}\n"; done
# The same dialect (#142) on \d \w \b . $ [\S] [^\s] via schema edits.
set_pattern() { python3 - "$t/$schema" "$1" <<'PY'
import json, sys
s = json.load(open(sys.argv[1])); s["properties"]["why"]["pattern"] = sys.argv[2]; json.dump(s, open(sys.argv[1], "w"))
PY
}
set_pattern '^\d+$'; expect check-decision-log "$L" "{$head,\"why\":\"\\\\u0663\",$tail}\n" "$L:1: why does not match"
expect check-decision-log "$L" "{$head,\"why\":\"1\\\\n\",$tail}\n" "$L:1: why does not match"; allow "$L" "{$head,\"why\":\"12\",$tail}\n"
set_pattern '^\w\b'; expect check-decision-log "$L" "{$head,\"why\":\"\\\\u00e9\",$tail}\n" "$L:1: why does not match"
allow "$L" "{$head,\"why\":\"a\\\\u00e9\",$tail}\n"; allow "$L" "{$head,\"why\":\"a b\",$tail}\n"
set_pattern '^a.b$'; expect check-decision-log "$L" "{$head,\"why\":\"a\\\\u2028b\",$tail}\n" "$L:1: why does not match"; allow "$L" "{$head,\"why\":\"a\\\\u0085b\",$tail}\n"
set_pattern '^[\S]+$'; expect check-decision-log "$L" "{$head,\"why\":\"a\\\\ufeff\",$tail}\n" "$L:1: why does not match"; allow "$L" "{$head,\"why\":\"a\\\\u001c\",$tail}\n"
set_pattern '^[^\s]+$'; expect check-decision-log "$L" "{$head,\"why\":\"a\\\\ufeff\",$tail}\n" "$L:1: why does not match"; allow "$L" "{$head,\"why\":\"a\\\\u0085\",$tail}\n"
# PR #140 review rounds 2 and 3 (owner: schemas/decision-log.schema.json $schema, #142): ^a++$ and ^a{U+0661}$
# are refused naming the property and node's error; an unmatched backreference matches empty, so "ac" passes.
set_pattern '^a++$'; plant "$L" "{$head,\"why\":\"a\",$tail}\n"; run check-decision-log; unplant "$L"
[[ "$rc" == 2 ]] && grep -qF "check-decision-log: $schema: unusable schema: property why: pattern '^a++\$': Invalid regular expression: /^a++\$/u: Nothing to repeat" <<<"$out" \
  || { echo "check-decision-log test: pattern ^a++\$ not refused as unusable" >&2; echo "$out" >&2; exit 1; }
set_pattern $'^a{\u0661}$'; plant "$L" "{$head,\"why\":\"a{\\\\u0661}\",$tail}\n"; run check-decision-log; unplant "$L"
[[ "$rc" == 2 ]] && grep -qF "check-decision-log: $schema: unusable schema: property why: pattern '^a{"$'\u0661'"}\$': Invalid regular expression: /^a{"$'\u0661'"}\$/u: Incomplete quantifier" <<<"$out" \
  || { echo "check-decision-log test: pattern ^a{U+0661}\$ not refused as unusable" >&2; echo "$out" >&2; exit 1; }
# PR #140 review round 4 (owner: #142): a property named __proto__ is schema data like any other, so its
# invalid pattern is refused with no tracked log and its valid one is tested.
set_proto() { cp "$t.schema" "$t/$schema"; python3 - "$t/$schema" "$1" <<'PY'
import json, sys
s = json.load(open(sys.argv[1])); s["properties"]["__proto__"] = {"type": "string", "pattern": sys.argv[2]}; json.dump(s, open(sys.argv[1], "w"))
PY
}
set_proto '^a++$'; run check-decision-log
[[ "$rc" == 2 ]] && grep -qF "check-decision-log: $schema: unusable schema: property __proto__: pattern '^a++\$': Invalid regular expression: /^a++\$/u: Nothing to repeat" <<<"$out" \
  || { echo "check-decision-log test: __proto__ pattern ^a++\$ not refused as unusable" >&2; echo "$out" >&2; exit 1; }
set_proto '^a$'; expect check-decision-log "$L" "{$head,\"why\":\"x\",$tail,\"__proto__\":\"b\"}\n" "$L:1: __proto__ does not match ^a\$"
allow "$L" "{$head,\"why\":\"x\",$tail,\"__proto__\":\"a\"}\n"
cp "$t.schema" "$t/$schema"
set_pattern '^(a|(b))\2c$'; allow "$L" "{$head,\"why\":\"ac\",$tail}\n"; expect check-decision-log "$L" "{$head,\"why\":\"bc\",$tail}\n" "$L:1: why does not match"
cp "$t.schema" "$t/$schema"
# The schema file is the one source for the field list and the extra-field policy.
python3 - "$t/$schema" <<'PY'
import json, sys
s = json.load(open(sys.argv[1])); s["required"].append("ticket"); s["properties"]["ticket"] = {"type": "string"}
json.dump(s, open(sys.argv[1], "w"))
PY
expect check-decision-log "$L" "$ok\n" "$L:1: missing ticket"
allow "$L" "{$head,\"why\":\"x\",$tail,\"ticket\":\"#44\"}\n"
python3 - "$t/$schema" <<'PY'
import json, sys
s = json.load(open(sys.argv[1])); s["additionalProperties"] = True; json.dump(s, open(sys.argv[1], "w"))
PY
allow "$L" "{$head,\"why\":\"x\",$tail,\"ticket\":\"#44\",\"note\":\"y\"}\n"
cp "$t.schema" "$t/$schema"
# Fails closed: an unusable schema (invalid JSON, missing, or a keyword the validator does not
# enforce) fails even with no log, never decision-log: ok.
schema_bad() {
  if [[ "$1" == missing ]]; then rm -f "$t/$schema"; else printf '%s' "$1" > "$t/$schema"; fi
  run check-decision-log; cp "$t.schema" "$t/$schema"
  [[ "$rc" != 0 ]] && grep -qF "check-decision-log: $schema: unusable schema" <<<"$out" && ! grep -qF 'decision-log: ok' <<<"$out" \
    || { echo "check-decision-log test: schema '$1' did not fail closed" >&2; echo "$out" >&2; exit 1; }
}
schema_bad missing
schema_bad '{"type": "object", "required": ["why"'
schema_bad '[]'
# Preserve malformed-schema refusal while the library owns structural validation.
schema_bad '{"type": "object", "required": ["why", "why"]}'
schema_bad '{"type": "object", "properties": {"why": {"minLength": 1.0}}}'
schema_bad '{"type": "object", "properties": {"why": {"minLength": true}}}'
schema_bad '{"type": "object", "required": ["why"], "properties": {"why": {"type": "string", "maxLength": 9}}}'
schema_bad '{"type": "object", "required": ["why"], "patternProperties": {}}'
schema_bad '{"type": "object", "required": ["why"], "properties": {"why": {"type": ["string", "null"]}}}'
schema_bad '{"type": "object", "required": ["why"], "properties": {"why": {"type": "string", "pattern": "("}}}'
schema_bad '{"type": "object", "required": ["why"], "additionalProperties": {"type": "string"}}'
schema_bad '{"type": "object", "required": ["why"], "properties": {"why": {"type": "string", "pattern": "(?P<a>x)"}}}'
schema_bad '{"type": "object", "required": ["why"], "properties": {"why": {"type": "string", "pattern": "x\\Z"}}}'
# Fails closed: an unreadable tracked log (a dangling link) fails naming it.
ln -s missing "$t/$L"; g add -f "$L"; run check-decision-log; unplant "$L"
[[ "$rc" != 0 ]] && grep -qF "check-decision-log: $L: cannot read" <<<"$out" && ! grep -qF 'decision-log: ok' <<<"$out" \
  || { echo "check-decision-log test: unreadable log not reported" >&2; echo "$out" >&2; exit 1; }
# Fails closed: a broken python3 or git (a stub first on the caller's PATH, which the justfile keeps ahead of its
# tools) fails the gate, never decision-log: ok.
broken() {
  local h="$t.bin"; mkdir -p "$h"
  printf '#!/bin/sh\necho "%s: broken (check-decision-log test stub)" >&2\nexit 2\n' "$1" > "$h/$1"; chmod +x "$h/$1"
  set +e; out="$(cd "$t" && PATH="$h:$PATH" just check-decision-log 2>&1)"; rc=$?; set -e
  rm -rf "$h"
  [[ "$rc" != 0 ]] && grep -qF "$1: broken" <<<"$out" && ! grep -qF 'decision-log: ok' <<<"$out" || { echo "check-decision-log test: broken $1 passed check-decision-log" >&2; echo "$out" >&2; exit 1; }
}
broken python3
broken git
grep -qF 'git ls-files exited 2' <<<"$out" || { echo "check-decision-log test: broken git not reported as a git error" >&2; echo "$out" >&2; exit 1; }
broken node
grep -qF 'node exited 2; the check cannot pass' <<<"$out" || { echo "check-decision-log test: broken node not reported" >&2; echo "$out" >&2; exit 1; }
# No node on PATH: fails closed naming the fix.
mkdir -p "$t.bin"; ln -s "$(command -v git)" "$t.bin/git"
# Use the locked interpreter: PATH isolation removes uv too, not just node.
python="$(cd "$kit" && uv run --locked --offline --no-sync python -c 'import sys; print(sys.executable)')"
set +e; out="$(cd "$t" && PATH="$t.bin" "$python" scripts/check-decision-log 2>&1)"; rc=$?; set -e; rm -rf "$t.bin"
[[ "$rc" == 2 ]] && grep -qF 'check-decision-log: node not found on PATH: install node (Pi needs it too); the check cannot pass' <<<"$out" \
  || { echo "check-decision-log test: missing node did not fail closed" >&2; echo "$out" >&2; exit 1; }
rm -f "$t.schema"
[[ -z "$(g status --porcelain)" ]] || { echo "check-decision-log test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
# The gate includes check-decision-log: `just check` in the copy fails on a nested log line missing why, naming
# FILE:LINE. The copy keeps only this test of tests/*.sh, so the gate there starts no other test, and the guard
# above stops this one if the planted log ever got past check-decision-log.
# It selects only its own recipe item (PYTEST_ADDOPTS -k, pytest's own selection, #507), so no recipe before it runs.
find "$t/tests" -maxdepth 1 -name '*.sh' ! -name check-decision-log.sh -delete; g add -A
plant "$N" "$ok\n{$head,$tail}\n"
set +e; out="$(cd "$t" && env -u CI CHECK_DECISION_LOG_TEST_COPY=1 XDG_STATE_HOME="$t.home" PYTEST_ADDOPTS="--color=no -k 'test_recipe and check-decision-log'" just check 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] || { echo "check-decision-log test: $N missing why passed just check" >&2; exit 1; }
grep -qF "check-decision-log: $N:2: missing why" <<<"$out" || { echo "check-decision-log test: just check did not report $N:2: missing why" >&2; echo "$out" >&2; exit 1; }
# Only its own item ran (#507): pytest's own selection, through the real `just check`.
grep -qF "FAILED tests/gate/test_gate.py::test_recipe[check-decision-log]" <<<"$out" && grep -qE '^=+ 1 failed(, [0-9]+ deselected)? in ' <<<"$out" \
  || { echo "check-decision-log test: just check ran more than its own item" >&2; echo "$out" >&2; exit 1; }
echo "check-decision-log: ok (missing why, invalid JSON and non-object lines fail naming FILE:LINE and the field, nested included; valid, untracked and no logs pass; the schema drives fields and extras; adversarial forms and a broken checker fail closed)"
