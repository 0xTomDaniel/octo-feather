#!/usr/bin/env bash
# Integration test for each template's own check-languages (#362, owner rulings #225, #261), in repos made by
# `just new-repo LANG DEST --no-spec-chat`, offline (packages from the uv cache and pnpm store CI fills): a fresh repo
# passes `just check-languages`; each of its six rules, broken once, fails it naming the file and the fix: a tracked
# unknown file, a Go file (unmapped), a file a tool's own list misses (an unattributed bash script; the Python repo:
# an extensionless Python script; the TypeScript repo: a dot-file .ts outside tsconfig's include), an `env -S`
# shebang scc cannot read, both pnpm pins (TypeScript repo), and ShellCheck's recipe out of the gate. The TypeScript repo's check runs with python, python3, uv and uvx on PATH as stubs that record any call:
# none is called (that template needs no Python). Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "template-languages test: $1" >&2; echo "${out:-}" >&2; exit 1; }
g() { git -C "$1" -c user.name=t -c user.email=t@t "${@:2}"; }
# new-repo trusts each created mise.toml: in this test's trust store, never the box's.
export MISE_STATE_DIR="$t/mise-state"
mkdir -p "$t/nopy"
for x in python python3 uv uvx; do printf '#!/bin/sh\necho "$0 $*" >>"%s/called"\nexit 127\n' "$t" >"$t/nopy/$x"; chmod +x "$t/nopy/$x"; done

for lang in python typescript; do
  d="$t/$lang"
  (cd "$t" && GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t \
    just --justfile "$kit/justfile" new-repo "$lang" "$d" --no-spec-chat >/dev/null)
  if [[ "$lang" == python ]]; then
    (cd "$d" && UV_OFFLINE=1 uv sync --locked --quiet) || fail "python: uv sync --locked offline failed (CI's uv step fills the cache)"
    check() { set +e; out="$(cd "$d" && just check-languages 2>&1)"; rc=$?; set -e; }
  else
    (cd "$d" && pnpm install --offline --frozen-lockfile >/dev/null) || fail "typescript: pnpm install offline failed (CI's pnpm fetch fills the store)"
    check() { set +e; out="$(cd "$d" && PATH="$t/nopy:$PATH" just check-languages 2>&1)"; rc=$?; set -e; }
  fi
  check; [[ "$rc" == 0 ]] && grep -qF "languages: ok (" <<<"$out" || fail "$lang: a fresh repo is not green"
  printf 'x\n' >"$d/notes.xyz"; printf 'package main\n' >"$d/tool.go"; printf '#!/usr/bin/env bash\necho hi\n' >"$d/hook"
  printf '#!/usr/bin/env -S node --x\n1\n' >"$d/envs"; chmod +x "$d/hook" "$d/envs"
  want=("notes.xyz: scc does not know this file type; give it a known extension, or mark it \`language-exempt\` in .gitattributes with the reason"
    "Go (tool.go) has no lint or type step: add its tools to the gate and to the justfile's check_languages, or declare it DATA in check-languages"
    "hook: BASH, but shellcheck's own file list misses it; ShellCheck's file list: give a file the \`shell\` attribute in .gitattributes (just shell-files)"
    "envs: scc cannot name the language of its shebang (it drops \`env -S\` forms); start it with #!/usr/bin/env <interpreter> or give it an extension")
  if [[ "$lang" == python ]]; then
    printf '#!/usr/bin/env python3\nprint(1)\n' >"$d/x-py"; chmod +x "$d/x-py"
    want+=("x-py: Python, but ruff's own file list misses it; ruff's own file list: name an extensionless script in pyproject.toml [tool.ruff] extend-include (just ruff-files)"
      "x-py: Python, but basedpyright's own file list misses it; basedpyright's analyzed files: add a path to [tool.basedpyright] include (under .agents/: .agents/pyrightconfig.json) (just pyright-files)")
  else
    printf 'export const x = 1;\n' >"$d/.hidden.ts"
    (cd "$d" && node -e 'const fs = require("fs"); const p = JSON.parse(fs.readFileSync("package.json", "utf8")); p.packageManager = "pnpm@10.7.0"; fs.writeFileSync("package.json", JSON.stringify(p, null, 2) + "\n");')
    want+=(".hidden.ts: TypeScript, but tsc's own file list misses it; tsc's own file list: add a path to tsconfig.json include (a dot path or dotfile by name) (just ts-files)"
      "package.json: packageManager and mise.toml [tools] pnpm both pin pnpm; delete packageManager: mise owns pnpm (owner ruling, issue #261), and pnpm's switch to packageManager would override it and need the network")
  fi
  g "$d" add -A
  check; [[ "$rc" != 0 ]] || fail "$lang: planted files passed"
  for s in "${want[@]}"; do grep -qxF -- "check-languages: $s" <<<"$out" || fail "$lang: output lacks: $s"; done
  g "$d" reset -q --hard; g "$d" clean -qfd -e node_modules -e .venv
  # ShellCheck's recipe out of the gate (GATE_RECIPES in the Python repo, check's dependencies in the TypeScript repo).
  sed -i -e 's/^export GATE_RECIPES := "check-languages check-scripts /export GATE_RECIPES := "check-languages /' \
    -e 's/^check: check-languages check-scripts /check: check-languages /' "$d/justfile"
  g "$d" add -A
  check; [[ "$rc" != 0 ]] || fail "$lang: shellcheck's recipe out of the gate passed"
  s="shellcheck gates BASH, but its recipe check-scripts is not in the gate"
  grep -qxF -- "check-languages: $s" <<<"$out" || fail "$lang: output lacks: $s"
done
[[ ! -e "$t/called" ]] || { out="$(cat "$t/called")"; fail "the TypeScript repo's check called Python or uv"; }
echo "template-languages: ok (python and typescript repos green fresh; unknown, Go, uncovered file, env -S shebang, both pnpm pins (typescript) and a gate recipe out each named; typescript without Python)"
