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
t="$(mktemp -d)"; trap 'rm -rf "$t" "$t.before"' EXIT
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
# grew: a baseline holds an entry its last commit lacks (the comparison: tests/fixtures/lint/baseline_grew.py).
grew() { ! (cd "$t" && python3 "$kit/tests/fixtures/lint/baseline_grew.py"); }

mkdir -p "$t/pkg" "$t/bin" "$t/.agents/skills/s/scripts"
cat >"$t/pyproject.toml" <<'EOF'
[project]
name = "target"
version = "0"
requires-python = ">=3.12"

[tool.ruff]
line-length = 100

# A table between [tool.ruff] and its sub-tables: init and shrink edit it as split tables.
[tool.basedpyright]
typeCheckingMode = "strict"

[tool.ruff.lint]
select = ["ALL"]
ignore = ["COM812", "CPY001", "D"]

[tool.ruff.format]
quote-style = "double"  # config beside the baseline's exclude, kept as written
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

# Fixed violations leave stale entries naming shrink; shrink deletes only them, never an emptied
# array outside the baseline table.
printf '\n[tool.unrelated]\n"extra" = [\n]\n' >>"$t/pyproject.toml"; g commit -qam unrelated
printf '#!/usr/bin/env python3\nimport sys\n\nN: int = 1\nsys.stdout.write(f"{N}\\n")\n' >"$t/bin/tool"
bad lint 'T201 no longer fires in bin/tool' 'octo-feather-lint shrink'
bad types 'no longer occur' 'octo-feather-lint shrink'
cp "$t/pyproject.toml" "$t.before"
ok shrink "shrink after fixes"
# Only bin/tool's emptied key went; every other byte of pyproject.toml is as it was.
gone="$(diff --unchanged-line-format= --old-line-format='-%L' --new-line-format='+%L' "$t.before" "$t/pyproject.toml" || true)"
[[ "$gone" == $'-"bin/tool" = [\n-    "T201",\n-]' ]] || fail "shrink changed more of pyproject.toml than bin/tool's key: $gone"
! grew || fail "shrink grew a baseline"
! grep -qF '"T201",' "$t/pyproject.toml" || fail "shrink left the stale T201"
grep -qxF '"extra" = [' "$t/pyproject.toml" || fail "shrink deleted [tool.unrelated] extra"
ok lint "after shrink"; ok types "after shrink"

# No tracked Python: no tool runs, so an untracked file is never linted, formatted or typed.
rm -rf "$t"; mkdir "$t"
printf '[tool.ruff.lint]\nselect = ["ALL"]\n\n[tool.basedpyright]\ntypeCheckingMode = "strict"\n' >"$t/pyproject.toml"
g init -q; g add pyproject.toml; g commit -qm base
printf 'import nonexistent\n' >"$t/untracked.py"
ok lint "with only an untracked file"; grep -qF 'lint: ok (0 files' <<<"$out" || fail "lint did not report 0 files"
ok format "with only an untracked file"; grep -qF 'format: ok (0 files' <<<"$out" || fail "format did not report 0 files"
ok types "with only an untracked file"; grep -qF 'analyzed 0 files' <<<"$out" || fail "types did not report 0 files"

# Every baselined file gone: the set is empty, every entry of each baseline stale; shrink empties them.
rm -rf "$t"; mkdir "$t"
printf '[tool.ruff.lint]\nselect = ["ALL"]\n\n[tool.basedpyright]\ntypeCheckingMode = "strict"\n' >"$t/pyproject.toml"
printf 'N: int = "x"\nX = {  "a":1 }\n' >"$t/bad.py"
g init -q; g add -A; g commit -qm base
ok init "init with bad.py"; g add -A; g commit -qm baselines
grep -qF '"./bad.py"' "$t/.basedpyright/baseline.json" || fail "init did not baseline bad.py's type error"
g rm -q bad.py; g commit -qm gone
bad lint 'bad.py is not in the file set' 'octo-feather-lint shrink'
bad format 'bad.py is formatted or gone' 'octo-feather-lint shrink'
bad types 'no longer occur' 'octo-feather-lint shrink'
ok shrink "shrink with every baselined file gone"
printf '{\n    "files": {}\n}' | cmp -s - "$t/.basedpyright/baseline.json" || fail "shrink left $(cat "$t/.basedpyright/baseline.json")"
! grep -qF 'bad.py' "$t/pyproject.toml" || fail "shrink left a bad.py ruff entry"
ok lint "after shrink"; ok format "after shrink"; ok types "after shrink"
echo "lint test: ok"
