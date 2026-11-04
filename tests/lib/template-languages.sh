# shellcheck shell=bash
# Sourced by tests/template-languages.sh (the Python repo) and tests/template-languages-typescript.sh (one gate item per
# template, #509), never run itself: in tests/lib/ so the gate's tests/*.sh glob does not collect it. Gives each item
# its own throwaway dir ($t, the trust store under it), the recording Python and uv stubs ($t/nopy), and
# check_template LANG: the repo `just new-repo LANG DEST --no-spec-chat` makes, green fresh, then each rule broken once.
set -euo pipefail
kit="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
# One pnpm store for the kit and its test copies (owner ruling #422; why: tests/check-ts.sh).
npm_config_store_dir="$(cd "$kit" && pnpm store path)"; export npm_config_store_dir
fail() { echo "template-languages test: $1" >&2; echo "${out:-}" >&2; exit 1; }
g() { git -C "$1" -c user.name=t -c user.email=t@t "${@:2}"; }
# new-repo trusts each created mise.toml: in this test's trust store, never the box's.
export MISE_STATE_DIR="$t/mise-state"
mkdir -p "$t/nopy"
for x in python python3 uv uvx; do printf '#!/bin/sh\necho "$0 $*" >>"%s/called"\nexit 127\n' "$t" >"$t/nopy/$x"; chmod +x "$t/nopy/$x"; done

# check_template LANG: the fresh repo passes `just check-languages`; each planted rule break, and ShellCheck's recipe
# out of the gate, fails it naming the file and the fix.
check_template() {
  local lang="$1"
  d="$t/$lang"
  (cd "$t" && GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t \
    just --justfile "$kit/justfile" new-repo "$lang" "$d" --no-spec-chat >/dev/null)
  if [[ "$lang" == python ]]; then
    (cd "$d" && UV_OFFLINE=1 uv sync --locked --quiet) || fail "python: uv sync --locked offline failed (CI's uv step fills the cache)"
    check() { set +e; out="$(cd "$d" && just check-languages 2>&1)"; rc=$?; set -e; }
  else
    # Its packages copied from the run's one offline install of the template (tests/lib/prepared.py).
    p="$(python3 "$kit/tests/lib/prepared.py" typescript "$t")" && cp -a "$p/node_modules" "$d/" \
      || fail "typescript: pnpm install offline failed (CI's pnpm fetch fills the store)"
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
}
