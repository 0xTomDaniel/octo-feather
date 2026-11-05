#!/usr/bin/env bash
# Integration test for `just shape` (roles#acceptance-shaper-launch): the shaper role's pi-role launch,
# its model, thinking and tools, exactly its listed kit skills, Spec Chat's from the target repo, none
# from home. Run by `just check`; it prints the launch it checks.
# criterion: roles#acceptance-shaper-launch
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
for s in spec-chat-shape spec-chat-review; do
  mkdir -p "$t/home/.agents/skills/$s" "$t/repo/.agents/skills/$s"
  echo "# home" > "$t/home/.agents/skills/$s/SKILL.md"; echo "# repo" > "$t/repo/.agents/skills/$s/SKILL.md"
done
mkdir -p "$t/home/.agents/skills/tdd"; echo "# home" > "$t/home/.agents/skills/tdd/SKILL.md"
git -c init.defaultBranch=main init -q "$t/repo"; export T="$t"
(cd "$t/repo" && HOME="$t/home" XDG_CACHE_HOME="$t/cache" PATH="$kit/scripts:$PATH" just --justfile "$kit/justfile" shape --json) > "$t/launch.json"
python3 -c 'import json, sys; a = json.load(sys.stdin)["args"]; print("just shape --json launch:", *a[:a.index("--append-system-prompt")] if "--append-system-prompt" in a else a, sep="\n  ")' < "$t/launch.json"
got="$(python3 -c '
import json, os, sys
a = json.load(sys.stdin)["args"]
val = lambda f: a[a.index(f) + 1] if f in a else "-"
print(" ".join(sorted(a[i + 1].replace(os.environ["T"], "T") for i, x in enumerate(a) if x == "--skill")))
print(val("--model"), val("--thinking"), val("--tools"), val("--octo-feather-role"), *[f for f in ("--no-skills", "--no-mcp") if f in a])' < "$t/launch.json")"
want="$kit/.agents/skills/codebase-design $kit/.agents/skills/domain-modeling $kit/.agents/skills/grill-with-docs $kit/.agents/skills/grilling $kit/.agents/skills/improve-codebase-architecture $kit/.agents/skills/sharpen T/repo/.agents/skills/spec-chat-review T/repo/.agents/skills/spec-chat-shape
anthropic/claude-opus-5-5 high read,grep,find,ls,bash,edit,write,codemode,mcp__parallel__*,mcp__exa__* shaper --no-skills"
[[ "$got" == "$want" ]] || { printf 'shape test: launch:\n%s\nwant:\n%s\n' "$got" "$want" >&2; exit 1; }
echo "shape: ok (pi-role launch of agents/shaper.md, its kit skills, Spec Chat's from the repo, none from home)"
