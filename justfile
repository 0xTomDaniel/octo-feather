# octo-feather kit commands. `just check` is the one gate (AGENTS.md).

set shell := ["bash", "-euo", "pipefail", "-c"]
# Recipe arguments reach the shell as "$@"/"$1", never as pasted text (#61).
set positional-arguments

# Exported so recipes use "$root" as data, never pasted text (#61).
export root := justfile_directory()
# mise's own dirs, as mise reports them, pinned for every recipe and test, so a test that points HOME elsewhere
# leaves nothing of mise's there and still finds its installs. Asked only when unset (a nested run inherits them):
# asking mise with HOME redirected is itself what wrote its cache under that HOME (#261 gate run 983e89dc).
export MISE_DATA_DIR := if env_var_or_default('MISE_DATA_DIR', '') != '' { env_var('MISE_DATA_DIR') } else { `command -v mise >/dev/null && mise doctor --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["dirs"]["data"])' || true` }
export MISE_CACHE_DIR := if env_var_or_default('MISE_CACHE_DIR', '') != '' { env_var('MISE_CACHE_DIR') } else { `command -v mise >/dev/null && mise doctor --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["dirs"]["cache"])' || true` }
export MISE_STATE_DIR := if env_var_or_default('MISE_STATE_DIR', '') != '' { env_var('MISE_STATE_DIR') } else { `command -v mise >/dev/null && mise doctor --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["dirs"]["state"])' || true` }
export MISE_CONFIG_DIR := if env_var_or_default('MISE_CONFIG_DIR', '') != '' { env_var('MISE_CONFIG_DIR') } else { `command -v mise >/dev/null && mise doctor --json | python3 -c 'import json, sys; print(json.load(sys.stdin)["dirs"]["config"])' || true` }
# Offline: a tool missing from mise's installs fails, never downloads (the gate calls no network service, quality
# #boundary-gate); `mise install --locked` fills them, outside the gate.
export MISE_OFFLINE := "1"
# The kit's tools (mise.toml at mise.lock versions) on PATH for every recipe, from any caller (a shell, a git hook,
# CI, an agent pane): mise's own answer for this repo's config (`mise bin-paths`, the config its shims read for
# panes, scripts/pi-role), placed just before the caller PATH's first system dir (/usr/local/sbin /usr/local/bin
# /usr/sbin /usr/bin /sbin /bin; at the end when it has none, pi-role's with_mise rule): mise replaces only what
# would resolve from the system, and every dir the caller put earlier (a test's stub, a user's tools) still wins.
# Only when just is invoked inside this repo: `just -f KIT/justfile ...` from a repo the kit did not create keeps
# that repo's PATH (no mise there). A tool not installed is named on stderr with the fix. macOS: GNU coreutils and
# util-linux (realpath -m, readlink -f, timeout, setsid, uuidgen), Homebrew's bash 5 and python3, also before the
# system dirs, after mise's. The running just's own dir comes last, so recipes and tests still find a just.
# $HOME/.local/bin comes after the whole caller PATH, a fallback only: the Pi and Herdr installers (and mise's) put
# their tools there, and a caller that is not a login shell (a git hook, CI, cron) may lack it on PATH; the justfile
# put it first since 2ad258f with no stated reason, so the box's real Pi beat a stub the caller put first (#437).
# Which version it finds is install-check's to guard.
mac_path := if os() == "macos" { "/opt/homebrew/opt/coreutils/libexec/gnubin:/usr/local/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/util-linux/bin:/usr/local/opt/util-linux/bin:/opt/homebrew/bin" } else { "" }
caller_path := if replace(invocation_directory() + "/", root + "/", "") == invocation_directory() + "/" { env_var('PATH') } else { `command -v mise >/dev/null || { echo "just: mise is not on PATH, so this repo's tools (mise.toml) are not resolved; install mise $(cat mise-version) (mise-version)" >&2; printf '%s' "$PATH"; exit 0; }; m="$(mise ls --local --missing 2>/dev/null | awk '{print $1 "@" $2}' | paste -sd ' ' -)"; [[ -z "$m" ]] || echo "just: not installed: $m (mise.toml, mise.lock); run: mise install --locked" >&2; add="$(mise bin-paths 2>/dev/null | paste -sd : -)"; [[ "$(uname -s)" != Darwin ]] || add="${add:+$add:}/opt/homebrew/opt/coreutils/libexec/gnubin:/usr/local/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/util-linux/bin:/usr/local/opt/util-linux/bin:/opt/homebrew/bin"; out=""; put=""; IFS=: read -ra ds <<<"$PATH"; for d in "${ds[@]}"; do [[ -n "$d" ]] || continue; case "${d%/}" in /usr/local/sbin|/usr/local/bin|/usr/sbin|/usr/bin|/sbin|/bin) [[ -n "$put" ]] || { out+="${add:+$add:}"; put=1; } ;; esac; out+="$d:"; done; [[ -n "$put" ]] || out+="${add:+$add:}"; printf '%s' "${out%:}"` }
export PATH := root + "/scripts:" + root + "/.agents/skills/herdr-comms/assets:" + (if caller_path == env_var('PATH') { if mac_path == "" { "" } else { mac_path + ":" } } else { "" }) + caller_path + ":" + env_var('HOME') + "/.local/bin:" + parent_directory(just_executable())
# The gate never reaches the product judge or factory evals (quality #acceptance-gate-no-model). just evaluates
# this before any recipe runs, so a check or check-* recipe depending on the qa or qc recipe, directly or transitively, fails
# every run before one starts. Anything but the script's exact ok line fails closed; the one other value is the
# backtick's own text, which `just --dry-run` substitutes without running it (or any recipe).
# Backticks run in --working-directory when given: there the guard is the published command on PATH.
gate_free_out := `f=scripts/check-gate-free; [[ -x "$f" ]] || f=check-gate-free; exec "$f"`
# The scan cannot see into the repo scripts a recipe runs: a check run also exports a marker (the outermost check
# run's just pid) that nested just runs and tools inherit; qa and octo-feather-qc refuse under it (check-gate-free --refuse).
export OCTO_FEATHER_CHECK_RUN := `f=scripts/check-gate-free; [[ -x "$f" ]] || f=check-gate-free; exec "$f" --run`
gate_free := if gate_free_out == "gate-free: ok" { "ok" } else if gate_free_out == "`f=scripts/check-gate-free; [[ -x \"$f\" ]] || f=check-gate-free; exec \"$f\"`" { "dry run" } else { error("check-gate-free did not pass (message above); just check stays deterministic and free") }

