#!/usr/bin/env bash
# Integration test for octo-feather-lint (#244), run as a command in a throwaway target repo (any repo,
# not the kit): `init` takes the baselines; then a new ruff code in a file fails `lint` naming
# file:line and rule, a new basedpyright error fails `types` naming file:line and rule (also in an
# extensionless script under a dot directory, which basedpyright skips unless the mirror works), a
# new unformatted file fails `format`; a fixed violation leaves a stale entry that fails naming
# `octo-feather-lint shrink`, and shrink deletes it; shrink never adds an entry, even with a new
# violation present. ruff and basedpyright come from the kit's uv environment, offline. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
lint() { (cd "$t" && uv run --project "$kit" --locked --offline --no-sync "$kit/scripts/octo-feather-lint" "$@"); }
fail() { echo "lint test: $1" >&2; [[ -z "${out:-}" ]] || echo "$out" >&2; exit 1; }
# run CMD: octo-feather-lint CMD into $out and $rc.
run() { set +e; out="$(lint "$1" 2>&1)"; rc=$?; set -e; }
ok() { run "$1"; [[ "$rc" == 0 ]] || fail "$1 is not green: $2"; }
# bad CMD TEXT...: CMD exits 1 and prints each TEXT.
bad() {
  local cmd="$1"; shift; run "$cmd"
  [[ "$rc" == 1 ]] || fail "$cmd exited $rc, want 1"
  for s in "$@"; do grep -qF -- "$s" <<<"$out" || fail "$cmd did not print: $s"; done
}
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
# grew: either baseline holds an entry its last commit lacks (pyproject.toml: a line added;
# basedpyright's file: more errors than committed, its JSON layout reflows when it shrinks).
grew() {
  [[ "$(g diff --numstat -- pyproject.toml | cut -f1)" =~ ^0?$ ]] || return 0
  local b=.basedpyright/baseline.json
  (( $(grep -c '"code"' "$t/$b") <= $(g show "HEAD:$b" | grep -c '"code"') )) && return 1 || return 0
}

mkdir -p "$t/pkg" "$t/bin" "$t/.agents/skills/s/scripts"
cat >"$t/pyproject.toml" <<'EOF'
[project]
name = "target"
version = "0"
requires-python = ">=3.12"

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["ALL"]
ignore = ["COM812", "CPY001", "D"]

[tool.basedpyright]
typeCheckingMode = "strict"
EOF
printf 'def double(n: int) -> int:\n    return n * 2\n' >"$t/pkg/m.py"
# bin/tool: one ruff code (T201) and one type error, both baselined by init.
printf '#!/usr/bin/env python3\nN: int = "x"\nprint(N)\n' >"$t/bin/tool"
printf '#!/usr/bin/env -S uv run --script\nVALUE = 1\n' >"$t/.agents/skills/s/scripts/run"
printf '#!/bin/sh\necho not python\n' >"$t/bin/shell"
chmod +x "$t/bin/tool" "$t/bin/shell" "$t/.agents/skills/s/scripts/run"
g init -q; g add -A; g commit -qm base

run files
[[ "$out" == $'.agents/skills/s/scripts/run\nbin/tool\npkg/m.py' ]] || fail "file set is not the 3 Python files"
ok init "init"
ok types "after init"
grep -qF 'basedpyright analyzed 3 files' <<<"$out" || fail "types did not analyze the 3 files"
grep -qF '"bin/tool" = [' "$t/pyproject.toml" && grep -qF '"T201",' "$t/pyproject.toml" || fail "init wrote no ruff baseline for bin/tool"
bad init "a baseline exists"
g add -A; g commit -qm baselines

# A new ruff code in a clean file, and one new in a baselined file.
printf 'import os\n' >>"$t/pkg/m.py"
bad lint 'pkg/m.py:3: F401' 'fix:' 'never add F401 for pkg/m.py'
g checkout -q -- pkg/m.py
printf 'assert N\n' >>"$t/bin/tool"
bad lint 'bin/tool:4: S101' 'never add S101 for bin/tool'
g checkout -q -- bin/tool
# A new basedpyright error, in a .py file and in the dot-directory script.
printf 'def name() -> str:\n    return double(1)\n' >>"$t/pkg/m.py"
bad types 'pkg/m.py:4: reportReturnType' 'fix:'
g checkout -q -- pkg/m.py
printf 'COUNT: int = "two"\n' >>"$t/.agents/skills/s/scripts/run"
bad types '.agents/skills/s/scripts/run:3: reportAssignmentType'
# Shrink refuses to grow: with that new error present it adds nothing to either baseline.
bad shrink
! grew || fail "shrink grew a baseline"
g checkout -q -- .agents/skills/s/scripts/run
# A new unformatted file.
printf 'X = {  "a":1 }\n' >"$t/pkg/n.py"; g add pkg/n.py
bad format 'pkg/n.py:1: unformatted' 'ruff format --diff pkg/n.py'
g rm -qf pkg/n.py

# Fixed violations leave stale entries naming shrink; shrink deletes only them.
printf '#!/usr/bin/env python3\nimport sys\n\nN: int = 1\nsys.stdout.write(f"{N}\\n")\n' >"$t/bin/tool"
bad lint 'T201 no longer fires in bin/tool' 'octo-feather-lint shrink'
bad types 'no longer occur' 'octo-feather-lint shrink'
ok shrink "shrink after fixes"
! grew || fail "shrink grew a baseline"
! grep -qF '"T201",' "$t/pyproject.toml" || fail "shrink left the stale T201"
ok lint "after shrink"; ok types "after shrink"
echo "lint test: ok"
