#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape), driven as
# commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-review through a review case and --review (rules: octo-feather-qa --help, Review;
# the case field: schema.md, Case): awaiting review with its output, a recorded verdict and note shown, the next run
# showing them beside its new output; check-evals refusing a review case with no question or with facts.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
mkdir -p "$t/rv/rv/reference"; cp -r "$t/good/fixtures" "$t/rv/"
echo '{"suite": "rv", "kind": "role-transcript", "description": "stub review", "max_tool_calls": 10, "timeout_s": 60}' > "$t/rv/rv/suite.json"
essay() {   # essay SAY: the review case, its stub writing notes.md and saying SAY
  python3 - "$t/rv/rv" "$1" <<'PY'
import json, sys
d, say = sys.argv[1:]
steps = [["bash", "echo hi > notes.md"], ["say", say]]
json.dump([{"id": "essay", "role": "implementer", "fixture": "fx", "task": "Write the notes. STUB-STEPS:" + json.dumps(steps),
            "review": {"question": "Do the notes answer the brief?"}}], open(f"{d}/cases.json", "w"))
json.dump({"essay": {"facts": []}}, open(f"{d}/reference/expectations.json", "w"))
PY
}
essay "The notes say hi."
last() { ls -dt "$t"/out/*/ | head -1; }

# Run: awaiting review, never a pass (exit 1), its output shown and kept.
run 1 "$Q" --evals "$t/rv"
grep -q "^REVIEW rv/essay: awaiting review: Do the notes answer the brief?; changed files: notes.md \[stop: exit, 2 tool calls, " <<< "$out" \
  || fail "no awaiting review line with the question and changed files: $out"
grep -q "^  output: final message: The notes say hi.$" <<< "$out" && grep -q "^  latest review: none$" <<< "$out" \
  || fail "output or latest review not shown: $out"
grep -q "^qa: 0/1 passed" <<< "$out" || fail "a review case counted as passed: $out"
d1="$(last)"; id1="$(basename "$d1")"
python3 - "$d1" <<'PY' || fail "review artifacts wrong"
import json, sys
c = f"{sys.argv[1]}/rv/essay"
k = json.load(open(f"{c}/review.json")); r = json.load(open(f"{c}/result.json"))
assert k == {"question": "Do the notes answer the brief?", "final_message": "The notes say hi.", "changed_files": ["notes.md"]}, k
assert r["verdict"] == "REVIEW" and r["review"] == {"question": "Do the notes answer the brief?"}, r
PY

# Shown awaiting review until a verdict is recorded; then the verdict and note.
run 0 "$Q" --review "$d1" rv/essay
grep -q "^REVIEW rv/essay: awaiting review (run $id1)$" <<< "$out" && grep -q "^  output: final message: The notes say hi.$" <<< "$out" \
  || fail "--review show before a verdict: $out"
run 0 "$Q" --review "$d1" rv/essay pass "Clear and short."
grep -q "^REVIEWED rv/essay: pass (run $id1, kit [0-9a-f]\{12\}, [0-9T:-]*Z): Clear and short.$" <<< "$out" || fail "recorded verdict not shown: $out"
run 0 "$Q" --review "$d1" rv/essay
grep -q "^REVIEWED rv/essay: pass (run $id1, .*): Clear and short.$" <<< "$out" || fail "--review show after a verdict: $out"
[[ "$(wc -l < "$t/out/reviews/rv/essay.jsonl")" == 1 ]] || fail "the verdict is not one line in the reviews file"

# The next run: the latest verdict and note beside its new output.
essay "The notes say hello."
run 1 "$Q" --evals "$t/rv" --runs 2
grep -q "^REVIEW rv/essay: 0/2 runs passed" <<< "$out" || fail "a review case's runs: want REVIEW: $out"
[[ "$(grep -c "^  output: final message: The notes say hello.$" <<< "$out")" == 2 ]] || fail "new output not shown per run: $out"
[[ "$(grep -c "^  latest review: pass (run $id1, .*): Clear and short.$" <<< "$out")" == 2 ]] || fail "latest verdict not shown beside the new output: $out"

# Usage: a bad verdict, a blank note, a case that is no review case: 64.
run 64 "$Q" --review "$d1" rv/essay maybe "x"
run 64 "$Q" --review "$d1" rv/essay fail " "
run 0 "$Q" --evals "$t/evals" --case reads
run 64 "$Q" --review "$(last)" trig/reads pass "x"
grep -q "not a review case" <<< "$out" || fail "a graded case took a verdict: $out"

# Shape: a review case needs its question, and has no facts.
rm -rf "$t/evals"; cp -r "$t/rv" "$t/evals"
python3 - "$t/evals/rv" <<'PY'
import json, sys
d = sys.argv[1]; c = json.load(open(f"{d}/cases.json")); c[0]["review"] = {}; json.dump(c, open(f"{d}/cases.json", "w"))
PY
run 1 "$C" "$t/evals"; grep -qF "rv/cases.json case essay: field review.question: missing or blank" <<< "$out" || fail "review with no question: $out"
bad 'e["essay"]["facts"] = [{"fact": "skill_read", "skill": "tdd"}]' "rv/reference/expectations.json case essay: field facts: a review case has none" "$t/rv" rv
echo "qa-review: ok (awaiting review with its output, verdict and note recorded and shown, the next run shows them beside its new output, shape refusals)"
