#!/usr/bin/env bash
# Integration test for check-languages (owner rulings #225, #261): in a throwaway git copy of the kit's tracked
# files, `just check-languages` passes clean; planted files fail it, each named with its fix: an Unknown type, an
# unmapped language (Go), shell outside ShellCheck's list, Python outside ruff's, TypeScript outside tsc's, a shebang
# scc cannot read (env -S), two pnpm pins, a gate tool's recipe out of GATE_RECIPES. An extensionless file with no
# shebang passes by design (no language found). Tools: the kit's mise pins, uv environment and node_modules.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
export UV_PROJECT_ENVIRONMENT="$kit/.venv"
# A link, which .gitignore's node_modules/ (a directory pattern) does not match: excluded by name.
ln -s "$kit/node_modules" "$t/node_modules"; echo /node_modules >>"$t/.git/info/exclude"
fail() { echo "languages test: $1" >&2; echo "$out" >&2; exit 1; }
run() { set +e; out="$(cd "$t" && just check-languages 2>&1)"; rc=$?; set -e; }
has() { for s in "$@"; do grep -qF -- "$s" <<<"$out" || fail "output lacks: $s"; done; }
plant() { mkdir -p "$(dirname "$t/$1")"; printf '%s\n' "$2" >"$t/$1"; chmod +x "$t/$1"; }

run; [[ "$rc" == 0 ]] || fail "the clean copy is not green"; has "languages: ok ("

plant notes.xyz 'data'
plant tool.go 'package main'
plant scripts/x-shell $'#!/usr/bin/env bash\necho ok'
plant scripts/x-py $'#!/usr/bin/env python3\nprint(1)'
plant scripts/x-envs $'#!/usr/bin/env -S uv run --script\nprint(1)'
plant .agents/skills/herdr-comms/assets/x.ts 'export const x = 1;'
plant x-data 'just data, no shebang'
python3 -c 'import json, sys; p = sys.argv[1]; d = json.load(open(p)); d["packageManager"] = "pnpm@10.7.0"; open(p, "w").write(json.dumps(d, indent=2) + "\n")' "$t/package.json"
g add -A
run; [[ "$rc" != 0 ]] || fail "planted files passed"
has "notes.xyz: scc does not know this file type" \
  "Go (tool.go) has no lint or type step" \
  "scripts/x-shell: BASH, but shellcheck's own file list misses it; ShellCheck's file list: give a file the \`shell\` attribute in .gitattributes (just shell-files)" \
  "scripts/x-py: Python, but ruff's own file list misses it; ruff's own file list, which basedpyright gets whole: name an extensionless script in pyproject.toml extend-include (just python-files)" \
  "scripts/x-envs: scc cannot name the language of its shebang" \
  ".agents/skills/herdr-comms/assets/x.ts: TypeScript, but tsc's own file list misses it" \
  "package.json: packageManager and mise.toml [tools] pnpm both pin pnpm; delete packageManager"
! grep -qF "x-data" <<<"$out" || fail "an extensionless file with no shebang was named"
g reset -q --hard; g clean -qfd

sed -i 's/^export GATE_RECIPES := "check-languages check-scripts /export GATE_RECIPES := "check-languages /' "$t/justfile"
g add -A
run; [[ "$rc" != 0 ]] || fail "GATE_RECIPES without check-scripts passed"
has "shellcheck gates BASH, but its recipe check-scripts is not in the gate"
echo "languages test: ok (clean green; Unknown, Go, uncovered shell, Python, TypeScript, env -S shebang, two pnpm pins and a missing gate recipe each named; shebang-less data passes)"
