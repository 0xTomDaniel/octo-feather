#!/usr/bin/env bash
# Role prose and kit skills say "the tracker skill" (spec skills #tracker-role-line, issue-lifecycle
# #acceptance-no-github-issue): agents/*.md and every kit skill's .md outside the vendored skills (Skillfile
# `github` entries) and the tracker skills (each tracker scripts/pi-role resolves a role's {tracker} to, asked
# through its --json command) name no gh issue command and no Linear, so no agent files or closes a GitHub
# issue for a Linear lane. Each hit names the file, line and the fix. Proves the scan finds a planted hit in a
# kit copy. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "tracker-prose test: $*" >&2; exit 1; }
trackers() { # KIT: the tracker skill folder of each tracker KIT's pi-role knows, one per line
  local p; p="$(mktemp -d "$t/probe.XXXX")"; mkdir -p "$p/agents" "$p/tgt"; ln -s "$1/.agents" "$p/.agents"
  printf -- '---\nname: probe\nskills: {tracker}\n---\n' > "$p/agents/probe.md"; git -C "$p/tgt" init -q
  echo 'tracker = "no-such-tracker"' > "$p/tgt/.octo-feather.toml"
  local e names n; e="$(cd "$p/tgt" && "$1/scripts/pi-role" --json "$p/agents/probe.md" 2>&1)" && fail "pi-role took an unknown tracker: $e"
  names="${e##*the kit has: }"; [[ "$names" != "$e" && "$names" != none ]] || fail "pi-role named no kit tracker: $e"
  for n in ${names//,/ }; do
    echo "tracker = \"$n\"" > "$p/tgt/.octo-feather.toml"
    (cd "$p/tgt" && "$1/scripts/pi-role" --json "$p/agents/probe.md") \
      | python3 -c 'import json,os,sys; a=json.load(sys.stdin)["args"]; print(os.path.basename(a[a.index("--skill") + 1]))' \
      || fail "pi-role --json did not resolve tracker $n"
  done
}
scan() { # KIT: one line per hit, `<file>:<line>: <what>; fix: ...`
  local ts; mapfile -t ts < <(trackers "$1")
  python3 - "$1" "${ts[@]}" <<'PY'
import os, re, sys
root = sys.argv[1]
skip = set(sys.argv[2:])
skip |= {w[2] for w in (x.split() for x in open(os.path.join(root, "Skillfile"))) if len(w) > 2 and w[:2] == ["github", "skill"]}
files = [os.path.join("agents", f) for f in sorted(os.listdir(os.path.join(root, "agents"))) if f.endswith(".md")]
sk = os.path.join(root, ".agents", "skills")
for s in sorted(os.listdir(sk)):
    if s in skip: continue
    for d, _, fs in sorted(os.walk(os.path.join(sk, s))):
        files += [os.path.relpath(os.path.join(d, f), root) for f in sorted(fs) if f.endswith(".md")]
BAD = [(re.compile(r"\bgh\s+issue\b"), "names a gh issue command"),
       (re.compile(r"\bgh\s+api\b[^\n`]*\bissues\b"), "names a gh api issues call"),
       (re.compile(r"\bLinear\b"), "names Linear")]
for f in files:
    for n, line in enumerate(open(os.path.join(root, f), encoding="utf-8"), 1):
        for rx, what in BAD:
            if rx.search(line):
                print(f"{f}:{n}: {what}; fix: say 'the tracker skill' and name its script (issue-view, issue-create, "
                      "issue-comment, issue-done, pr-line, lane-key), never a tracker's own command or name (spec skills #tracker-role-line)")
PY
}
mapfile -t kts < <(trackers "$kit"); [[ " ${kts[*]} " == *" github-issues "* ]] || fail "tracker skills via pi-role: ${kts[*]}"
for s in "${kts[@]}"; do [[ -f "$kit/.agents/skills/$s/SKILL.md" ]] || fail "pi-role tracker skill $s has no SKILL.md"; done
out="$(scan "$kit")"
[[ -z "$out" ]] || { echo "$out" >&2; fail "role prose or a kit skill names a tracker; fix each line above"; }
# The scan sees a planted hit in a role and in a local skill, and none in a vendored or tracker skill.
mkdir -p "$t/kit/scripts"; cp -r "$kit/agents" "$kit/.agents" "$kit/Skillfile" "$t/kit/"; cp "$kit/scripts/pi-role" "$t/kit/scripts/"
echo 'File it with `gh issue create`.' >> "$t/kit/agents/director.md"
echo 'Close it in Linear.' >> "$t/kit/.agents/skills/push/SKILL.md"
echo 'Run gh issue close 5.' >> "$t/kit/.agents/skills/tdd/SKILL.md"
echo 'Run gh issue close 5.' >> "$t/kit/.agents/skills/github-issues/SKILL.md"
out="$(scan "$t/kit")"
[[ "$(wc -l <<<"$out")" == 2 && "$out" == *"agents/director.md:"*": names a gh issue command; fix: say 'the tracker skill'"* \
   && "$out" == *".agents/skills/push/SKILL.md:"*": names Linear; fix:"* ]] || fail "planted hits: $out"
echo "tracker-prose: ok (agents and local non-tracker skills name no gh issue command and no Linear; planted hits found, vendored and tracker skills skipped)"
