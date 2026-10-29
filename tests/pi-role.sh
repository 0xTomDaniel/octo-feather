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
# #261: agent shells are non-interactive, so in a repo with its own mise.toml pi-role places mise's shims dir (mise's
# own answer) just before the caller PATH's first system dir: the caller's earlier dirs (here $t/bin, the stub pi)
# still win. In a repo without one (a repo the kit did not create, here gh1) and with no mise on PATH, PATH is left
# as it was. The PATHs are fixed here, so an empty entry in the caller's PATH cannot change the comparison.
shims="$(mise doctor --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["dirs"]["shims"])')"
mkdir -p "$t/mbin"; ln -s "$(command -v mise)" "$t/mbin/mise"
grep -qxF "PATH=$t/bin:$PATH" "$t/env.pane" || { echo "pi-role test: child PATH in a repo without mise.toml changed: $(grep ^PATH= "$t/env.pane")" >&2; exit 1; }
git init -q "$t/made"; printf '[tools]\n' >"$t/made/mise.toml"
(cd "$t/made" && env PATH="$t/bin:$t/mbin:/usr/local/bin:/usr/bin:/bin" PI_ENV_OUT="$t/env.made" "$kit/scripts/pi-role" "$kit/agents/implementer.md" 2>/dev/null)
grep -qxF "PATH=$t/bin:$t/mbin:$shims:/usr/local/bin:/usr/bin:/bin" "$t/env.made" || { echo "pi-role test: child PATH in a mise.toml repo lacks mise's shims $shims before the system dirs, after the caller's: $(grep ^PATH= "$t/env.made")" >&2; exit 1; }
(cd "$t/made" && env PATH="$t/bin:/usr/bin:/bin" PI_ENV_OUT="$t/env.nomise" "$kit/scripts/pi-role" "$kit/agents/implementer.md" 2>/dev/null)
grep -qx "PATH=$t/bin:/usr/bin:/bin" "$t/env.nomise" || { echo "pi-role test: without mise, child PATH changed: $(grep ^PATH= "$t/env.nomise")" >&2; exit 1; }
# #175 (roles#launch-codemode, roles#acceptance-codemode-every-role).
# #262 (roles#launch-web): a web role's tab args add the kit's two web servers and drop --no-mcp.
ro=read,grep,find,ls,bash,codemode; rw=read,grep,find,ls,bash,edit,write,codemode
web=',mcp__parallel__*,mcp__exa__*;web'
for rt in "director:$ro$web" "code-reviewer:$ro$web" "qc-judge:$ro;--no-mcp" "supervisor:$rw;--no-mcp" "implementer:$rw$web" "corrector:$rw$web"; do
  role="${rt%%:*}"; want="${rt#*:}"
  got="$(cd "$t/gh1" && "$kit/scripts/pi-role" --json "$kit/agents/$role.md" 2>/dev/null | python3 -c 'import json,sys; a=json.load(sys.stdin)["args"]; print((a[a.index("--tools")+1] if "--tools" in a else "none") + ";" + ("--no-mcp" if "--no-mcp" in a else "web" if a[a.index("--octo-feather-web-servers")+1].endswith("/web-mcp.json") else "?"))')"
  [[ "$got" == "$want" ]] || { echo "pi-role test: $role --tools is $got, want $want" >&2; exit 1; }
done

# #175 (roles#fm-tools).
# A fixture kit: the real scripts and skills, a director whose tools list codemode.
mkdir -p "$t/kit/scripts" "$t/kit/.agents"
cp "$kit/scripts/check-roles" "$kit/scripts/pi-role" "$t/kit/scripts/"; cp -r "$kit/agents" "$t/kit/"; cp "$kit/web-mcp.json" "$t/kit/"
ln -s "$kit/.agents/skills" "$t/kit/.agents/skills"
sed -i 's/^tools: .*/tools: read, grep, find, ls, bash, codemode/' "$t/kit/agents/director.md"
if "$t/kit/scripts/check-roles" >/dev/null 2>"$t/cr"; then echo "pi-role test: check-roles passed a role listing codemode" >&2; exit 1; fi
grep -q 'agents/director.md: .*`codemode`.*pi-role adds it' "$t/cr" || { echo "pi-role test: check-roles did not name the file and codemode: $(cat "$t/cr")" >&2; exit 1; }
echo "pi-role: ok (repo skill from a lane worktree, home ignored, missing one warned; -p/--print child has no OCTO_FEATHER_PARENT or HERDR_PANE_ID/TAB_ID/WORKSPACE_ID, a pane launch keeps them; mise's shims before the system dirs in a mise.toml repo, none elsewhere or without mise (#261); #175 (roles#launch-codemode, roles#fm-tools))"
