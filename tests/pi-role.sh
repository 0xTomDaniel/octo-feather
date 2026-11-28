#!/usr/bin/env bash
# Integration test for scripts/pi-role's externalSkills lookup: the target repo's
# .agents/skills (main checkout, seen from a lane worktree), never home. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
export XDG_STATE_HOME="$t/state"; "$kit/scripts/pi-role" --set-identity t t@t >/dev/null   # the commit identity a role launch needs (#665)
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
# as it was. The PATHs are fixed here, so an empty entry in the caller's PATH cannot change the comparison. In each,
# the stash guard's dir ($g) where pi-role places it (pi-role --help, Stash guard).
shims="$(mise doctor --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["dirs"]["shims"])')"; g="$kit/scripts/stash-guard"
mkdir -p "$t/mbin"; ln -s "$(command -v mise)" "$t/mbin/mise"
grep -qF ":$g:" "$t/env.pane" || { echo "pi-role test: child PATH in a repo without mise.toml lacks the stash guard $g: $(grep ^PATH= "$t/env.pane")" >&2; exit 1; }
# A caller PATH that already holds $g (a gate under an agent's launch PATH: CI's) has it moved, not added (#1322).
bare=":$PATH:"; bare="${bare//:$g:/:}"; bare="${bare#:}"; bare="${bare%:}"
grep -qxF "PATH=$t/bin:$bare" <(sed "s|:$g:|:|" "$t/env.pane") || { echo "pi-role test: child PATH in a repo without mise.toml changed: $(grep ^PATH= "$t/env.pane")" >&2; exit 1; }
git init -q "$t/made"; printf '[tools]\n' >"$t/made/mise.toml"
(cd "$t/made" && env PATH="$t/bin:$t/mbin:/usr/local/bin:/usr/bin:/bin" PI_ENV_OUT="$t/env.made" "$kit/scripts/pi-role" "$kit/agents/implementer.md" 2>/dev/null)
grep -qxF "PATH=$t/bin:$t/mbin:$g:$shims:/usr/local/bin:/usr/bin:/bin" "$t/env.made" || { echo "pi-role test: child PATH in a mise.toml repo lacks mise's shims $shims before the system dirs, after the caller's: $(grep ^PATH= "$t/env.made")" >&2; exit 1; }
(cd "$t/made" && env PATH="$t/bin:/usr/bin:/bin" PI_ENV_OUT="$t/env.nomise" "$kit/scripts/pi-role" "$kit/agents/implementer.md" 2>/dev/null)
grep -qxF "PATH=$t/bin:$g:/usr/bin:/bin" "$t/env.nomise" || { echo "pi-role test: without mise, child PATH changed: $(grep ^PATH= "$t/env.nomise")" >&2; exit 1; }
# #175 (roles#launch-codemode, roles#acceptance-codemode-every-role).
# #262 (roles#launch-web): a web role's tab args add the kit's two web servers and drop --no-mcp.
ro=read,grep,find,ls,bash,codemode; rw=read,grep,find,ls,bash,edit,write,codemode
web=',mcp__parallel__*,mcp__exa__*;web'
# roles#fm-extensions: a role's own extensions on top of every role's; only director and supervisor load results-on-wake.ts.
every="resume-on-error.ts spend-ledger.ts skills-loaded.ts"
# One launch per role, read by one python3 for both facts (the CPU budget, #1323): its tools;mcp and its extensions.
roles=(director supervisor implementer code-reviewer corrector general-worker reflector shaper qc-judge)
for role in "${roles[@]}"; do (cd "$t/gh1" && "$kit/scripts/pi-role" --json "$kit/agents/$role.md" 2>/dev/null >"$t/json.$role"); done
python3 - "$t" "${roles[@]}" >"$t/launch" <<'PY'
import json, os, sys
for role in sys.argv[2:]:
    a = json.load(open(f"{sys.argv[1]}/json.{role}"))["args"]
    tools = (a[a.index("--tools") + 1] if "--tools" in a else "none") + ";" + ("--no-mcp" if "--no-mcp" in a else "web" if a[a.index("--octo-feather-web-servers") + 1].endswith("/web-mcp.json") else "?")
    ext = " ".join(sorted(os.path.basename(a[i + 1]) for i, x in enumerate(a) if x == "--extension" and os.path.basename(a[i + 1]) != "web-servers.ts"))
    print(f"{role}|{tools}|{ext}")
PY
for rt in "director:$ro$web" "code-reviewer:$ro$web" "qc-judge:$ro;--no-mcp" "supervisor:$rw;--no-mcp" "implementer:$rw$web" "general-worker:$rw$web" "corrector:$rw$web" "shaper:read,grep,find,ls,bash,edit,write,codemode$web"; do
  role="${rt%%:*}"; want="${rt#*:}"
  got="$(grep "^$role|" "$t/launch" | cut -d'|' -f2)"
  [[ "$got" == "$want" ]] || { echo "pi-role test: $role --tools is $got, want $want" >&2; exit 1; }
done
for role in "${roles[@]}"; do
  got="$(grep "^$role|" "$t/launch" | cut -d'|' -f3)"
  case "$role" in director|supervisor) want="$every results-on-wake.ts" ;; *) want="$every" ;; esac
  want="$(tr ' ' '\n' <<<"$want" | sort | tr '\n' ' ' | sed 's/ $//')"
  [[ "$got" == "$want" ]] || { echo "pi-role test: $role extensions are [$got], want [$want]" >&2; exit 1; }
done

echo "pi-role: ok (repo skill from a lane worktree, home ignored, missing one warned; -p/--print child has no OCTO_FEATHER_PARENT or HERDR_PANE_ID/TAB_ID/WORKSPACE_ID, a pane launch keeps them; mise's shims before the system dirs in a mise.toml repo, none elsewhere or without mise (#261); #175 (roles#launch-codemode, roles#fm-tools); #829 general-worker launch; roles#fm-extensions: results-on-wake.ts for director and supervisor only, every role's extensions unchanged; check-roles and the bad role files: tests/check-roles.sh)"
