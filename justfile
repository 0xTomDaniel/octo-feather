# octo-feather kit commands. `just check` is the one gate (AGENTS.md).

set shell := ["bash", "-euo", "pipefail", "-c"]

root := justfile_directory()
export PATH := env_var('HOME') + "/.local/bin:" + root + "/scripts:" + root + "/skills/herdr-comms/assets:" + env_var('PATH')

default:
    @just --list

# The gate: script syntax, Pi-only and GitHub-only references, no dashes, skill frontmatter.
check: check-scripts check-refs check-dashes check-skills
    @echo "just check: ok"

# shellcheck when installed, else bash -n.
check-scripts:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{root}}"
    files=(scripts/* skills/herdr-comms/assets/*)
    if command -v shellcheck >/dev/null; then
      shellcheck -S warning "${files[@]}"; echo "scripts: shellcheck ok (${#files[@]} files)"
    else
      for f in "${files[@]}"; do bash -n "$f"; done; echo "scripts: bash -n ok (${#files[@]} files; shellcheck not installed)"
    fi
    for f in "${files[@]}"; do [[ -x "$f" ]] || { echo "not executable: $f" >&2; exit 1; }; done

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
    if grep -nHiE 'claude|codex' "${files[@]}"; then
      echo "check-refs: Claude/Codex references above; Pi is the only runtime (docs/adr/0001)" >&2; bad=1; fi
    if grep -nHE 'octo-lite-|\.octo-lite|octo-lite:' "${files[@]}"; then
      echo "check-refs: octo-lite product names above; rename to octo-feather (attribution stays in NOTICE)" >&2; bad=1; fi
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
    for r in meta-operator orchestrator implementer integrator code-reviewer; do
      [[ -f "agents/$r.md" ]] || { echo "check-skills: missing role contract agents/$r.md" >&2; exit 1; }
    done
    echo "skills: ok ($n skills, 5 roles)"

# Verify the runtime tools on this box (octo-lite's install --check equivalent).
install-check:
    #!/usr/bin/env bash
    set -uo pipefail
    bad=0
    for t in herdr pi gh jq git just; do
      if p="$(command -v "$t")"; then printf '%-6s ok  %s\n' "$t" "$p"
      else printf '%-6s MISSING\n' "$t"; bad=1; fi
    done
    gh auth status >/dev/null 2>&1 && echo "gh     authenticated" || { echo "gh     NOT authenticated (gh auth login)"; bad=1; }
    exit "$bad"

# Start the director (meta-operator) in Herdr workspace `director` (docs/adr/0011).
start cwd=invocation_directory():
    octo-feather-start --director --cwd "{{cwd}}"

# Start one lane owner for GitHub issue N in workspace gh<N>, tab `lane`.
lane issue cwd=invocation_directory():
    octo-feather-start --issue "{{issue}}" --cwd "{{cwd}}"

# Print this Herdr session's octo-feather state directory.
state:
    @octo-feather-state
