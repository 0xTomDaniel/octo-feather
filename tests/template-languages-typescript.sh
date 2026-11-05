#!/usr/bin/env bash
# Integration test for each template's own check-languages (#362, owner rulings #225, #261), one gate item per template
# (#509; setup and check_template: tests/lib/template-languages.sh), here the TypeScript repo, made by
# `just new-repo typescript DEST --no-spec-chat`, offline (its packages copied from the run's one install from the pnpm
# store CI fills, tests/lib/prepared.py): a fresh repo passes `just check-languages`; each of its rules, broken once,
# fails it naming the file and the fix: a tracked unknown file, a Go file (unmapped), a file a tool's own list misses
# (an unattributed bash script, a dot-file .ts outside tsconfig's include), an `env -S` shebang scc cannot read, both
# pnpm pins, and ShellCheck's recipe out of the gate. Its check runs with python, python3, uv and uvx on PATH as stubs
# that record any call: none is called (that template needs no Python).
# Its trend line (comms #acceptance-report-gate-budget, issue-lifecycle #acceptance-merge-ask-gate-budget, #556): the
# tiers' just check appends one line of tier full, timing every GATE_RECIPES recipe and each test kind, and each
# just fast one of tier subset; a state dir it cannot create or write is a warning, the run still green; then
# `octo-feather-lane report` (fake gh and herdr, tests/fixtures/lane-report/) shows the repo's gate budget block from
# that full run against the template's gate-budget.toml, and `merge-ask` on its head shows its Gate time block.
# Run by `just check`.
# shellcheck source=tests/lib/template-languages.sh
source "$(dirname "$0")/lib/template-languages.sh"
unset HERDR_SESSION
export XDG_STATE_HOME="$t/xdg"
S="$XDG_STATE_HOME/octo-feather"; trend="$S/check-runs.jsonl"
check_template typescript
check_tiers typescript
[[ ! -e "$t/called" ]] || { out="$(cat "$t/called")"; fail "the TypeScript repo's check called Python or uv"; }

# One line per tier run: just check full, each just fast subset, all passed, on the repo's head.
H="$(g "$d" rev-parse HEAD)"
out="$(cat "$trend" 2>&1)" || fail "typescript: no trend file $trend"
got="$(GATE_RECIPES="$(cd "$d" && just --evaluate GATE_RECIPES)" python3 -c '
import json, os, sys
runs = [json.loads(l) for l in open(sys.argv[1])]
print(" ".join("%s:%s:%s" % (r["tier"], r["exit"], r["head"] == sys.argv[2]) for r in runs))
names = {s["name"] for s in runs[0]["steps"] if s["result"] == "ok"}
want = [f"tests/gate.test.ts > {x}" for x in os.environ["GATE_RECIPES"].split()] + ["tests/other.test.ts > doubles"]
print("missing:", *[w for w in want if w not in names], *([] if any(n.startswith("tests/cli.e2e.test.ts > ") for n in names) else ["e2e"]))
' "$trend" "$H")"
[[ "$got" == $'full:0:True subset:0:True subset:0:True\nmissing:' ]] || fail "typescript: trend lines (tier:exit:on head, then steps missing from the full run): $got"

# A state dir that cannot be created (its parent a file) or written: a warning on stderr, the run's verdict unchanged.
: >"$t/afile"; mkdir -p "$t/ro/octo-feather"; chmod 555 "$t/ro/octo-feather"
for x in "$t/afile" "$t/ro"; do
  set +e; out="$(cd "$d" && XDG_STATE_HOME="$x" PATH="$t/nopy:$PATH" pnpm exec vitest run tests/other.test.ts 2>&1)"; rc=$?; set -e
  [[ "$rc" == 0 ]] && grep -q "^trend: warning: line not written to check-runs.jsonl (.*); the verdict stands$" <<<"$out" \
    || fail "typescript: state dir $x: exit $rc, or no warning"
done
chmod 755 "$t/ro/octo-feather"
[[ "$(wc -l <"$trend")" == 3 ]] || fail "typescript: a run with another state dir wrote the trend file"

# The factory report and the merge ask show the repo's full gate against its gate-budget.toml: o/ts, PR #1 at H.
P="$t/pr/o__ts"; mkdir -p "$P" "$S/lanes" "$t/bin"
cp "$kit/tests/fixtures/lane-report/gh" "$kit/tests/fixtures/lane-report/herdr" "$t/bin/"; chmod +x "$t/bin/"*
echo '[]' >"$t/agents.json"; printf '[{"sha": "%s"}]\n' "$H" >"$P/commits.json"; cp "$d/gate-budget.toml" "$P/"
printf '{"state": "OPEN", "isDraft": false, "headRefName": "gh1", "headRefOid": "%s", "statusCheckRollup": [], "comments": [], "commits": [{"oid": "%s"}], "body": "## Merge ask\\n\\nHead: %s\\nBuilt: none\\nFailed: none\\n"}\n' \
  "$H" "$H" "${H:0:12}" >"$P/1.json"
printf 'supervisor = "w9:p1"\nrepository = "o/ts"\nissue = "gh1"\ngoal = "ts"\npr = 1\nstarted_at = "2026-11-04T08:00:00Z"\nlast_handoff_at = "2026-11-04T09:00:00Z"\nwaiting_on = ""\n' >"$S/lanes/ts.toml"
export FAKE_GH_PRS="$t/pr" FAKE_HERDR_AGENTS="$t/agents.json"
budget='(within budget, [0-9.]+s to spare|OVER BUDGET by [0-9.]+s) \(budget 60s\)'
fullre="  full gate: [0-9.]+s, head ${H:0:12}, started [0-9TZ:-]+ \([0-9hm]+ ago\): $budget"
slow="  slowest: .*tests/gate.test.ts > check-ts [0-9.]+s"
out="$(PATH="$t/bin:$PATH" "$kit/scripts/octo-feather-lane" report 2>&1)" || fail "typescript: report exited non-zero: $out"
block="$(sed -n '/^gate budget o\/ts:/,/^owner queue/p' <<<"$out")"
grep -qx "gate budget o/ts: the latest passed full gate run against gate-budget.toml on o/ts's default branch" <<<"$block" \
  && grep -qE "^$fullre\$" <<<"$block" && grep -qE "^$slow" <<<"$block" || fail "typescript: report's gate budget block: $out"
set +e; out="$(cd "$d" && PATH="$t/bin:$PATH" "$kit/scripts/octo-feather-lane" merge-ask 1 --repo o/ts --base "$H" 2>&1)"; set -e
grep -qx "Gate time (the full gate on the final head against gate-budget.toml at ${H:0:12}; .*" <<<"$out" \
  && grep -qE "^$fullre\$" <<<"$out" && grep -qE "^$slow" <<<"$out" || fail "typescript: merge-ask's Gate time block: $out"
echo "template-languages-typescript: ok (typescript repo green fresh; unknown, Go, uncovered file, env -S shebang, both pnpm pins and a gate recipe out each named; typescript without Python; trend lines full for just check with every gate step, subset for just fast, a bad state dir a warning; report and merge-ask show its gate budget)"
