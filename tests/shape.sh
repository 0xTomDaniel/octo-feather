#!/usr/bin/env bash
# Integration test for scripts/octo-feather-shape: exactly the shaping skills,
# spec-chat-shape from the target repo, nothing from home. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
mkdir -p "$t/home/.agents/skills/spec-chat-shape" "$t/repo/.agents/skills/spec-chat-shape"
echo "# home" > "$t/home/.agents/skills/spec-chat-shape/SKILL.md"; echo "# repo" > "$t/repo/.agents/skills/spec-chat-shape/SKILL.md"
git -c init.defaultBranch=main init -q "$t/repo"; export T="$t"
got="$(cd "$t/repo" && HOME="$t/home" "$kit/scripts/octo-feather-shape" --json | python3 -c 'import json,sys,os; a=json.load(sys.stdin)["args"]; print(" ".join(sorted(a[i+1].replace(os.environ["T"], "T") for i,x in enumerate(a) if x == "--skill")) + (" no-skills" if "--no-skills" in a else ""))' )"
want="$kit/.agents/skills/codebase-design $kit/.agents/skills/domain-modeling $kit/.agents/skills/grill-with-docs $kit/.agents/skills/grilling $kit/.agents/skills/improve-codebase-architecture $kit/.agents/skills/sharpen T/repo/.agents/skills/spec-chat-shape no-skills"
[[ "$got" == "$want" ]] || { echo "shape test: skills: $got" >&2; exit 1; }
echo "shape: ok (shaping skills only, spec-chat-shape from the repo, not home)"
