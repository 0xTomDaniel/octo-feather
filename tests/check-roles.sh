#!/usr/bin/env bash
# Integration test for scripts/check-roles and pi-role's refusal of a bad role file, each fault in its own run: a role
# listing codemode (#175, roles#fm-tools), a role file not in ROLES (#829), an extension that is no file name in
# extensions/ (roles#fm-extensions), a key pi-role does not honour (roles#acceptance-unknown-key). Moved out of
# tests/pi-role.sh (#1323: each item under the per-test CPU budget). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
git init -q "$t/gh1"   # the target pi-role launches from, as in tests/pi-role.sh
# #175 (roles#fm-tools).
# A fixture kit: the real scripts and skills, a director whose tools list codemode.
mkdir -p "$t/kit/scripts" "$t/kit/.agents"
cp "$kit/scripts/check-roles" "$kit/scripts/pi-role" "$t/kit/scripts/"; cp -r "$kit/agents" "$t/kit/"; cp "$kit/web-mcp.json" "$t/kit/"; cp -r "$kit/extensions" "$t/kit/"
ln -s "$kit/.agents/skills" "$t/kit/.agents/skills"
sed -i 's/^tools: .*/tools: read, grep, find, ls, bash, codemode/' "$t/kit/agents/director.md"
if "$t/kit/scripts/check-roles" >/dev/null 2>"$t/cr"; then echo "check-roles test: check-roles passed a role listing codemode" >&2; exit 1; fi
grep -q 'agents/director.md: .*`codemode`.*pi-role adds it' "$t/cr" || { echo "check-roles test: check-roles did not name the file and codemode: $(cat "$t/cr")" >&2; exit 1; }
# #829: check-roles counts general-worker among its roles, and still refuses a role file not in ROLES.
cp "$kit/agents/director.md" "$t/kit/agents/director.md"
out="$("$t/kit/scripts/check-roles" 2>"$t/cr")" || { echo "check-roles test: check-roles refused the kit's roles: $(cat "$t/cr")" >&2; exit 1; }
[[ "$out" == "roles: ok (8 role files"* ]] || { echo "check-roles test: check-roles did not count 8 roles: $out" >&2; exit 1; }
sed 's/^name: .*/name: stray/' "$kit/agents/general-worker.md" > "$t/kit/agents/stray.md"
if "$t/kit/scripts/check-roles" >/dev/null 2>"$t/cr"; then echo "check-roles test: check-roles passed a role file not in ROLES" >&2; exit 1; fi
grep -qF "agents/: role files ['stray'] are not in ROLES" "$t/cr" || { echo "check-roles test: check-roles did not name the stray role file: $(cat "$t/cr")" >&2; exit 1; }
rm "$t/kit/agents/stray.md"
# check-roles refuses an extension that is no file name in extensions/ (missing, or a path), naming file and name; a
# key pi-role does not honour stays refused (roles#acceptance-unknown-key); pi-role refuses the launch too.
for bad in missing.ts ../extensions/results-on-wake.ts; do
  sed "s|^extensions: .*|extensions: $bad|" "$kit/agents/supervisor.md" > "$t/kit/agents/supervisor.md"
  if "$t/kit/scripts/check-roles" >/dev/null 2>"$t/cr"; then echo "check-roles test: check-roles passed extensions: $bad" >&2; exit 1; fi
  grep -qF "agents/supervisor.md: extension \`$bad\` is no file name in extensions/" "$t/cr" || { echo "check-roles test: check-roles did not name supervisor.md and $bad: $(cat "$t/cr")" >&2; exit 1; }
  if (cd "$t/gh1" && "$t/kit/scripts/pi-role" --json "$t/kit/agents/supervisor.md" >/dev/null 2>"$t/pr"); then echo "check-roles test: pi-role launched with extensions: $bad" >&2; exit 1; fi
  grep -qF "extension '$bad' is no file in" "$t/pr" || { echo "check-roles test: pi-role did not name $bad: $(cat "$t/pr")" >&2; exit 1; }
done
sed 's/^extensions: .*/extensions: results-on-wake.ts\nbogus: x/' "$kit/agents/supervisor.md" > "$t/kit/agents/supervisor.md"
if "$t/kit/scripts/check-roles" >/dev/null 2>"$t/cr"; then echo "check-roles test: check-roles passed an unknown key" >&2; exit 1; fi
grep -qF 'agents/supervisor.md: field `bogus` is not one pi-role honours' "$t/cr" || { echo "check-roles test: check-roles did not name bogus: $(cat "$t/cr")" >&2; exit 1; }
cp "$kit/agents/supervisor.md" "$t/kit/agents/supervisor.md"
echo "check-roles: ok (#175 roles#fm-tools: a role listing codemode refused; #829 check-roles counts general-worker and refuses a stray role file; roles#fm-extensions: a missing or path extension refused by check-roles and pi-role; an unknown key still refused)"
