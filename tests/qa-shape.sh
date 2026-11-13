#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape),
# driven as commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves: the shape check (rules: .agents/skills/eval-cases/references/schema.md) names case and field for
# skill-trigger and role-transcript suites, the exact leak rule, and octo-feather-qa refuses a malformed suite (2).
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
mk_rt; mk_fl; mk_ran
# Shape check (rules: schema.md, by section; output and exit: check-evals --help, octo-feather-qa --help).
bad 'del c[0]["task"]' "trig/cases.json case reads: field task: missing"
bad 'del c[1]["split"]' "trig/cases.json case near: field split: missing"
bad 'c[0]["facts"] = e["reads"]["facts"]' "trig/cases.json case reads: field facts: unknown field"
bad 'e["reads"]["facts"][0]["fact"] = "skill_vibes"' "case reads fact #1: field fact: unknown fact type 'skill_vibes'"
bad 'e["reads"]["facts"][0]["skill"] = "nope"' "case reads fact #1: field skill: no .agents/skills/nope/SKILL.md in the kit or in fixture fx"
# A fixture-only skill resolves in the tree the agent sees: the head fixture's when the case has one (schema.md, Facts).
bad 'c[[x["id"] for x in c].index("repoload")]["head"] = {"fixture": "fx2", "branch": "hb", "message": "m"}' "case repoload fact #1: field skill: no .agents/skills/repo-only/SKILL.md in the kit or in fixture fx2" "$t/rt-good" rt
bad 'del e["quiet"]' "trig/cases.json case quiet: field id: no expectations"
bad 'e["ghost"] = e["quiet"]' "trig/reference/expectations.json case ghost: field id: no case in cases.json"
bad 'c[0]["task"] += " Read .agents/skills/tdd/SKILL.md first."' "case reads: field task: shows the agent its grade (skill path tdd/SKILL.md)"
bad 'c[2]["task"] += " Graded on " + json.dumps(e["quiet"]["facts"][0])' "case quiet: field task: shows the agent its grade (fact #1 as JSON"
# Leaks (rule: schema.md, Leaks): a fact reordered and reindented; a skill path's component forms.
bad 'c[2]["task"] += " Grade: " + json.dumps(dict(reversed(list(e["quiet"]["facts"][0].items()))), indent=3)' "case quiet: field task: shows the agent its grade (fact #1 as JSON"
bad 'c[0]["task"] += " See skills/tdd/ for it."' "case reads: field task: shows the agent its grade (skill path skills/tdd)"
rm -rf "$t/evals"; cp -r "$t/good" "$t/evals"
python3 - "$t/evals/trig" <<'EOF'
import json, sys
d = sys.argv[1]; c = json.load(open(f"{d}/cases.json")); e = json.load(open(f"{d}/reference/expectations.json"))
c[0]["task"] += ' Use the implement skill; .agents/skills/implement-spec/SKILL.md and skills/implement-spec/ are not it; {"fact": "skill_read"}'
e["reads"]["facts"][0]["skill"] = "implement"
json.dump(c, open(f"{d}/cases.json", "w")); json.dump(e, open(f"{d}/reference/expectations.json", "w"))
EOF
run 0 "$C" "$t/evals"   # a neighbour skill's path, the skill's name in prose, a JSON object that is no fact (schema.md, Leaks)
# Role-transcript fields and facts (rules: schema.md, Case, Facts, Before targets).
bad 'c[0]["branch"] = "x"' "trig/cases.json case reads: field branch: unknown field; only a role-transcript case sets up a repo"
bad 'c[0]["branch"] = "a..b"' "rt/cases.json case order: field branch: must be a branch name" "$t/rt-good" rt
bad 'c[0]["origin"] = False' "rt/cases.json case order: field origin: must be true (leave it out for false)" "$t/rt-good" rt
bad 'c[0]["fake_gh"] = "yes"' "rt/cases.json case order: field fake_gh: must be true" "$t/rt-good" rt
bad 'del c[4]["head"]["message"]' "rt/cases.json case setup: field head.message: missing" "$t/rt-good" rt
bad 'c[4]["head"]["fixture"] = "nope"' "rt/cases.json case setup: field head.fixture: no fixture dir" "$t/rt-good" rt
bad 'c[4]["head"]["branch"] = "work"' "rt/cases.json case setup: field head.branch: must be a new branch name" "$t/rt-good" rt
bad 'c[4]["head"] = "fx2"' "rt/cases.json case setup: field head: must be an object" "$t/rt-good" rt
bad 'del c[0]["origin"]' "case order fact #4: field before: git_push needs the case's origin: true" "$t/rt-good" rt
bad 'del c[0]["fake_gh"]' "case order fact #5: field before: gh_call needs the case's fake_gh: true" "$t/rt-good" rt
bad 'c[0]["fixture"] = "fx"' "case order fact #1: field before: test_write needs fixture fx to declare its tests" "$t/rt-good" rt
bad 'c[0]["head"] = {"fixture": "fx2", "branch": "hb", "message": "m"}' "case order fact #1: field before: test_write needs fixture fx2 to declare its tests" "$t/rt-good" rt
bad 'e["order"]["facts"][0]["before"] = "lunch"' "case order fact #1: field before: must be one of" "$t/rt-good" rt
bad 'e["incl"]["facts"][0]["items"] = [{"test": 1}]' "case incl fact #1: field items: must be a non-empty list of non-empty objects of string values" "$t/rt-good" rt
bad 'e["incl"]["facts"][0]["items"] = []' "case incl fact #1: field items: must be a non-empty list" "$t/rt-good" rt
bad 'del e["incl"]["facts"][0]["field"]' "case incl fact #1: field field: missing" "$t/rt-good" rt
bad 'c[0]["should_trigger"] = False' "case reads: field should_trigger: false, but no skill_not_read fact"
bad 'e["reads"]["facts"].append({"fact": "attempt_blocked", "kind": "vibes"})' "case reads fact #2: field kind: must be one of ['credential', 'herdr', 'lane_state', 'network', 'repo'], got 'vibes'"
bad 'e["reads"]["facts"].append({"fact": "declared", "field": "", "in": []})' "case reads fact #2: field field: must be a non-empty string"
bad 'e["reads"]["facts"].append({"fact": "declared", "field": "rung", "in": [1]})' "case reads fact #2: field in: must be a non-empty list of strings"
bad 'del e["fnone"]["facts"][0]["field"]' "case fnone fact #1: field field: missing" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["lines"] = 1' "case fnone fact #1: field lines: unknown field for field_lines" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["field"] = "Checks"' "case fnone fact #1: field field: must be a field name" "$t/fl-good" fl
bad 'e["fnone"]["facts"][0]["none"] = "yes"' "case fnone fact #1: field none: only true" "$t/fl-good" fl
bad 'e["fexact"]["facts"][0]["includes"] = [{"klass": "exact"}]' "case fexact fact #1: field includes: must be a non-empty list of non-empty objects of string values, keys from" "$t/fl-good" fl
bad 'e["fexact"]["facts"][0]["every"] = {"class": "exact"}' "case fexact fact #1: field every: must be a non-empty object of string lists" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3] = {"fact": "branch_paths"}' "case fnone fact #4: field untouched: missing" "$t/fl-good" fl
bad 'del e["rpass"]["facts"][0]["program"]' "case rpass fact #1: field program: missing" "$t/ran-good" ran
bad 'e["rpass"]["facts"][0]["program"] = "a/b"' "case rpass fact #1: field program: must be a command name" "$t/ran-good" ran
bad 'e["rpass"]["facts"][0]["args"] = "lane show"' "case rpass fact #1: field args: must be a list of strings" "$t/ran-good" ran
bad 'e["rpass"]["facts"][0]["count"] = -1' "case rpass fact #1: field count: must be an integer >= 0, got -1" "$t/ran-good" ran
bad 'e["rpass"]["facts"][0]["count"] = True' "case rpass fact #1: field count: must be an integer >= 0, got True" "$t/ran-good" ran
bad 'e["rpass"]["facts"][0]["exit"] = 0' "case rpass fact #1: field exit: unknown field for ran" "$t/ran-good" ran
bad 'e["fweb"]["facts"][0]["tools"] = []' "case fweb fact #1: field tools: must be a non-empty list of tool names" "$t/fl-good" fl
bad 'e["fweb"]["facts"][0]["tools"] = ["web a"]' "case fweb fact #1: field tools: must be a non-empty list of tool names" "$t/fl-good" fl
bad 'del e["fweb"]["facts"][0]["tools"]' "case fweb fact #1: field tools: missing" "$t/fl-good" fl
bad 'e["fweb"]["facts"][1]["field"] = "Prior  art"' "case fweb fact #2: field field: must be a field name" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["untouched"] = "scripts/"' "case fnone fact #4: field untouched: must be a non-empty list of relative paths" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["touched"] = ["../x"]' "case fnone fact #4: field touched: must be a non-empty list of relative paths" "$t/fl-good" fl
bad 'e["fnone"]["facts"][3]["paths"] = []' "case fnone fact #4: field paths: unknown field for branch_paths" "$t/fl-good" fl
bad 'c[0]["role"] = "nobody"' "case reads: field role: no kit role agents/nobody.md"
run 2 "$Q" --evals "$t/evals"
grep -q "field role: no kit role" <<< "$out" && ! grep -q "qa: run " <<< "$out" || fail "evals ran a malformed suite: $out"
echo "qa-shape: ok (exact leak rule, shape check names case and field, a malformed suite not run)"
