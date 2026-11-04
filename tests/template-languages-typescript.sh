#!/usr/bin/env bash
# Integration test for each template's own check-languages (#362, owner rulings #225, #261), one gate item per template
# (#509; setup and check_template: tests/lib/template-languages.sh), here the TypeScript repo, made by
# `just new-repo typescript DEST --no-spec-chat`, offline (its packages copied from the run's one install from the pnpm
# store CI fills, tests/lib/prepared.py): a fresh repo passes `just check-languages`; each of its rules, broken once,
# fails it naming the file and the fix: a tracked unknown file, a Go file (unmapped), a file a tool's own list misses
# (an unattributed bash script, a dot-file .ts outside tsconfig's include), an `env -S` shebang scc cannot read, both
# pnpm pins, and ShellCheck's recipe out of the gate. Its check runs with python, python3, uv and uvx on PATH as stubs
# that record any call: none is called (that template needs no Python). Run by `just check`.
# shellcheck source=tests/lib/template-languages.sh
source "$(dirname "$0")/lib/template-languages.sh"
check_template typescript
check_tiers typescript
[[ ! -e "$t/called" ]] || { out="$(cat "$t/called")"; fail "the TypeScript repo's check called Python or uv"; }
echo "template-languages-typescript: ok (typescript repo green fresh; unknown, Go, uncovered file, env -S shebang, both pnpm pins and a gate recipe out each named; typescript without Python)"
