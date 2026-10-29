#!/usr/bin/env bash
# Integration test for each template's own check-languages (#362, owner rulings #225, #261), in repos made by
# `just new-repo LANG DEST --no-spec-chat`, offline (packages from the uv cache and pnpm store CI fills): a fresh repo
# passes `just check-languages`; a tracked unknown file, a Go file and an unattributed bash script fail it, each
# named. The TypeScript repo's check runs with python, python3, uv and uvx on PATH as stubs that record any call:
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
  chmod +x "$d/hook"; g "$d" add -A
  check; [[ "$rc" != 0 ]] || fail "$lang: planted files passed"
  for s in "notes.xyz: scc does not know this file type" "Go (tool.go) has no lint or type step" \
    "hook: BASH, but shellcheck's own file list misses it; give it the \`shell\` attribute in .gitattributes"; do
    grep -qF -- "$s" <<<"$out" || fail "$lang: output lacks: $s"
  done
done
[[ ! -e "$t/called" ]] || { out="$(cat "$t/called")"; fail "the TypeScript repo's check called Python or uv"; }
echo "template-languages: ok (python and typescript repos green fresh; unknown, Go and unattributed shell named; typescript without Python)"
