#!/usr/bin/env bash
# Demo for #173: both --help name the eval-cases skill as schema owner; check-evals on a tmp evals copy with one
# field broken at a time (at least one per schema section) fails naming a field, and the skill's schema states it.
# Run from the kit root: evidence/gh173-schema-owner/demo.sh
set -euo pipefail
kit="$(pwd)"; S=.agents/skills/eval-cases/references/schema.md
echo "== scripts/check-evals --help (owner lines)"; scripts/check-evals --help | grep -n "eval-cases"
echo "== scripts/octo-feather-qa --help (owner lines)"; scripts/octo-feather-qa --help | grep -n "eval-cases\|schema"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fresh() { rm -rf "$t/evals"; cp -r "$kit/evals" "$t/evals"; ln -sfn "$kit/evidence" "$t/evidence"; }
fresh; echo "== baseline copy: $(scripts/check-evals "$t/evals")"
n=0; bad=0
# break SECTION FILE PYTHON: load FILE (relative to the copy) as o, run PYTHON, write it back, run check-evals.
brk() {
  local sec="$1" f="$2" py="$3"; fresh
  python3 - "$t/evals/$f" "$py" <<'EOF'
import json, sys
p, code = sys.argv[1], sys.argv[2]
o = json.load(open(p)); exec(code); json.dump(o, open(p, "w"))
EOF
  set +e; out="$(scripts/check-evals "$t/evals" 2>&1)"; rc=$?; set -e
  # the field named: `field <dotted path>` (its last segment that is a key, not a classifier id or index), or a
  # coverage refusal's `no case for <field>`; stated in the schema as `field` or "field".
  line="$(grep -m1 -E ': field |no case for ' <<<"$out" || true)"
  if [[ "$line" == *": field "* ]]; then fld="$(sed -E 's/.*: field ([^:]+):.*/\1/' <<<"$line")"
  else fld="$(sed -E 's/.*no case for ([a-z_]+).*/\1/' <<<"$line")"; fi
  leaf="$(tr '.' '\n' <<<"${fld%%[[]*}" | grep -E '^[a-z_]+$' | tail -1)"
  if [[ "$rc" == 1 && -n "$leaf" ]] && grep -qE "[\`\"]$leaf[\`\"]" "$kit/$S"; then st=ok; else st=MISS; bad=$((bad + 1)); fi
  n=$((n + 1)); printf '%-28s exit %s  %s\n%-28s field %s stated in schema: %s\n' "[$sec]" "$rc" "$line" "" "$leaf" "$st"
}
RT=role-transcripts; ST=skill-triggers; JG=judgment-exact-or-proxy
brk Suite            $RT/suite.json 'o["kind"] = "chat"'
brk Suite            $RT/suite.json 'o["timeout_s"] = 0'
brk Suite            $RT/suite.json 'o["covers"] = "role-skills"'
brk Case             $RT/cases.json 'o[0]["id"] = "Bad_Id"'
brk Case             $RT/cases.json 'o[0]["role"] = "nobody"'
brk Case             $ST/cases.json 'o[0]["split"] = "test"'
brk Case             $ST/cases.json 'o[0]["should_trigger"] = "yes"'
brk Case/setup       $RT/cases.json 'o[0]["branch"] = "main"'
brk Case/setup       $RT/cases.json 'o[4]["head"]["message"] = " "'
brk Case/setup       $RT/cases.json 'o[8]["origin"] = False'
brk Facts            $RT/reference/expectations.json 'o["implementer-python-ticket"]["facts"][0]["fact"] = "skill_seen"'
brk Facts            $RT/reference/expectations.json 'o["implementer-python-ticket"]["facts"][0]["skill"] = "no-such-skill"'
brk "Before targets" $RT/reference/expectations.json 'o["implementer-python-ticket"]["facts"][0]["before"] = "test_run"'
brk "Before targets" $RT/reference/expectations.json 'o["implementer-python-ticket"]["facts"][0]["before"] = "git_push"'
brk "Attempt record" isolation/reference/expectations.json 'k = next(iter(o)); o[k]["facts"] = [{"fact": "attempt_blocked", "kind": "network"}]'
brk "Final JSON"     $RT/reference/expectations.json 'o["implementer-python-ticket"]["facts"].append({"fact": "declared", "field": "rung", "in": []})'
brk "Field lines"    $RT/reference/expectations.json 'o["implementer-python-ticket"]["facts"].append({"fact": "field_lines", "field": "Checks"})'
brk "Field lines"    $RT/reference/expectations.json 'o["implementer-python-ticket"]["facts"].append({"fact": "field_lines", "field": "Check", "every": {"colour": ["x"]}})'
brk "Branch paths"   $RT/reference/expectations.json 'o["implementer-python-ticket"]["facts"].append({"fact": "branch_paths", "touched": ["/abs"]})'
brk Leaks            $RT/cases.json 'o[0]["task"] += " Read .agents/skills/tdd/SKILL.md first."'
brk Coverage         $ST/cases.json '[c.update(role="director") for c in o if c["role"] == "implementer" and c["split"] == "held-out" and not c["should_trigger"]]'
brk "Judgment suite" $JG/question.json 'o["labels"] = ["exact"]'
brk "Judgment suite" $JG/cases.json 'o[0]["split"] = "dev"'
brk "Judgment suite" $JG/reference/expectations.json 'k = next(iter(o)); o[k]["reason"] = "two\nlines"'
brk Calibration      $JG/suite.json 'o["calibration"]["held_out"]["brier"] = 3'
brk Calibration      $JG/suite.json 'o["calibration"]["threshold"]["accepted"] = "no"'
brk Calibration      $JG/suite.json 'o["calibration"]["evidence"] = "../outside.md"'
brk "Judgment model" judgment-model.json 'o["model"] = "openrouter/~typesafe/jev-latest"'
brk "Judgment model" judgment-model.json 'o["chosen"] = 1'
brk Classifiers      classifiers.json 'o["owner"] = ""'
brk Classifiers      classifiers.json 'o["moving_alias"].append(next(iter(o["pinned"])))'
brk Classifiers      classifiers.json 'k = next(iter(o["yes_no_only"])); del o["yes_no_only"][k]["error"]'
echo "== $n breaks, $bad not failing or naming a field the schema does not state"
[[ "$bad" == 0 ]]