default:
    @just --list

# The recipes the gate runs, in order, each one pytest item of check-tests (tests/gate/). Only check-* recipes,
# so check-gate-free's scan of them sees every recipe the gate runs.
export GATE_RECIPES := "check-languages check-scripts check-refs check-dashes check-skills check-decision-log check-roles check-behavior-smoke check-vendored check-spec-status check-templates check-evals check-lint check-format check-types check-ts"

# Every GATE_RECIPES recipe and every tests/*.sh, through check-tests (#201, #224).
# The gate: every tracked language gated, script syntax, Pi-only references, no dashes, skill frontmatter, decision logs, vendored skills, eval case shape, kit Python lint, format and types, kit tests.
check: check-tests

# Every language scc finds in the tracked files has its lint and type step here; two pnpm pins fail (rules and
# what passes by design: the head of scripts/check-languages).
check-languages:
    @python3 "$root/scripts/check-languages"

# check-languages' data (the head of scripts/check-languages): one LANGUAGE:TOOL:GATE_RECIPE:FILES_RECIPE entry
# per language scc can name and gate tool that must cover its files; FILES_RECIPE prints that tool's own file list.
check_languages := "Python:ruff:check-lint:python-files Python:basedpyright:check-types:python-files Shell:shellcheck:check-scripts:shell-files BASH:shellcheck:check-scripts:shell-files TypeScript:tsc:check-ts:ts-files TypeScript:eslint:check-ts:ts-files JavaScript:tsc:check-ts:ts-files JavaScript:eslint:check-ts:ts-files"

# ruff's own file list, which basedpyright gets whole: name an extensionless script in pyproject.toml extend-include
python-files:
    @uv run --locked --offline --no-sync octo-feather-lint files

# tsc's own file list, which eslint gets whole (check-ts): add a path to tsconfig.json include (dot paths by name)
ts-files:
    @pnpm exec tsc --showConfig | python3 -c 'import json, sys; print(*json.load(sys.stdin).get("files", []), sep="\n")'

# Minus the trees with their own gate (templates/) or frozen data (evals/, evidence/).
# ShellCheck's file list: give a file the `shell` attribute in .gitattributes
shell-files:
    @git -C "$root" ls-files ':(attr:shell)' ':(exclude)templates/' ':(exclude)evals/' ':(exclude)evidence/'

