#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: field_lines column-0 only (bullet and fenced fail; none, every, includes, Owner restated, other
# fields, a two-word field), tool_called (an error or empty result skipped, a named tool's text result passes, none
# called fails), branch_paths committed and uncommitted (untouched, touched).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
mk_fl
run 1 "$Q" --evals "$t/fl"
fl() { grep -E "^$1 fl/$2: " <<< "$out" | grep -qF "$3" || fail "fl $2: want $1 with '$3': $out"; }
fl PASS fnone 'field_lines Check: `Checks: none`; field_lines Check: `Checks: none`; every line in {"class": ["exact"]}; field_lines Blocked: 1 line(s) [{"text": "the scan (no criterion asks for it)"}]; branch_paths: changed src/a.py, src/b.py; none under scripts/, justfile; each of src/ changed'
fl FAIL fbullet 'field_lines Check: report classifies no check'
fl FAIL ffenced 'field_lines Check: report classifies no check'
fl FAIL fexact 'branch_paths: changed scripts/check-exec (untouched: scripts/, justfile)'
grep -E '^FAIL fl/fexact: ' <<< "$out" | grep -qF 'field_lines Check:' && fail "fexact: a well-formed exact Check line failed: $out"
fl FAIL fproxy 'field_lines Check: [{"path": "scripts/check-exec", "rule": "every script is executable", "owner": "criterion exec-bit", "reads": "git index modes", "class": "proxy"}] outside {"class": ["exact"]}'
fl PASS fowner 'holds {"path": "docs/adr/0099-x.md", "restated": "README.md"}; {"path": "docs/adr/0099-x.md", "restated": "AGENTS.md"}; {"path": "docs/adr/0099-x.md", "restated": "skills/s.md"}'
fl FAIL fonone 'field_lines Blocked: no column-0 `Blocked:` line with a value outside code blocks'
grep -E '^FAIL fl/fonone: ' <<< "$out" | grep -qF 'field_lines Owner:' && fail "fonone: Owners: none failed: $out"
# tool_called (schema.md, Tool call): an error result skipped, a named tool's text result passes; a two-word field.
fl PASS fweb 'tool_called web_a | web_b: tool call 3 web_b {"query": "q"} returned 20 characters; field_lines Prior art: 1 line(s) [{"text": "PyYAML 6.0.2 | released: 2024-08-06 | license: MIT"}]'
fl FAIL fwebnone 'tool_called web_a | web_b: call 2 web_a: error'
fl FAIL fwebnone 'field_lines Prior art: no column-0 `Prior art:` line'
fl FAIL fwebempty 'tool_called web_a | web_b: call 2 web_b: empty result'
fl FAIL fwebno 'tool_called web_a | web_b: no call to any of them in 2 tool calls'
echo "qa-field-lines: ok (field_lines column-0 only (bullet and fenced fail; none, every, includes, Owner restated, other fields, a two-word field), tool_called (an error or empty result skipped, a named tool's text result passes, none called fails), branch_paths committed and uncommitted (untouched, touched))"
