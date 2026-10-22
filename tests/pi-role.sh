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

# #77: a headless run (-p or --print) drops the parent route and Herdr ids; a pane launch keeps them.
# A fake pi on PATH writes the env it was exec'd with.
mkdir -p "$t/bin"
printf '#!/usr/bin/env bash\nenv > "$PI_ENV_OUT"\n' > "$t/bin/pi"; chmod +x "$t/bin/pi"
route=(OCTO_FEATHER_PARENT=fake:p1 HERDR_PANE_ID=fake:p0 HERDR_TAB_ID=fake:t0 HERDR_WORKSPACE_ID=fake)
child() { local out="$t/env.$1"; shift
  (cd "$t/gh1" && env PATH="$t/bin:$PATH" PI_ENV_OUT="$out" "${route[@]}" "$kit/scripts/pi-role" "$kit/agents/implementer.md" "$@" 2>/dev/null); }
for flag in -p --print; do
  child "h$flag" "$flag" x
  for v in OCTO_FEATHER_PARENT HERDR_PANE_ID HERDR_TAB_ID HERDR_WORKSPACE_ID; do
    ! grep -q "^$v=" "$t/env.h$flag" || { echo "pi-role test: headless ($flag) child has $(grep "^$v=" "$t/env.h$flag")" >&2; exit 1; }
  done
done
child pane
for kv in "${route[@]}"; do
  grep -qx "$kv" "$t/env.pane" || { echo "pi-role test: pane launch child lacks $kv" >&2; exit 1; }
done
echo "pi-role: ok (repo skill from a lane worktree, home ignored, missing one warned; -p/--print child has no OCTO_FEATHER_PARENT or HERDR_PANE_ID/TAB_ID/WORKSPACE_ID, a pane launch keeps them)"
