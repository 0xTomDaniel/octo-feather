#!/usr/bin/env bash
# Integration test for scripts/pi-role's externalSkills lookup: the target repo's
# .agents/skills (main checkout, seen from a lane worktree), never home. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
g() { git -c user.name=t -c user.email=t@t -c init.defaultBranch=main "$@"; }
mkdir -p "$t/home/.agents/skills/spec-chat-review" "$t/repo"
echo "# home" > "$t/home/.agents/skills/spec-chat-review/SKILL.md"
g init -q "$t/repo"; echo '.agents/skills/spec-chat-*' > "$t/repo/.gitignore"
g -C "$t/repo" add -A; g -C "$t/repo" commit -qm init; g -C "$t/repo" worktree add -q -b gh1 "$t/gh1"
mkdir -p "$t/repo/.agents/skills/spec-chat-shape"; echo "# repo" > "$t/repo/.agents/skills/spec-chat-shape/SKILL.md"
args="$(cd "$t/gh1" && HOME="$t/home" "$kit/scripts/pi-role" --json "$kit/agents/supervisor.md" 2>"$t/err")"
grep -q "\"$t/repo/.agents/skills/spec-chat-shape\"" <<<"$args" || { echo "pi-role test: repo skill not found from the lane worktree: $args" >&2; exit 1; }
! grep -q "$t/home/.agents" <<<"$args" || { echo "pi-role test: a home skill loaded" >&2; exit 1; }
grep -q "external skill spec-chat-review not installed" "$t/err" || { echo "pi-role test: no warning for the missing skill" >&2; exit 1; }
echo "pi-role: ok (repo skill from a lane worktree, home ignored, missing one warned)"