# ShellCheck (mise.toml pin) over shell-files, never a bash -n fallback (#361); every Python file of the kit's
# set (octo-feather-lint files: ruff's own list) byte-compiles: compile(), not ast.parse, refuses what parses but
# cannot run (top-level return, break, yield; #121 D1); scripts/, the herdr-comms assets and tests/ hold executables.
check-scripts:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    mapfile -t sh < <(just --justfile "$root/justfile" shell-files)
    shellcheck -S warning "${sh[@]}"; echo "scripts: shellcheck ok (${#sh[@]} files)"
    mapfile -t py < <(uv run --locked --offline --no-sync octo-feather-lint files)
    python3 -c 'import sys
    bad = 0
    for f in sys.argv[1:]:
        try: compile(open(f, "rb").read(), f, "exec", dont_inherit=True)
        except SyntaxError as e: print(f"{f}:{e.lineno}: {e.msg}; fix it: Python cannot run this file", file=sys.stderr); bad = 1
    sys.exit(bad)' "${py[@]}"
    echo "python: ok (${#py[@]} files compile)"
    for f in scripts/* .agents/skills/herdr-comms/assets/* tests/*; do
      [[ ! -f "$f" || -x "$f" ]] || { echo "check-scripts: not executable: $f; chmod +x $f" >&2; exit 1; }
    done

# No CLAUDE.md, no .claude/.codex projections, no octo-lite product names, no lane branch default.
# Exempt: docs/ (ADRs name what was rejected), AGENTS.md, README.md, NOTICE,
# LICENSE, this justfile (docs/ also covers docs/specs/) and
# .skillfile/ patches, which quote the upstream lines they remove. The lane branch default
# exempts only docs/adr/0011 (below).
check-refs:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    bad=0
    if git ls-files | grep -iE '(^|/)(CLAUDE(\.local)?\.md|AGENTS\.override\.md|\.claude|\.codex)(/|$)'; then
      echo "check-refs: Claude/Codex instruction files or projections above are not allowed; Pi is the only runtime, AGENTS.md the only instruction file (docs/adr/0001)" >&2; bad=1; fi
    mapfile -t files < <(git ls-files | grep -vE '^(docs/|\.skillfile/|AGENTS\.md$|README\.md$|NOTICE$|LICENSE$|justfile$)')
    # Retired words stay retired in all kit text, docs/ and this justfile included
    # (the pattern brackets a letter so it does not match itself). Exempt files:
    #   GLOSSARY.md: lists the retired words.
    #   vendored skills (Skillfile github entries) and .skillfile/: upstream wording and quotes of it.
    #   docs/specs/.viz/, docs/specs/.style/: Spec Chat's vendored runtime and style (NOTICE).
    #   LICENSE: the upstream Apache-2.0 text.
    #   judgment suites' label data (evals/judgment-*/ cases.json, reference/expectations.json, REPORT.md): frozen
    #   quotes of history the cases are taken from; the rest of each suite stays scanned (owner ruling 2026-10-25).
    #   The lane-branch scan below skips them too.
    labels='evals/judgment-[^/]+/(cases\.json|reference/expectations\.json|REPORT\.md)$'
    # Exempt quotes of frozen or upstream text, not kit naming: each a (file, exact quote)
    # pair in the table below, removed only in that file, then the rest of its line is scanned.
    vend="$(awk '$1 == "github" {printf "%s|", $3}' Skillfile)"
    mapfile -t own < <(git ls-files | grep -vE "^(\.agents/skills/(${vend%|})/|\.skillfile/|docs/specs/\.(viz|style)/|GLOSSARY\.md\$|LICENSE\$|$labels)")
    # Fails closed: grep exit 0 or 1 and perl exit 0 are the only scans; match is perl output, no match none,
    # any other exit a scanner error that fails the check.
    retired='\b(meta-)?[o]perators?\b|\b[h]umans?\b'
    rc=0; hits="$(grep -nHiE "$retired" "${own[@]}")" || rc=$?
    if (( rc > 1 )); then
      echo "check-refs: retired-words scanner error: grep exited $rc (message above); fix the scan, the check cannot pass" >&2; bad=1; hits=""; fi
    rc=0; found="$(RETIRED="$retired" perl -ne '
        BEGIN { %ok = (
          # Frozen spec anchor kept from octo-lite (docs/adr/0021): its definition, the index map, its citers
          # (the director role and the anchors list of the comms spec call log).
          "docs/specs/comms.spec.html"    => [qr{data-anchor="handoff-[o]perator(-wrap)?"}],
          "docs/specs/index.spec.html"    => [qr{data-anchor="map-handoff-[o]perator"}, qr{#handoff-[o]perator(?=[<"])}],
          "agents/director.md"            => [qr{`#handoff-[o]perator`}],
          "docs/specs/comms.calls.jsonl"  => [qr{"handoff-[o]perator"}],
          # The #acceptance-retired-words criterion names the words it bans.
          "docs/specs/overview.spec.html" => [qr{uses the retired word [o]perator or [h]uman}],
          # The corrector quotes vendored pstack correct.
          "agents/corrector.md"           => [qr{"The [o]perator" there is the owner}],
          # NOTICE attribution names the octo-lite file the director came from.
          "NOTICE"                        => [qr{\(was agents/meta-[o]perator\.md\)}],
          # Spec Chat names the owner side of a spool (its directory and event actor) so on disk: the one SPOOL_SIDE value per file.
          "scripts/octo-feather-accepted" => [qr{^SPOOL_SIDE = "[h]uman"(?=\s)}],
          "tests/accepted.sh"             => [qr{^SPOOL_SIDE=[h]uman(?=;)}],
        ) }
        my ($f, $s) = /^(.*?):\d+:(.*)$/s;
        $s =~ s/$_//g for @{ $ok{$f} || [] };
        if ($s =~ /$ENV{RETIRED}/i) { print }' <<<"$hits")" || rc=$?
    if (( rc != 0 )); then
      echo "check-refs: retired-words scanner error: perl exited $rc (message above); fix the scan, the check cannot pass" >&2; bad=1
    elif [[ -n "$found" ]]; then
      printf '%s\n' "$found"
      echo "check-refs: retired words above; use director for the top agent and owner for the person (GLOSSARY.md)" >&2; bad=1; fi
    # Lane branch strings: the owner's #71 shapes (#121 N1 N2), owned by docs/adr/0011, not scanned (nor the judgment label data above).
    # The patterns bracket a letter so this justfile does not match itself.
    mapfile -t lane < <(git ls-files | grep -vE "^(docs/adr/0011-|$labels)")
    if grep -nHE -e 'octo-feather/g[h]<' -e 'g[h]<[^>]*>-<' "${lane[@]}"; then
      echo "check-refs: lane branch default above; the lane branch is \`gh<N>\`: write only a pointer, docs/adr/0011" >&2; bad=1; fi
    # Pi has no Skill tool: a skill loads by reading its SKILL.md by path. Fixed strings, in skills (vendored too) and role files (#107).
    if git ls-files -z .agents/skills agents | xargs -0 grep -nHF -e 'Skill tool' -e 'Skill call'; then
      echo "check-refs: Skill tool named above; Pi has none: write 'read the \`<name>\` skill (\`../<name>/SKILL.md\`)', vendored skills through .skillfile/patches (#107)" >&2; bad=1; fi
    if grep -nHE 'octo-lite-|\.octo-lite|octo-lite:' "${files[@]}"; then
      echo "check-refs: octo-lite product names above; rename to octo-feather (attribution stays in NOTICE)" >&2; bad=1; fi
    [[ "$bad" == 0 ]] && echo "refs: ok (${#files[@]} files)"
    exit "$bad"

# Dash rule and its upstream carve-outs: #121 D7. Scans tracked files minus docs/specs/.viz/, docs/specs/.style/,
# LICENSE, the Skillfile's github entries in .agents/skills/ and .skillfile/.
check-dashes:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    vend="$(awk '$1 == "github" {printf "%s|", $3}' Skillfile)"
    mapfile -t files < <(git ls-files | grep -vE "^(docs/specs/\.(viz|style)/|\.agents/skills/(${vend%|})/|\.skillfile/|LICENSE\$)")
    if grep -nHF -e "$(printf '\xe2\x80\x93')" -e "$(printf '\xe2\x80\x94')" "${files[@]}"; then
      echo "check-dashes: replace the em/en dashes above with a colon, comma or parentheses" >&2; exit 1; fi
    echo "dashes: ok (${#files[@]} files)"

# Every skill opens with a --- frontmatter block with non-empty name and description; every role file exists.
check-skills:
    @python3 "$root/scripts/check-skills"

# Every tracked decisions.jsonl, anywhere in the repo: each line one JSON object matching schemas/decision-log.schema.json (quality #decision-log, docs/adr/0010).
check-decision-log:
    @python3 "$root/scripts/check-decision-log"

# Kit Python (#244): templates/python's ruff check (every rule), ruff format --check and strict basedpyright
# over every tracked *.py and Python-shebang file the root ruff config keeps (its extend-exclude names each
# exclusion and why). Today's violations sit in each tool's own baseline, which only shrinks: pyproject.toml
# [tool.ruff.lint.extend-per-file-ignores] and [tool.ruff.format] exclude, .basedpyright/baseline.json
# (scripts/octo-feather-lint --help). Pinned in pyproject.toml and uv.lock, run offline from the uv cache.
check-lint:
    @uv run --locked --offline --no-sync octo-feather-lint lint

check-format:
    @uv run --locked --offline --no-sync octo-feather-lint format

check-types:
    @uv run --locked --offline --no-sync octo-feather-lint types

# Kit TypeScript (#245): templates/typescript's tsc (@tsconfig/strictest) and eslint (typescript-eslint
# strict-type-checked and stylistic-type-checked) over the files tsconfig.json declares (its exclude names each
# exclusion and why); eslint gets exactly tsc's list (tsc --showConfig), never a directory. Pinned in package.json
# and pnpm-lock.yaml at the template's versions, installed offline from the pnpm store (filled once, with network:
# CI's pnpm step; install-check names the command). Today's eslint violations in extensions/spend-ledger.ts and its
# test fixture sit in eslint's own bulk suppressions, eslint-suppressions.json (per file and rule, a count), which only
# shrinks: a rule over its count fails (eslint then lists every occurrence of it in that file), an unused entry fails
# until pruned. tsc has no baseline: its errors are fixed in place.
# One recipe, not two: two gate items installing node_modules at once would race.
check-ts:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    err="$(pnpm install --offline --frozen-lockfile 2>&1)" || { printf '%s\n' "$err" >&2
      echo "check-ts: tsc and eslint (pnpm-lock.yaml) are not in the pnpm store; fetch them once, with network: pnpm install --frozen-lockfile --dir $root" >&2; exit 1; }
    cfg="$(pnpm exec tsc --showConfig)" || { printf '%s\n' "$cfg" >&2; echo "check-ts: tsc cannot read tsconfig.json (error above)" >&2; exit 1; }
    mapfile -t files < <(python3 -c 'import json, sys; sys.stdout.writelines(f + "\n" for f in json.load(sys.stdin).get("files", []))' <<<"$cfg")
    (( ${#files[@]} )) || { echo "check-ts: tsconfig.json lists no files" >&2; exit 1; }
    bad=0
    pnpm exec tsc || { bad=1; echo "check-ts: fix each tsc error above at its file(line,col)" >&2; }
    pnpm exec eslint --max-warnings 0 -- "${files[@]}" || { bad=1
      echo "check-ts: fix each eslint finding above at its file, line:col; rule docs: https://typescript-eslint.io/rules/<rule> or https://eslint.org/docs/latest/rules/<rule> (an exception: // eslint-disable-next-line <rule> -- <reason>, on its line). Never add to eslint-suppressions.json; an unused entry there is pruned: pnpm exec eslint --prune-suppressions -- ${files[*]}" >&2; }
    [[ "$bad" == 0 ]] && echo "ts: ok (${#files[@]} files: tsc, eslint)"
    exit "$bad"

# Every template wires the same gate and pins its tools with mise at the kit's versions (rules: the head of
# scripts/check-templates): AGENTS.md with a `Repo skills:` line, check, integrate and qc recipes, check-languages
# in the gate, a git hook that runs `just check` (the hook is run against a recording just), mise.toml, mise.lock
# and the kit's mise-version. Each template's own `just check` runs in its repo (no network here).
check-templates:
    @python3 "$root/scripts/check-templates" "$root"

# Integration tests of the kit scripts, each in a throwaway repo (tests/*.sh). Whether a test reaches past a
# script's public surface is review's call, not a check (docs/adr/0008, #118).
# pytest + pytest-xdist (tests/gate/): each GATE_RECIPES recipe, then each tests/*.sh, one item run as a command
# (TMPDIR its real path: tests/gate/test_gate.py); every item's duration, failures with their output, one trend line
# per run in the state dir (tests/gate/conftest.py). Timing never decides pass or fail. Offline: pytest from the
# uv cache, filled by `uv sync --locked` in the kit (CI's uv step). Workers: GATE_WORKERS, default 2: half the 4 CPUs,
# since the box runs at most 2 heavy commands at once across lanes (CI sets 4). A gate run inside an item (a test's
# throwaway copy running `just check`) is sequential and stops at its first failure (-n 0 -x), recipes first, so a red
# copy fails on its recipe, never fans out a nested gate (#208).
# Every gate recipe and kit test as a pytest item, parallel, timed, one trend line per run; extra arguments go to pytest.
check-tests *args:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    if [[ -n "${GATE_NESTED:-}" ]]; then set -- -n 0 -x "$@"; else set -- -n "${GATE_WORKERS:-2}" "$@"; fi
    err="$(uv sync --locked --offline --quiet 2>&1)" || { printf '%s\n' "$err" >&2
      echo "check-tests: pytest and pytest-xdist (uv.lock) are not in the uv cache; fetch them once, with network: uv sync --locked --project $root" >&2; exit 1; }
    # tsc and eslint into node_modules before the items fan out: check-languages reads tsc's file list while check-ts
    # runs, and two installs at once would race (check-ts's own install is then a no-op).
    err="$(pnpm install --offline --frozen-lockfile 2>&1)" || { printf '%s\n' "$err" >&2
      echo "check-tests: tsc and eslint (pnpm-lock.yaml) are not in the pnpm store; fetch them once, with network: pnpm install --frozen-lockfile --dir $root" >&2; exit 1; }
    GATE_NESTED=1 exec uv run --locked --offline --no-sync pytest "$@"

# The gate's pytest items, all or a subset by pytest arguments (`just test -k check-dashes`, `just test --lf`): check-tests.
test *args:
    @just check-tests "$@"

# Every docs/specs/*.status.json names exactly its spec's criterion ids, planned or built, and every spec change
# since its accepted_commit is named by a call in <slug>.calls.jsonl (docs/adr/0021, issue-lifecycle #gates-spec-calls).
check-spec-status:
    @python3 "$root/scripts/octo-feather-spec-status" check "$root/docs/specs"

# Each vendored skill folder equals upstream at its Skillfile pin plus its patches (skills spec #acceptance-patch-only).
# No network: reads the authenticated pin-SHA cache `just vendored-fetch` fills; a missing cache fails naming it.
check-vendored:
    @python3 "{{root}}/scripts/check-vendored"

# Fill the check-vendored cache: pinned skillfile binary, each Skillfile pin commit (fetch-only Spec Chat included, #96), every call time-bounded. Never inside `just check`.
vendored-fetch:
    @python3 "{{root}}/scripts/check-vendored" --fetch

# Owner shaping chat in the target repo: Pi with only the shaping skills, not a factory role (docs/adr/0021).
[no-cd]
shape *args:
    octo-feather-shape "$@"

# Spec Chat's skills into REPO/.agents/skills as git-ignored links into $SPEC_CHAT_CLONE (default ~/src/spec-chat); no provider links (docs/adr/0001).
[no-cd]
spec-chat repo:
    octo-feather-spec-chat "$1"

# Integrate worker commits onto the lane's branch (its lane key: gh12, eng-123 for ENG-123), then its `just check`; non-zero on any conflict (docs/adr/0017).
[no-cd]
integrate issue +refs:
    octo-feather-integrate "$@"

# Every eval case's shape (rules: .agents/skills/eval-cases/references/schema.md; quality #acceptance-qa-cases-checked).
check-evals:
    @python3 "$root/scripts/check-evals"

# Role files: only fields pi-role honours, skills resolve, allowed models (docs/adr/0013).
check-roles:
    @python3 "$root/scripts/check-roles"

# A role path changed on this branch needs evidence/*.md and docs/owed-evals/*.md in the same diff, or Behaviour-neutral commits (docs/adr/0008, correction lane #26). Base: origin/main or the CI PR base; none: skips locally, fails in CI.
check-behavior-smoke:
    @python3 "$root/scripts/check-behavior-smoke"

# Verify the runtime tools on this box (octo-lite's install --check equivalent), agent-browser at its pin included, and the tracker CLI of the target
# (the invocation directory, or TARGET: `just -f KIT/justfile install-check` in it); a Linear target checks linear,
# each pinned tool's first hit on CALLER_PATH (default the caller's PATH, which panes and shells resolve) is the
# pinned one, or that launcher is named with the fix;
# a target whose qc.toml declares [browser] checks Playwright's headless Chromium shell at its pin.
install-check target=invocation_directory() $CALLER_PATH=env_var('PATH'):
    #!/usr/bin/env bash
    set -uo pipefail
    bad=0
    for t in herdr pi gh jq git just python3 node pnpm; do
      if p="$(command -v "$t")"; then printf '%-6s ok  %s\n' "$t" "$p"
      else printf '%-6s MISSING\n' "$t"; bad=1; fi
    done
    # Pi at the pin in pi-version (docs/adr/0023 Consequences).
    pin="$(tr -d '[:space:]' <"$root/pi-version")"
    if p="$(command -v pi)"; then
      v="$(pi --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
      if [[ "$v" == "$pin" ]]; then printf 'pi     version %s ok (pi-version)\n' "$v"
      else printf 'pi     WRONG VERSION %s reports %s, want %s (pi-version); npm install -g --ignore-scripts @earendil-works/pi-coding-agent@%s\n' "$p" "${v:-no version}" "$pin" "$pin"; bad=1; fi
    fi
    # Native tools (owner ruling #261): mise at mise-version, then each mise.toml tool at its mise.lock version in the
    # target (the kit itself when run there) when it has its own mise.toml; a repo without one (a repo the kit did not
    # create) keeps its own pins: no tool line, its panes get no mise shims (scripts/pi-role). Each repo's justfile
    # puts its own mise tools on PATH for its recipes; where the caller's PATH resolves them: the PATH check below.
    # A mise.toml with only [tools] needs no trust; a "not trusted" answer means it gained [env], [tasks] or hooks.
    python3 -c 'import json, os, shutil, subprocess, sys
    root, top = sys.argv[1], sys.argv[2]
    pin = open(os.path.join(root, "mise-version")).read().strip()
    how = f"install mise {pin}: https://github.com/jdx/mise/releases/tag/v{pin} (sha256 from its SHASUMS256.txt)"
    exe = shutil.which("mise")
    if not exe: sys.exit(f"mise   MISSING (want {pin}, mise-version); {how}")
    v = subprocess.run(["mise", "--version"], capture_output=True, text=True).stdout.split()
    got = v[0] if v else "no version"
    if got != pin: sys.exit(f"mise   WRONG VERSION {exe} reports {got}, want {pin} (mise-version); {how}")
    print(f"mise   version {pin} ok (mise-version)")
    shims = json.loads(subprocess.run(["mise", "doctor", "--json"], capture_output=True, text=True).stdout or "{}").get("dirs", {}).get("shims", "")
    bad = 0
    # Tools the kit itself runs from PATH in any target, so at the kit mise.lock version there too: just (the kit
    # recipes, just integrate, check-gate-free and octo-feather-lane read the --dump and --dry-run answers of just).
    # Only the version on PATH is compared: nothing is installed or resolved through mise in the target.
    kit_pins = json.loads(subprocess.run(["mise", "-C", root, "ls", "--local", "--json"], capture_output=True, text=True).stdout or "{}")
    for tool in ("just",):
        want = (kit_pins.get(tool) or [{}])[0].get("version")
        path = shutil.which(tool)
        got = (subprocess.run([tool, "--version"], capture_output=True, text=True).stdout.split() + ["", ""])[1] if path else "nothing"
        if got == want: print(f"{tool:<6} version {got} ok (kit mise.lock)")
        else: print(f"{tool:<6} WRONG VERSION {path or tool} reports {got}, want {want} (kit mise.lock); the kit runs it in every target: put {tool} {want} first on PATH (the kit mise install: cd {root} and mise install --locked, then {shims} first), or install {tool} {want}"); bad = 1
    for d in [os.path.realpath(top)]:
        if not os.path.isfile(os.path.join(d, "mise.toml")): continue
        fix = f"mise -C {d} install --locked"
        r = subprocess.run(["mise", "-C", d, "ls", "--local", "--json"], capture_output=True, text=True)
        if r.returncode:
            print(f"mise   {d}/mise.toml UNREADABLE: {r.stderr.strip()} (a [tools]-only mise.toml needs no trust; review it, then mise trust {d}/mise.toml)"); bad = 1; continue
        for tool, rows in json.loads(r.stdout or "{}").items():
            row = rows[0] if rows else {}
            have, want = row.get("version"), row.get("requested_version")
            if row.get("installed"): print(f"mise   {tool} {have} ok ({d}/mise.lock)")
            else: print(f"mise   {tool} {want} MISSING ({d}/mise.lock); {fix}"); bad = 1
    sys.exit(bad)' "$root" "$(git -C "$1" rev-parse --show-toplevel 2>/dev/null || echo "$1")" || bad=1
    # agent-browser at the pin in agent-browser-version, the vendored agent-browser skill's release (spec remote#host-tools).
    # Its postinstall marks the native binary executable, so no --ignore-scripts. It starts a Chrome it finds (Playwright's
    # included); `agent-browser doctor` names it, `agent-browser install` downloads one where none is found.
    pin="$(tr -d '[:space:]' <"$root/agent-browser-version")"
    how="npm install -g agent-browser@$pin (then agent-browser doctor --offline; no Chrome found: agent-browser install)"
    if ! p="$(command -v agent-browser)"; then printf 'agent-browser MISSING (want %s, agent-browser-version); %s\n' "$pin" "$how"; bad=1
    else
      v="$(agent-browser --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
      if [[ "$v" == "$pin" ]]; then printf 'agent-browser version %s ok (agent-browser-version)\n' "$v"
      else printf 'agent-browser WRONG VERSION %s reports %s, want %s (agent-browser-version); %s\n' "$p" "${v:-no version}" "$pin" "$how"; bad=1; fi
    fi
    # The caller's PATH (#422 item 2: older launchers earlier on PATH ran instead of the pinned mise, node, pnpm, uv):
    # for each pinned tool, its first hit there is the pinned one (ok, its path), else that launcher is named with the
    # pinned path and the fix. Pinned: mise, pi, agent-browser and just (when the target pins no just) by version, the
    # first hit reporting the pin (none on PATH at the pin: the version lines above name the install); every executable
    # of the target mise.toml tools by path, mise's shim or `mise bin-paths` install (a shim when there is one).
    python3 -c 'import json, os, re, subprocess, sys
    root, top, path = sys.argv[1], os.path.realpath(sys.argv[2]), sys.argv[3]
    dirs = [d for d in path.split(":") if os.path.isabs(d)]
    def run(*a):
        try: return subprocess.run(a, capture_output=True, text=True, timeout=20, cwd=top, stdin=subprocess.DEVNULL).stdout
        except (OSError, subprocess.SubprocessError): return ""
    def hits(name):
        fs = [os.path.join(d, name) for d in dirs]
        return list(dict.fromkeys(f for f in fs if os.path.isfile(f) and os.access(f, os.X_OK)))
    def version(f):
        m = re.search(r"[0-9]+\.[0-9]+\.[0-9]+", run(f, "--version"))
        return m.group(0) if m else None
    bad = 0
    def line(name, first, ok, pinned, why):
        global bad
        if ok: print(f"path   {name} ok  {first} ({why})"); return
        print(f"path   {name} SHADOWED {first} comes first on PATH, before the pinned {pinned} ({why}); remove or rename {first}, or put {os.path.dirname(pinned)} first on PATH"); bad = 1
    def js(*a):
        try: return json.loads(run(*a) or "{}")
        except ValueError: return {}
    pin = {n: open(os.path.join(root, n + "-version")).read().strip() for n in ("mise", "pi", "agent-browser")}
    mise = next((h for h in hits("mise") if version(h) == pin["mise"]), "mise")  # a stale mise first answers nothing useful
    shims = js(mise, "doctor", "--json").get("dirs", {}).get("shims", "")
    bins = {}  # executable name: its pinned path, for the target mise.toml tools
    if os.path.isfile(os.path.join(top, "mise.toml")):
        for b in run(mise, "-C", top, "bin-paths").split("\n"):
            for n in sorted(os.listdir(b)) if b and os.path.isdir(b) else []:
                f = os.path.join(b, n)
                if os.path.isfile(f) and os.access(f, os.X_OK): bins.setdefault(n, f)
    kit = js(mise, "-C", root, "ls", "--local", "--json")
    pins = [(n, pin[n], f"{n}-version") for n in pin] + [("just", (kit.get("just") or [{}])[0].get("version"), "kit mise.lock")]
    for name, want, why in pins:
        if name in bins or not (hs := hits(name)): continue
        pinned = next((h for h in hs if version(h) == want), None)
        if pinned: line(name, hs[0], hs[0] == pinned, pinned, why)
    for name, f in sorted(bins.items()):
        if not (hs := hits(name)): continue
        shim = os.path.join(shims, name) if shims else ""
        pinned = shim if shim and os.path.isfile(shim) else f
        ok = os.path.dirname(hs[0]) == shims or os.path.realpath(hs[0]) in (os.path.realpath(f), os.path.realpath(pinned))
        line(name, hs[0], ok, pinned, f"{top}/mise.lock")
    sys.exit(bad)' "$root" "$(git -C "$1" rev-parse --show-toplevel 2>/dev/null || echo "$1")" "$2" || bad=1
    # The kit's TypeScript tools (check-ts, #245): pnpm's copy of the lockfile in node_modules equals pnpm-lock.yaml once
    # the fetch below ran, which also filled the pnpm store check-ts installs from offline. A file compare, not a pnpm call:
    # pnpm under another HOME (corepack's shim) would download itself.
    if cmp -s "$root/pnpm-lock.yaml" "$root/node_modules/.pnpm/lock.yaml"; then echo "pnpm   kit TypeScript tools ok (pnpm-lock.yaml)"
    else echo "pnpm   kit TypeScript tools NOT FETCHED (pnpm-lock.yaml); fetch them once, with network: pnpm install --frozen-lockfile --dir $root"; bad=1; fi
    gh auth status >/dev/null 2>&1 && echo "gh     authenticated" || { echo "gh     NOT authenticated (gh auth login)"; bad=1; }
    # The target's tracker skill, resolved as pi-role resolves {tracker}; its optional scripts/install-check checks its CLI.
    skill="$(python3 -c 'import importlib.machinery as m, importlib.util as u, sys
    s = u.spec_from_loader("pi_role", m.SourceFileLoader("pi_role", sys.argv[1] + "/scripts/pi-role")); r = u.module_from_spec(s); s.loader.exec_module(r)
    print(r.tracker_skill(sys.argv[1] + "/.agents/skills", sys.argv[2]))' "$root" "$1")" || exit 1
    echo "tracker ${skill} (target $1)"
    c="$root/.agents/skills/$skill/scripts/install-check"
    [[ ! -x "$c" ]] || "$c" || bad=1
    # A target whose qc.toml has [browser] (its verify skill drives a headless browser, spec remote#host-tools):
    # Playwright's headless Chromium shell at the pinned Playwright release, once per box in
    # ${XDG_DATA_HOME:-~/.local/share}/octo-feather/ms-playwright/<pin>, the PLAYWRIGHT_BROWSERS_PATH a drive sets.
    # Never under ~/.cache: the qc sandbox masks it. No qc.toml or no [browser]: no browser line.
    top="$(git -C "$1" rev-parse --show-toplevel 2>/dev/null || echo "$1")"
    bpin="$(python3 -c 'import os, re, sys, tomllib
    p = os.path.join(sys.argv[1], "qc.toml")
    if not os.path.isfile(p): sys.exit(0)
    try: b = tomllib.load(open(p, "rb")).get("browser")
    except (OSError, ValueError) as e: sys.exit(f"browser {p}: not TOML: {e} (octo-feather-contract)")
    if b is None: sys.exit(0)
    v = b.get("playwright") if isinstance(b, dict) else None
    if not isinstance(v, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v): sys.exit(f"browser {p}: [browser] playwright must be a release like 1.64.1 (octo-feather-contract)")
    print(v)' "$top")" || bad=1
    if [[ -n "$bpin" ]]; then
      folder="${XDG_DATA_HOME:-$HOME/.local/share}/octo-feather/ms-playwright/$bpin"; cache="${XDG_CACHE_HOME:-$HOME/.cache}"
      shell="$(ls -d "$folder"/chromium_headless_shell-*/INSTALLATION_COMPLETE 2>/dev/null | head -1)"
      if [[ "$folder/" == "$cache/"* ]]; then
        printf 'browser UNREADABLE IN THE QC SANDBOX %s is under %s, which the sandbox masks; set XDG_DATA_HOME outside it\n' "$folder" "$cache"; bad=1
      elif [[ -n "$shell" ]]; then printf 'browser ok  %s (Playwright %s; PLAYWRIGHT_BROWSERS_PATH=%s)\n' "${shell%/INSTALLATION_COMPLETE}" "$bpin" "$folder"
      else printf 'browser MISSING (want Playwright %s headless Chromium shell in %s); install: PLAYWRIGHT_BROWSERS_PATH=%s npx -y playwright@%s install --only-shell chromium\n' "$bpin" "$folder" "$folder" "$bpin"; bad=1; fi
    fi
    exit "$bad"

# Start the director in Herdr workspace `director` (docs/adr/0011).
start cwd=invocation_directory():
    octo-feather-start --director --cwd "$1"

# Start one supervisor for a ticket as the tracker writes it (12, ENG-123) in workspace named by its lane key (gh12, eng-123), tab `supervisor`.
supervise issue cwd=invocation_directory():
    octo-feather-start --issue "$1" --cwd "$2"

# Product QC: a fresh cross-family judge runs each claimed criterion; passed ones become built (docs/adr/0022). Never inside `just check`.
# Arguments reach bash as "$@" and exported variables, never as interpolated source (#30, #61).
[no-cd]
qc $status $pr +$ids:
    octo-feather-qc "$@"

# Factory QA: each eval case (evals/) runs its role headless in the qc sandbox; PASS/FAIL per case from transcript facts (octo-feather-qa --help). Never inside `just check`.
qa *args:
    @[[ "$(check-gate-free --refuse 'just qa (factory evals)')" == "gate-free: ok" ]]
    octo-feather-qa "$@"

# Print this Herdr session's octo-feather state directory.
state:
    @octo-feather-state

# New target repo at DEST from templates/LANG: tracked files, one commit on main, Spec Chat links unless --no-spec-chat; never `just setup` or GitHub (#21).
# Arguments reach bash as "$@" and exported variables, never as interpolated source (#61).
[no-cd]
new-repo $lang $dest *$flags:
    octo-feather-new-repo "$@"

# Opt-in, never part of `just check`: tests/qc.sh with the box's real herdr (QC_TEST_HERDR=real) for the
# sandbox pane proof: a judge's pane runs in its PID namespace, reaches no live session and dies with the run.
# Offline like the gate; a throwaway HOME with its own "live" session, the box's sessions untouched. Needs herdr on PATH.
qc-real-herdr:
    QC_TEST_HERDR=real "$root/tests/qc.sh"
