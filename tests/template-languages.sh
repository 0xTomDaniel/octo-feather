#!/usr/bin/env bash
# Integration test for each template's own check-languages (#362, owner rulings #225, #261), one gate item per template
# (#509; setup and check_template: tests/lib/template-languages.sh), here the Python repo, made by
# `just new-repo python DEST --no-spec-chat`, offline (packages from the uv cache CI fills): a fresh repo passes
# `just check-languages`; each of its rules, broken once, fails it naming the file and the fix: a tracked unknown file,
# a Go file (unmapped), a file a tool's own list misses (an unattributed bash script, an extensionless Python script),
# an `env -S` shebang scc cannot read, and ShellCheck's recipe out of the gate. Run by `just check`.
# shellcheck source=tests/lib/template-languages.sh
source "$(dirname "$0")/lib/template-languages.sh"
check_template python
echo "template-languages: ok (python repo green fresh; unknown, Go, uncovered file, env -S shebang and a gate recipe out each named)"
