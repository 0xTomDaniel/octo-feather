# octo-feather kit commands. `just check` is the one gate (AGENTS.md).

set shell := ["bash", "-euo", "pipefail", "-c"]

root := justfile_directory()
export PATH := env_var('HOME') + "/.local/bin:" + root + "/scripts:" + root + "/skills/herdr-comms/assets:" + env_var('PATH')

default:
    @just --list

# The gate: script syntax, Pi-only and GitHub-only references, no dashes, skill frontmatter.
check: check-scripts check-refs check-dashes check-skills check-roles
    @echo "just check: ok"

# shellcheck when installed, else bash -n; python scripts byte-compile.
check-scripts:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    files=(); py=()
    for f in scripts/* skills/herdr-comms/assets/*; do
      if head -1 "$f" | grep -q python; then py+=("$f"); else files+=("$f"); fi
    done
    for f in "${py[@]}"; do python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])' "$f"; done
    echo "python: ok (${#py[@]} files)"
    if command -v shellcheck >/dev/null; then
      shellcheck -S warning "${files[@]}"; echo "scripts: shellcheck ok (${#files[@]} files)"
    else
      for f in "${files[@]}"; do bash -n "$f"; done; echo "scripts: bash -n ok (${#files[@]} files; shellcheck not installed)"
    fi
    for f in "${files[@]}" "${py[@]}"; do [[ -x "$f" ]] || { echo "not executable: $f" >&2; exit 1; }; done

# No CLAUDE.md, no .claude/.codex projections, no Linear, no octo-lite product names.
# Exempt: docs/ (ADRs name what was rejected), AGENTS.md, README.md, NOTICE,
# LICENSE, this justfile, and spec/ (octo-lite's spec, kept as format reference).
check-refs:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    bad=0
    if git ls-files | grep -E '(^|/)(CLAUDE\.md|\.claude|\.codex)(/|$)'; then
      echo "check-refs: Claude/Codex projection files above are not allowed (docs/adr/0001)" >&2; bad=1; fi
    mapfile -t files < <(git ls-files | grep -vE '^(docs/|spec/|AGENTS\.md$|README\.md$|NOTICE$|LICENSE$|justfile$)')
    if grep -nHiE '\blinear\b' "${files[@]}"; then
      echo "check-refs: Linear references above; GitHub Issues is the tracker (docs/adr/0004)" >&2; bad=1; fi
    # Model ids (anthropic/claude-*) are a provider choice, not a runtime.
    if grep -nHiE 'claude|codex' "${files[@]}" | grep -vE 'anthropic/claude-[a-z0-9-]+'; then
      echo "check-refs: Claude/Codex references above; Pi is the only runtime (docs/adr/0001)" >&2; bad=1; fi
    if grep -nHE 'octo-lite-|\.octo-lite|octo-lite:' "${files[@]}"; then
      echo "check-refs: octo-lite product names above; rename to octo-feather (attribution stays in NOTICE)" >&2; bad=1; fi
    [[ "$bad" == 0 ]] && echo "refs: ok (${#files[@]} files)"
    exit "$bad"

# No em or en dashes in kit text. Exempt upstream copies: spec/, LICENSE and
# vendored skills (agents/skills/, .skillfile/patches/), which keep upstream wording.
check-dashes:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    mapfile -t files < <(git ls-files | grep -vE '^(spec/|agents/skills/|\.skillfile/|LICENSE$)')
    if grep -nHF -e "$(printf '\xe2\x80\x93')" -e "$(printf '\xe2\x80\x94')" "${files[@]}"; then
      echo "check-dashes: replace the em/en dashes above with a colon, comma or parentheses" >&2; exit 1; fi
    echo "dashes: ok (${#files[@]} files)"

# Every skill has name and description frontmatter; every role file exists.
check-skills:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    n=0
    for f in skills/*/SKILL.md agents/skills/*/SKILL.md; do
      head -5 "$f" | grep -q '^name: ' && head -8 "$f" | grep -q '^description: ' || { echo "check-skills: $f lacks name/description frontmatter" >&2; exit 1; }
      n=$((n + 1))
    done
    for r in meta-operator supervisor implementer integrator code-reviewer; do
      [[ -f "agents/$r.md" ]] || { echo "check-skills: missing role contract agents/$r.md" >&2; exit 1; }
    done
    echo "skills: ok ($n skills, 5 roles)"

# Role files: pi-subagents frontmatter, skills resolve, allowed models (docs/adr/0013).
check-roles:
    @python3 "{{root}}/scripts/check-roles"

# Install the pinned project-local pi-subagents (.pi/settings.json) into .pi/npm.
install:
    cd "{{root}}" && pi install -l "$(jq -r '.packages[] | select(startswith("npm:pi-subagents@"))' .pi/settings.json)"

# Verify the runtime tools on this box (octo-lite's install --check equivalent).
install-check:
    #!/usr/bin/env bash
    set -uo pipefail
    bad=0
    for t in herdr pi gh jq git just python3; do
      if p="$(command -v "$t")"; then printf '%-6s ok  %s\n' "$t" "$p"
      else printf '%-6s MISSING\n' "$t"; bad=1; fi
    done
    gh auth status >/dev/null 2>&1 && echo "gh     authenticated" || { echo "gh     NOT authenticated (gh auth login)"; bad=1; }
    pin="$(jq -r '.packages[] | select(startswith("npm:pi-subagents@"))' "{{root}}/.pi/settings.json")"
    v="$(jq -r .version "{{root}}/.pi/npm/node_modules/pi-subagents/package.json" 2>/dev/null)"
    [[ "npm:pi-subagents@$v" == "$pin" ]] && echo "pi-subagents ok  $v (project-local)" || { echo "pi-subagents MISSING or not $pin (just install)"; bad=1; }
    exit "$bad"

# Start the director (meta-operator) in Herdr workspace `director` (docs/adr/0011).
start cwd=invocation_directory():
    octo-feather-start --director --cwd "{{cwd}}"

# Start one supervisor for GitHub issue N in workspace gh<N>, tab `supervisor`.
supervise issue cwd=invocation_directory():
    octo-feather-start --issue "{{issue}}" --cwd "{{cwd}}"

# Print this Herdr session's octo-feather state directory.
state:
    @octo-feather-state
