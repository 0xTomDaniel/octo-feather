# octo-feather kit commands. The gate's tiers, `just fast` and `just check`: quality spec #recipes-table (AGENTS.md).

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
caller_path := if replace(invocation_directory() + "/", root + "/", "") == invocation_directory() + "/" { env_var('PATH') } else { `command -v mise >/dev/null || { echo "just: mise is not on PATH, so this repo's tools (mise.toml) are not resolved; install mise $(cat mise-version) (mise-version)" >&2; printf '%s' "$PATH"; exit 0; }; m="$(mise ls --local --missing 2>/dev/null | awk '{print $1 "@" $2}' | paste -sd ' ' -)"; [[ -z "$m" ]] || echo "just: not installed: $m (mise.toml, mise.lock); run: $PWD/scripts/octo-feather-mise-install $PWD" >&2; add="$(mise bin-paths 2>/dev/null | paste -sd : -)"; [[ "$(uname -s)" != Darwin ]] || add="${add:+$add:}/opt/homebrew/opt/coreutils/libexec/gnubin:/usr/local/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/util-linux/bin:/usr/local/opt/util-linux/bin:/opt/homebrew/bin"; out=""; put=""; IFS=: read -ra ds <<<"$PATH"; for d in "${ds[@]}"; do [[ -n "$d" ]] || continue; case "${d%/}" in /usr/local/sbin|/usr/local/bin|/usr/sbin|/usr/bin|/sbin|/bin) [[ -n "$put" ]] || { out+="${add:+$add:}"; put=1; } ;; esac; out+="$d:"; done; [[ -n "$put" ]] || out+="${add:+$add:}"; printf '%s' "${out%:}"` }
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
    # ShellCheck fanned out over the CPUs (#507): the same files and flags in batches run at once, each batch holding
    # every file one of its files sources (a `# shellcheck source=` directive or a literal path: ShellCheck follows a
    # sourced file only when it is an input of the same run), each batch's output printed whole in turn, and the run
    # exiting with the first failing batch's status. No files: one plain run, which refuses that itself.
    python3 -c 'import concurrent.futures as cf, os, re, subprocess, sys
    files = sys.argv[1:]; up = {f: f for f in files}
    def top(f):
        while up[f] != f: f = up[f]
        return f
    src = re.compile(r"shellcheck\b[^\n]*?\bsource=(\S+)|^[ \t]*(?:source|\.)[ \t]+[\x22\x27]?([^\s\x22\x27;&|$`]+)", re.M)
    for f in files:
        try: text = open(f, encoding="utf-8", errors="replace").read()
        except OSError: continue
        for m in src.finditer(text):
            p = m[1] or m[2]
            hit = next((c for c in (os.path.normpath(p), os.path.normpath(os.path.join(os.path.dirname(f), p))) if c in up), None)
            if hit and top(hit) != top(f): up[top(hit)] = top(f)
    groups = {}
    for f in files: groups.setdefault(top(f), []).append(f)
    size = lambda g: sum(os.path.getsize(f) if os.path.isfile(f) else 0 for f in g)
    bins = [[] for _ in range(os.cpu_count() or 1)]
    for g in sorted(groups.values(), key=size, reverse=True): min(bins, key=size).extend(g)
    bins = [b for b in bins if b] or [[]]
    run = lambda b: subprocess.run(["shellcheck", "-S", "warning", *b], capture_output=True, text=True)
    rc = 0
    try:
        with cf.ThreadPoolExecutor(len(bins)) as pool:
            for r in pool.map(run, bins):
                sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); rc = rc or r.returncode
    except FileNotFoundError: print("check-scripts: shellcheck not found on PATH (mise.toml pins it)", file=sys.stderr); rc = 127
    sys.exit(rc)' "${sh[@]}"; echo "scripts: shellcheck ok (${#sh[@]} files)"
    # Fails closed (#507): a lister that fails is never an empty list.
    list="$(uv run --locked --offline --no-sync octo-feather-lint files)" || { echo "check-scripts: the Python file list (octo-feather-lint files) failed (error above), so no Python file was compiled; fix that error (a module not found: the kit's environment is not synced: uv sync --locked --project $root)" >&2; exit 1; }
    py=(); [[ -z "$list" ]] || mapfile -t py <<<"$list"
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
          "tests/gate/kit/accepted.py"    => [qr{^SPOOL_SIDE = "[h]uman"(?=\s)}],
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

# The gate's side of skills spec #loading-refuse (scripts/check-skills); every role file exists.
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
# uv cache, filled by `uv sync --locked` in the kit (CI's uv step). Workers: GATE_WORKERS, default 8: the fastest wall
# measured on the 4-vCPU box, quiet, 105 items (#510): 2 workers 410 s, 4 269 s, 6 225-238 s, 8 213-231 s, ~730-800
# CPU s each (the CPU floor ~190 s); no item over 60 s at 6 or 8 (CI sets 4). A gate run inside an item (a test's
# throwaway copy running `just check`) is sequential and stops at its first failure (-n 0 -x), recipes first, so a red
# copy fails on its recipe, never fans out a nested gate (#208).
# Every gate recipe and kit test as a pytest item, parallel, timed, one trend line per run; extra arguments go to pytest.
check-tests *args:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    if [[ -n "${GATE_NESTED:-}" ]]; then set -- -n 0 -x "$@"; else set -- -n "${GATE_WORKERS:-8}" "$@"; fi
    # The gate's Python: .python-version's release, owned by uv (owner ruling #422, #261), found as uv sync finds it
    # (a venv skipped); without it uv sync --offline only says no interpreter. The fix's --no-bin: its message.
    err="$(uv python find --system 2>&1)" || { printf '%s\n' "$err" >&2
      echo "check-tests: the gate's Python $(<.python-version) (.python-version) is not installed; install it once, with network: uv python install --no-bin $(<.python-version) (--no-bin: no python3.X link in ~/.local/bin, which would change the interpreter uv finds for every other repo on the box)" >&2; exit 1; }
    err="$(uv sync --locked --offline --quiet 2>&1)" || { printf '%s\n' "$err" >&2
      echo "check-tests: pytest and pytest-xdist (uv.lock) are not in the uv cache; fetch them once, with network: uv sync --locked --project $root" >&2; exit 1; }
    # tsc and eslint into node_modules before the items fan out: check-languages reads tsc's file list while check-ts
    # runs, and two installs at once would race (check-ts's own install is then a no-op).
    err="$(pnpm install --offline --frozen-lockfile 2>&1)" || { printf '%s\n' "$err" >&2
      echo "check-tests: tsc and eslint (pnpm-lock.yaml) are not in the pnpm store; fetch them once, with network: pnpm install --frozen-lockfile --dir $root" >&2; exit 1; }
    # mise's state dir one empty dir per gate run, removed after it, inherited by every item and nested run: each
    # `mise` an item runs in a temp repo records it there (tracked-configs), never in the user's, where the link
    # dangles once the repo goes (#493 AC7). Nothing the gate runs needs the user's trust entries: the kit's and the
    # templates' mise.toml are [tools] only. As the qc sandbox's per-run state dir (scripts/octo-feather-qc-sandbox, step 6).
    if [[ -z "${GATE_NESTED:-}" ]]; then MISE_STATE_DIR="$(mktemp -d)"; export MISE_STATE_DIR; trap 'rm -rf "$MISE_STATE_DIR"' EXIT; fi
    GATE_NESTED=1 uv run --locked --offline --no-sync pytest "$@"

# The fast tier (quality #recipe-fast; when it suffices: issue-lifecycle #lanes-checkpoints): the gate items
# scripts/octo-feather-gate select chooses, each named with why, through check-tests.
fast:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    ids="$(python3 "$root/scripts/octo-feather-gate" select)"
    mapfile -t ids <<<"$ids"
    just check-tests "${ids[@]}"

# The dry run of just fast: the items it would select, each with why, and the count; runs none.
fast-list:
    @python3 "$root/scripts/octo-feather-gate" select 2>&1 >/dev/null

# The coverage map just fast selects from: every gate item run under coverage.py (COVERAGE_PROCESS_START and the
# .pth coverage installs in the kit venv; one data dir per item, GATE_ITEM: tests/gate/coverage.toml), on a clean tree,
# written for HEAD into the git common dir (scripts/octo-feather-gate map), from the items that passed; exits as the run did.
# Slower than just check; never in it or CI.
fast-map *args:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$root"
    [[ -z "$(git status --porcelain)" ]] || { echo "fast-map: the tree has changes; commit them first, the map is written for HEAD" >&2; exit 1; }
    d="$(mktemp -d)"; trap 'rm -rf "$d"' EXIT
    rc=0; env -u GATE_ITEM COV_MAP_DIR="$d" COVERAGE_PROCESS_START="$root/tests/gate/coverage.toml" just check-tests --junitxml="$d/junit.xml" "$@" || rc=$?
    uv run --locked --offline --no-sync python3 "$root/scripts/octo-feather-gate" map "$d" --junit "$d/junit.xml"
    exit "$rc"

# The gate's pytest items, all or a subset by pytest arguments (`just test -k check-dashes`, `just test --lf`): check-tests.
test *args:
    @just check-tests "$@"

# #493 AC1 on this box: the gate, or the items pytest args choose (`just check-user-mise -k qc`), run as tests/user-mise.sh's
# fixture user (global mise tools absent from the kit lock, python3 a mise shim, stale shims), in a named Herdr
# session's pane, or outside Herdr with USER_MISE_HERDR=none; the caller's GATE_WORKERS (default 1); not a gate item (the gate runs tests/user-mise.sh's own assertions), never in CI.
# The gate, or chosen items, inside tests/user-mise.sh's fixture HOME (#493 AC1); extra arguments go to pytest.
check-user-mise *args:
    @"$root/tests/user-mise.sh" --gate "$@"

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

# Owner shaping chat in the target repo: the shaper role (agents/shaper.md) through pi-role, outside the factory (docs/adr/0021).
[no-cd]
shape *args:
    octo-feather-shape "$@"

# Spec Chat's skills into REPO/.agents/skills as git-ignored links into $SPEC_CHAT_CLONE (default ~/src/spec-chat); no provider links (docs/adr/0001).
[no-cd]
spec-chat repo:
    octo-feather-spec-chat "$1"

# Integrate worker commits onto the lane's branch (its lane key: gh12, eng-123 for ENG-123), then its `just fast`, or `just check` at a checkpoint (--full forces it); non-zero on any conflict or red gate (docs/adr/0017).
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
# each pinned tool's first hit on the PATH the kit runs it from (this recipe's own PATH, the justfile's caller_path
# rule, and the PATH pi-role gives a pane started from CALLER_PATH, default the caller's) is the pinned one, or that
# launcher is named with the fix; one only CALLER_PATH itself finds first is a NOTE line, never a failure;
# a target whose qc.toml declares [browser] checks Playwright's headless Chromium shell at its pin; the box facts
# (kernel, user namespaces, state folder, kit install, agent-browser's browser, optional ffmpeg), Spec Chat's review
# service (else its installer run), the one manual step, and one line naming just install-check-models (no model call).
# Every gap line names its fix (#461).
install-check target=invocation_directory() $CALLER_PATH=env_var('PATH'):
    #!/usr/bin/env bash
    set -uo pipefail
    bad=0
    # The install of a repo's own locked mise tools, every fix line below: scripts/octo-feather-mise-install owns it
    # (#493 AC5). locked DIR prints it for DIR.
    locked() { printf '%s' "$root/scripts/octo-feather-mise-install $1"; }
    # Each missing tool names its official install (#461): Herdr's installer, Pi at pi-version through npm (docs/adr/0023),
    # GitHub CLI's apt repository (not Debian's gh: broken at 2.45 and 2.46), Debian and Ubuntu packages, the kit's mise tools.
    declare -A fix=([herdr]="curl -fsSL https://herdr.dev/install.sh | sh"
      [pi]="npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$(tr -d '[:space:]' <"$root/pi-version") (pi-version)"
      [gh]='(Debian, Ubuntu: GitHub CLI'"'"'s apt repository) (type -p wget >/dev/null || (sudo apt update && sudo apt install wget -y)) && sudo mkdir -p -m 755 /etc/apt/keyrings && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg && sudo mkdir -p -m 755 /etc/apt/sources.list.d && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt update && sudo apt install gh -y'
      [jq]="sudo apt install jq (Debian, Ubuntu)" [git]="sudo apt install git (Debian, Ubuntu)"
      [python3]="install Python 3.11 or later as the box python3 (Debian 12, Ubuntu 24.04: apt install python3), first on PATH")
    for t in herdr pi gh jq git just python3 node pnpm; do
      if p="$(command -v "$t")"; then printf '%-6s ok  %s\n' "$t" "$p"
      else printf '%-6s MISSING; %s\n' "$t" "${fix[$t]:-$(locked "$root") (kit mise.toml), then put the mise shims folder first on PATH}"; bad=1; fi
    done
    # The gate's Python (owner ruling #422, #261): the release the kit's .python-version pins, owned by uv
    # (python-build-standalone), found as check-tests finds it, with venv and ensurepip (tests make venvs) and
    # os.pidfd_open (tests/fixtures/start-nohup); and the box python3, which runs the kit's stdlib scripts outside the
    # gate, at 3.11 or later (tomllib). The fix's --no-bin: its message.
    python3 -c 'import os, re, shutil, subprocess, sys
    root = sys.argv[1]
    pin = open(os.path.join(root, ".python-version")).read().strip()
    fix = f"uv python install --no-bin {pin} (--no-bin: no python3.X link in ~/.local/bin, which would change the interpreter uv finds for every other repo on the box)"
    def run(*a):
        try: r = subprocess.run(a, capture_output=True, text=True, timeout=60, cwd=root, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError): return 1, ""
        return r.returncode, r.stdout.strip()
    bad = 0
    rc, exe = run("uv", "python", "find", "--system")
    probe = "import importlib.util as u, os, platform; print(platform.python_version(), *[n for n in (\"venv\", \"ensurepip\") if u.find_spec(n) is None], *([] if hasattr(os, \"pidfd_open\") else [\"os.pidfd_open\"]))"
    got = run(exe, "-c", probe)[1].split() if not rc and exe else []
    if not got: print(f"python gate {pin} MISSING (.python-version); {fix}"); bad = 1
    elif got[0] != pin or got[1:]: lacks = " ".join(got[1:]) or "nothing"; print(f"python gate {pin} UNUSABLE {exe} reports {got[0]}, lacks {lacks} (.python-version: {pin}, venv, ensurepip, os.pidfd_open); {fix}"); bad = 1
    else: print(f"python gate {pin} ok  {exe} (venv, pidfd_open; .python-version)")
    box = shutil.which("python3")
    m = re.search(r"([0-9]+)\.([0-9]+)\.[0-9]+", run(box, "--version")[1]) if box else None
    how = "install Python 3.11 or later as the box python3 (Debian 12, Ubuntu 24.04: apt install python3), first on PATH"
    if m and (int(m[1]), int(m[2])) >= (3, 11): print(f"python3 version {m[0]} ok  {box} (3.11 or later, the kit scripts)")
    else: has, name = (m[0] if m else "no version"), box or "python3"; print(f"python3 WRONG VERSION {name} reports {has}, want 3.11 or later (the kit scripts read TOML with tomllib); {how}"); bad = 1
    sys.exit(bad)' "$root" || bad=1
    # The box facts (#461): the kernel and user namespaces of spec remote#host-vm (uname and unshare -rm are the
    # probes); the session state folder octo-feather-state
    # prints, with its lanes/; the live kit install octo-feather-lane post-merge step 3 fast-forwards, the dir its
    # kit_install() names (asked of it: OCTO_FEATHER_KIT_INSTALL, else the kit dir), a clone or a worktree of one with
    # an origin, on main, detached or not (the box's install is a detached worktree beside the main checkout, #422).
    python3 -c 'import importlib.machinery as im, importlib.util as iu, os, re, subprocess, sys
    root = sys.argv[1]
    def run(*a):
        try: r = subprocess.run(a, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError) as e: return 127, "", str(e)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    bad = 0
    rel = run("uname", "-r")[1] or "unknown"
    m = re.match(r"([0-9]+)\.([0-9]+)", rel)
    if m and (int(m[1]), int(m[2])) >= (6, 6): print(f"kernel {rel} ok (6.6 or later, the qc sandbox)")
    else:
        bp = "echo \"deb http://deb.debian.org/debian bookworm-backports main\" | sudo tee /etc/apt/sources.list.d/backports.list && sudo apt update && sudo apt install -t bookworm-backports linux-image-$(dpkg --print-architecture)"
        print(f"kernel {rel} TOO OLD, want 6.6 or later (the qc sandbox overlay needs tmpfs user xattrs: scripts/octo-feather-qc-sandbox); boot a 6.6 or later kernel, then reboot (Debian 12: {bp}; Ubuntu 22.04: sudo apt install linux-generic-hwe-22.04)"); bad = 1
    rc, _, err = run("unshare", "-rm", "true")
    if not rc: print("userns ok (unshare -rm true, the qc sandbox)")
    else:
        def val(k):
            try: return open("/proc/sys/" + k).read().strip()
            except OSError: return None
        knobs = (("kernel/apparmor_restrict_unprivileged_userns", "1", "0"), ("kernel/unprivileged_userns_clone", "0", "1"), ("user/max_user_namespaces", "0", "10000"))
        sets = [k.replace("/", ".") + "=" + good for k, off, good in knobs if val(k) == off]
        if rc == 127: how = "install unshare: sudo apt install util-linux"
        elif sets: how = "allow them: printf \"" + "\\n".join(sets) + "\\n\" | sudo tee /etc/sysctl.d/60-octo-feather-userns.conf && sudo sysctl --system"
        else: how = "no sysctl here turns them off (kernel.apparmor_restrict_unprivileged_userns, kernel.unprivileged_userns_clone, user.max_user_namespaces): a container or seccomp policy does; run the kit on a VM or a bare-metal box"
        last = (err.splitlines() or ["exit " + str(rc)])[-1]
        print(f"userns FAILED unshare -rm true: {last} (the qc sandbox runs its judge in unprivileged user namespaces, #404); {how}"); bad = 1
    rc, st, _ = run(os.path.join(root, "scripts", "octo-feather-state"))
    lanes = os.path.join(st, "lanes")
    if rc or not st: print(f"state  UNREADABLE octo-feather-state failed (exit {rc}); set HOME, or XDG_STATE_HOME, to a writable folder"); bad = 1
    elif not os.path.isdir(lanes): print(f"state  MISSING {lanes} (the session state folder, octo-feather-state); mkdir -p {lanes}"); bad = 1
    elif not os.access(lanes, os.W_OK): print(f"state  NOT WRITABLE {lanes} (the session state folder, octo-feather-state); sudo chown -R $(id -un) {st}"); bad = 1
    else: print(f"state  ok  {st} (octo-feather-state)")
    sys.path.insert(0, os.path.join(root, "scripts"))  # its own imports (handoff_log), as when it runs
    import octo_feather_lane as lane  # octo-feather-lane is its launcher
    kit, src = str(lane.kit_install()), "OCTO_FEATHER_KIT_INSTALL" if os.environ.get("OCTO_FEATHER_KIT_INSTALL") else "the kit dir"
    def git(*a): return run("git", "-C", kit, *a)
    url = run("git", "-C", root, "config", "--get", "remote.origin.url")[1] or "<kit url>"
    why = f"({src}; octo-feather-lane post-merge step 3 fast-forwards it)"
    if not os.path.exists(os.path.join(kit, ".git")):
        print(f"kit    NOT A CLONE {kit} {why}; git clone {url} {kit}, or set OCTO_FEATHER_KIT_INSTALL to the install clone"); bad = 1
    elif not git("config", "--get", "remote.origin.url")[1]:
        print(f"kit    NO ORIGIN {kit} {why}; git -C {kit} remote add origin {url}"); bad = 1
    else:
        branch = git("symbolic-ref", "-q", "--short", "HEAD")[1]
        on_main = branch == "main" or (not branch and any(not git("merge-base", "--is-ancestor", "HEAD", r)[0] for r in ("refs/remotes/origin/main", "refs/heads/main")))
        if on_main: print(f"kit    ok  {kit} on main ({src})")
        else:
            at = f"branch {branch}" if branch else "a detached HEAD off main"
            back = "switch main" if os.path.isdir(os.path.join(kit, ".git")) else "switch --detach origin/main"  # a worktree: main is checked out in the main checkout
            print(f"kit    NOT ON MAIN {kit} is on {at} {why}; live install clones stay on main (work in a git worktree): git -C {kit} {back}"); bad = 1
    sys.exit(bad)' "$root" || bad=1
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
    # Only the target's own tools count (octo-feather-mise-install --list, #493 AC3): the user's are never MISSING here.
    python3 -c 'import json, os, shutil, subprocess, sys
    root, top, locked = sys.argv[1], sys.argv[2], sys.argv[3]
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
        else: print(f"{tool:<6} WRONG VERSION {path or tool} reports {got}, want {want} (kit mise.lock); the kit runs it in every target: put {tool} {want} first on PATH (the kit mise install: {locked.replace("DIR", root)}, then {shims} first), or install {tool} {want}"); bad = 1
    for d in [os.path.realpath(top)]:
        if not os.path.isfile(os.path.join(d, "mise.toml")): continue
        fix = locked.replace("DIR", d)
        r = subprocess.run(["mise", "-C", d, "ls", "--local", "--json"], capture_output=True, text=True)
        if r.returncode:
            print(f"mise   {d}/mise.toml UNREADABLE: {r.stderr.strip()} (a [tools]-only mise.toml needs no trust; review it, then mise trust {d}/mise.toml)"); bad = 1; continue
        own = subprocess.run([os.path.join(root, "scripts", "octo-feather-mise-install"), "--list", d], capture_output=True, text=True).stdout.split()
        for tool, rows in json.loads(r.stdout or "{}").items():
            row = rows[0] if rows else {}
            if tool not in own: continue
            have, want = row.get("version"), row.get("requested_version")
            if row.get("installed"): print(f"mise   {tool} {have} ok ({d}/mise.lock)")
            else: print(f"mise   {tool} {want} MISSING ({d}/mise.lock); {fix}"); bad = 1
    sys.exit(bad)' "$root" "$(git -C "$1" rev-parse --show-toplevel 2>/dev/null || echo "$1")" "$(locked DIR)" || bad=1
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
    # The cache folder the qc sandbox masks (a tmpfs over it): a browser under it is unreadable there. One rule for both
    # browsers (spec remote#host-tools): agent-browser's own, here, and the qc one below.
    cache="${XDG_CACHE_HOME:-$HOME/.cache}"
    under_cache() { [[ "$1/" == "$cache/"* ]]; }
    # agent-browser's own browser (#422 item 7), the Chrome `agent-browser doctor --offline` names. `agent-browser install`
    # puts Chrome for Testing in ~/.agent-browser/browsers, which it searches before Playwright's cache in ~/.cache.
    if command -v agent-browser >/dev/null; then
      chrome="$(agent-browser doctor --offline --quick --json 2>/dev/null | python3 -c 'import json, re, sys
    try: c = next(c for c in json.load(sys.stdin)["checks"] if c.get("id") == "chrome.installed")
    except (ValueError, KeyError, TypeError, StopIteration): sys.exit(0)
    m = re.search(r" at (/.*)$", c.get("message", ""))
    print(m[1] if c.get("status") == "pass" and m else "")')"
      how="agent-browser install (Chrome for Testing into $HOME/.agent-browser/browsers, which agent-browser searches first; drop any AGENT_BROWSER_EXECUTABLE_PATH, or executablePath in ~/.agent-browser/config.json, naming another)"
      if [[ -z "$chrome" ]]; then printf 'agent-browser browser MISSING (agent-browser doctor --offline names no Chrome); %s\n' "$how"; bad=1
      elif under_cache "$chrome"; then printf 'agent-browser browser UNREADABLE IN THE QC SANDBOX %s is under %s, which the sandbox masks; %s\n' "$chrome" "$cache" "$how"; bad=1
      else printf 'agent-browser browser ok  %s (outside %s)\n' "$chrome" "$cache"; fi
    fi
    # ffmpeg (#422 item 9): only agent-browser's video recording needs it, so it never fails the check.
    if p="$(command -v ffmpeg)"; then printf 'ffmpeg ok  %s (optional: agent-browser video recording)\n' "$p"
    else echo "ffmpeg OPTIONAL not installed; only agent-browser video recording needs it, the check passes; to record video: sudo apt install ffmpeg"; fi
    # The PATHs the kit runs tools from (#422 item 2: older launchers earlier on PATH ran instead of the pinned mise,
    # node, pnpm, uv): this recipe's own PATH (the justfile's caller_path rule) and the PATH pi-role gives a pane
    # started from the caller's PATH (its with_mise rule, asked of pi-role itself). For each pinned tool, its first hit
    # on both is the pinned one (ok, its path), else that launcher is named with the pinned path and the fix. One only
    # the caller's own PATH finds first (a shell started before mise's shims went first) is a NOTE: the kit is
    # unaffected, the exit unchanged (the director's pane, #422). Pinned: mise, pi, agent-browser and just (when the target pins no just) by version, the
    # first hit reporting the pin (none on PATH at the pin: the version lines above name the install); every executable
    # of the target mise.toml tools by path, mise's shim or `mise bin-paths` install (a shim when there is one); the
    # target's own tools only (octo-feather-mise-install --list), never the user's global ones (#493 AC4). The recipe PATH comes as an
    # argument: a python3 that is a mise shim runs this with the whole mise toolset put first on its own PATH.
    python3 -c 'import functools, importlib.machinery as im, importlib.util as iu, json, os, re, subprocess, sys
    root, top, caller = sys.argv[1], os.path.realpath(sys.argv[2]), sys.argv[3]
    recipe = sys.argv[4]
    s = iu.spec_from_loader("pi_role", im.SourceFileLoader("pi_role", root + "/scripts/pi-role")); pr = iu.module_from_spec(s); s.loader.exec_module(pr)
    os.chdir(top); os.environ["PATH"] = caller
    pane = pr.mise_path() or caller  # what pi-role puts on a pane started from the caller here
    os.environ["PATH"] = recipe
    def run(*a):
        try: return subprocess.run(a, capture_output=True, text=True, timeout=20, cwd=top, stdin=subprocess.DEVNULL).stdout
        except (OSError, subprocess.SubprocessError): return ""
    def hits(name, path=recipe):
        fs = [os.path.join(d, name) for d in path.split(":") if os.path.isabs(d)]
        return list(dict.fromkeys(f for f in fs if os.path.isfile(f) and os.access(f, os.X_OK)))
    @functools.cache
    def version(f):
        m = re.search(r"[0-9]+\.[0-9]+\.[0-9]+", run(f, "--version"))
        return m.group(0) if m else None
    bad = 0
    def line(name, judge, why):
        # judge(path): (first hit, ok, pinned) on that PATH, or None when it decides nothing there
        global bad
        kit = [v for v in (judge(recipe), judge(pane)) if v]
        if not kit: return
        first, ok, pinned = next((v for v in kit if not v[1]), kit[0])
        if not ok:
            print(f"path   {name} SHADOWED {first} comes first on PATH, before the pinned {pinned} ({why}); remove or rename {first}, or put {os.path.dirname(pinned)} first on PATH"); bad = 1; return
        print(f"path   {name} ok  {first} ({why})")
        c = judge(caller)
        if c and not c[1]: print(f"path   {name} NOTE {c[0]} comes first on your shell PATH, before the pinned {c[2]} ({why}); the kit is unaffected: its recipes (justfile) and panes (pi-role) put mise first and run {first}; to run the pinned one in this shell too, put {os.path.dirname(c[2])} first on PATH")
    def js(*a):
        try: return json.loads(run(*a) or "{}")
        except ValueError: return {}
    pin = {n: open(os.path.join(root, n + "-version")).read().strip() for n in ("mise", "pi", "agent-browser")}
    mise = next((h for h in hits("mise") if version(h) == pin["mise"]), "mise")  # a stale mise first answers nothing useful
    shims = js(mise, "doctor", "--json").get("dirs", {}).get("shims", "")
    bins = {}  # executable name: its pinned path, for the target mise.toml tools; pi and agent-browser that npm put in
    # the node bin dir of mise (their fix lines, #463) keep their own version pins
    own = run(os.path.join(root, "scripts", "octo-feather-mise-install"), "--list", top).split()
    if os.path.isfile(os.path.join(top, "mise.toml")) and own:
        for b in run(mise, "-C", top, "bin-paths", *own).split("\n"):
            for n in sorted(os.listdir(b)) if b and os.path.isdir(b) else []:
                f = os.path.join(b, n)
                if n not in pin and os.path.isfile(f) and os.access(f, os.X_OK): bins.setdefault(n, f)
    kit = js(mise, "-C", root, "ls", "--local", "--json")
    pins = [(n, pin[n], f"{n}-version") for n in pin] + [("just", (kit.get("just") or [{}])[0].get("version"), "kit mise.lock")]
    def by_version(name, want):
        def judge(path):
            hs = hits(name, path)
            pinned = next((h for h in hs if version(h) == want), None)
            return (hs[0], hs[0] == pinned, pinned) if pinned else None
        return judge
    def by_bin(name, f):
        shim = os.path.join(shims, name) if shims else ""
        pinned = shim if shim and os.path.isfile(shim) else f
        def judge(path):
            if not (hs := hits(name, path)): return None
            return hs[0], os.path.dirname(hs[0]) == shims or os.path.realpath(hs[0]) in (os.path.realpath(f), os.path.realpath(pinned)), pinned
        return judge
    for name, want, why in pins:
        if name not in bins: line(name, by_version(name, want), why)
    for name, f in sorted(bins.items()):
        line(name, by_bin(name, f), f"{top}/mise.lock")
    sys.exit(bad)' "$root" "$(git -C "$1" rev-parse --show-toplevel 2>/dev/null || echo "$1")" "$2" "$PATH" || bad=1
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
      folder="${XDG_DATA_HOME:-$HOME/.local/share}/octo-feather/ms-playwright/$bpin"
      shell="$(ls -d "$folder"/chromium_headless_shell-*/INSTALLATION_COMPLETE 2>/dev/null | head -1)"
      if under_cache "$folder"; then
        printf 'browser UNREADABLE IN THE QC SANDBOX %s is under %s, which the sandbox masks; set XDG_DATA_HOME outside it\n' "$folder" "$cache"; bad=1
      elif [[ -n "$shell" ]]; then printf 'browser ok  %s (Playwright %s; PLAYWRIGHT_BROWSERS_PATH=%s)\n' "${shell%/INSTALLATION_COMPLETE}" "$bpin" "$folder"
      else printf 'browser MISSING (want Playwright %s headless Chromium shell in %s); install: PLAYWRIGHT_BROWSERS_PATH=%s npx -y playwright@%s install --only-shell chromium\n' "$bpin" "$folder" "$folder" "$bpin"; bad=1; fi
    fi
    # exe.dev Private sharing, the one step no command inside the box can check (spec remote#review-proxy,
    # #review-never-public): the VM name is this box's on exe.dev (<vm>.exe.xyz), else <vm>.
    vm="$(timeout 5 hostname -f 2>/dev/null)"; [[ "$vm" == *.exe.xyz ]] && vm="${vm%.exe.xyz}" || vm="<vm>"
    # Spec Chat's review service (spec remote#review-service, #review-setup): the systemd user unit its installer writes,
    # running and enabled (up at boot); else the installer run box setup makes, from the clone new-repo links.
    unit=spec-chat-review.service
    how="${SPEC_CHAT_CLONE:-$HOME/src/spec-chat}/scripts/install-spec-chat --review $root/docs/specs/index.spec.html --public $vm.exe.xyz --service (remote#review-setup)"
    python3 -c 'import shutil, subprocess, sys
    unit, how = sys.argv[1], sys.argv[2]
    if not shutil.which("systemctl"): print(f"review MISSING no systemctl: the review service runs as a systemd user service ({unit}); on a systemd box: {how}"); sys.exit(1)
    try: out = subprocess.run(["systemctl", "--user", "show", "-p", "ActiveState", "-p", "UnitFileState", unit], capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL).stdout
    except (OSError, subprocess.SubprocessError): out = ""
    st = dict(line.partition("=")[::2] for line in out.splitlines())
    active, file = st.get("ActiveState") or "unknown", st.get("UnitFileState") or "not installed"
    if (active, file) == ("active", "enabled"): print(f"review ok  {unit} active, enabled (Spec Chat\x27s review service, systemd --user)")
    else: print(f"review NOT RUNNING {unit} is {active}, {file} (want active, enabled: the systemd user service box setup installs); {how}"); sys.exit(1)' "$unit" "$how" || bad=1
    # The model check makes a model call per role model, so it is a setup step of its own (spec remote#host-models).
    echo "models MANUAL not checked here (no model call); at box setup and after a model key change: just install-check-models"
    echo "sharing MANUAL exe.dev Private sharing cannot be checked from inside the box; on the exe.dev VM that hosts reviews, from your own machine: ssh exe.dev share set-private $vm (never share set-public: a public share has no login)"
    exit "$bad"

# Box setup, never in install-check or the gate (spec remote#host-models): one short call through Pi to each model a
# role file names (pi-role --json reads the frontmatter), no tools, no skills, no session, and one classify call to the
# kit's judgment model (octo-feather-qa reads evals/judgment-model.json; its bench extension makes the call, outside
# the qc sandbox); each model ok, its key REJECTED or the proxy UNREACHABLE, with its users and the fix. Pi reads the
# key from its own provider config or environment: the key never goes on a command line and no line prints it (an
# error body that may echo it is dropped).
install-check-models:
    #!/usr/bin/env bash
    set -uo pipefail
    python3 -c 'import concurrent.futures as cf, glob, importlib.machinery as im, importlib.util as iu, json, os, re, shutil, subprocess, sys, tempfile
    root = sys.argv[1]
    limit = 120  # seconds per call: Pi retries a connection error 3 times (2, 4, 8 s) before it gives up
    pi = shutil.which("pi")
    if not pi: sys.exit("models MISSING pi on PATH; just install-check names its install, then rerun just install-check-models")
    bad, roles = 0, {}
    for f in sorted(glob.glob(os.path.join(root, "agents", "*.md"))):
        role = os.path.basename(f)[:-3]
        r = subprocess.run([os.path.join(root, "scripts", "pi-role"), "--json", f], capture_output=True, text=True, cwd=root, stdin=subprocess.DEVNULL)
        try: args = json.loads(r.stdout)["args"]
        except (ValueError, KeyError, TypeError):
            print(f"model  {role} UNREADABLE pi-role --json {f} failed: {(r.stderr.strip().splitlines() or ["no output"])[-1]}; fix the role file (scripts/check-roles names the problem)"); bad = 1; continue
        if "--model" in args: roles.setdefault(args[args.index("--model") + 1], []).append(role)
    s = iu.spec_from_loader("qa", im.SourceFileLoader("qa", os.path.join(root, "scripts", "octo-feather-qa"))); qa = iu.module_from_spec(s); s.loader.exec_module(qa)
    judge = None
    try: judge = qa.judgment_model(os.path.join(root, "evals"))
    except (OSError, ValueError, KeyError, TypeError) as e: print(f"model  judgment UNREADABLE evals/judgment-model.json ({e}); record the kit judgment model there (shape: scripts/check-evals --help)"); bad = 1
    agent = os.environ.get("PI_CODING_AGENT_DIR") or os.path.expanduser("~/.pi/agent")
    cfg, auth = os.path.join(agent, "models.json"), os.path.join(agent, "auth.json")
    def load(f, k=None):
        try: d = json.load(open(f)); d = d.get(k, {}) if k else d
        except (OSError, ValueError, AttributeError): return {}
        return d if isinstance(d, dict) else {}
    providers, stored = load(cfg, "providers"), load(auth)
    print(f"models pi {pi} (one short call per role model and the judgment model, no tools; Pi reads each key from {cfg}, {auth} or its environment)")
    def plain(s): return re.sub(r"[A-Za-z0-9_.~+/=-]{20,}", "<redacted>", s.split("{")[0]).strip(" :")[:160] or "no message"
    def run(cmd, cwd):
        try: return subprocess.run(cmd, capture_output=True, text=True, timeout=limit, cwd=cwd, stdin=subprocess.DEVNULL, env=dict(os.environ, PI_OFFLINE="1")), None
        except subprocess.TimeoutExpired: return None, ("UNREACHABLE", f"no answer in {limit} s", 0.0)
        except OSError as e: return None, ("FAILED", plain(str(e)), 0.0)
    def failed(r): return "FAILED", plain((r.stderr.strip().splitlines() or [f"pi exit {r.returncode}, no answer"])[-1]), 0.0
    def verdict(err, cost):
        head = plain(str(err or ""))
        code = (re.search(r"\b([45][0-9][0-9])\b", head) or [None, ""])[1]
        if code in ("401", "403") or re.search(r"(?i)unauthori[sz]ed|forbidden|authenticat|invalid.{0,20}(api.?key|token)", head): return "REJECTED", head, cost
        if code in ("502", "503", "504") or re.search(r"(?i)connect|timed? ?out|ECONN|ENOTFOUND|EAI_AGAIN|fetch failed|socket|network|getaddrinfo|terminated", head): return "UNREACHABLE", head, cost
        return "FAILED", head, cost
    def probe(model):
        cmd = [pi, "-p", "--mode", "json", "--no-session", "--no-tools", "--no-skills", "--no-context-files", "--no-prompt-templates", "--no-mcp", "--thinking", "off", "--model", model, "Reply with the one word ok."]
        with tempfile.TemporaryDirectory() as cwd: r, done = run(cmd, cwd)
        if done: return done
        last = None
        for line in r.stdout.splitlines():
            try: ev = json.loads(line)
            except ValueError: continue
            msg = ev.get("message") if isinstance(ev, dict) and ev.get("type") == "message_end" else None
            if isinstance(msg, dict) and msg.get("role") == "assistant": last = msg
        if r.returncode or last is None: return failed(r)
        cost = float(((last.get("usage") or {}).get("cost") or {}).get("total") or 0)
        return ("ok", "answered", cost) if last.get("stopReason") != "error" else verdict(last.get("errorMessage"), cost)
    def classify(model):
        # One case, one yes/no question: the bench extension octo-feather-qa runs, its flags, its output reader.
        inp = {"question": "Is this text a greeting?", "labels": ["yes", "no"], "criteria": {"yes": "a greeting", "no": "anything else"}, "cases": [{"id": "probe", "state": "hello"}], "classifiers": [model]}
        with tempfile.TemporaryDirectory() as cwd:
            open(os.path.join(cwd, qa.BENCH_INPUT), "w").write(json.dumps(inp))
            open(os.path.join(cwd, qa.BENCH_EXT), "w").write(qa.BENCH_SOURCE % {"command": qa.BENCH_COMMAND})
            r, done = run([pi, "--no-session", "--no-skills", "--no-mcp", "--no-context-files", "--no-prompt-templates", "--no-extensions", "--no-tools", "-e", os.path.join(cwd, qa.BENCH_EXT), "-p", f"/{qa.BENCH_COMMAND} {os.path.join(cwd, qa.BENCH_INPUT)}"], cwd)
        if done: return done
        bench, _ = qa.bench_output(r.stdout)
        if bench is None: return failed(r)
        cost = sum(float(c.get("cost_usd") or 0) for c in bench.get("calls") or [])
        if model not in (bench.get("benched") or []): return "FAILED", f"Pi lists no classifier {model}: no key for its provider, or not in Pi catalog", cost
        rows = bench.get("rows") or [[None] * 6]
        ei = rows[0][5]
        return ("ok", "answered", cost) if ei is None and rows[0][2] else verdict((bench.get("errors") or ["no answer"])[ei or 0], cost)
    users = {m: "roles " + ", ".join(rs) for m, rs in roles.items()}
    jobs = [(m, probe) for m in roles]
    if judge:
        users[judge] = ("roles " + ", ".join(roles[judge]) + "; " if judge in roles else "") + "judgment model (evals/judgment-model.json): the advisory judge, judgment benches"
        jobs.append((judge, classify))
    with cf.ThreadPoolExecutor(max_workers=4) as ex: results = list(zip([m for m, _ in jobs], ex.map(lambda j: j[1](j[0]), jobs)))
    spend = 0.0
    for model, (got, why, cost) in results:
        spend += cost
        who = users[model]
        prov = model.split("/")[0]
        p = providers.get(prov) if isinstance(providers.get(prov), dict) else {}
        a = stored.get(prov) if isinstance(stored.get(prov), dict) else {}
        key, where = (p["apiKey"], f"{cfg} (providers.{prov}.apiKey)") if "apiKey" in p else (a.get("key"), f"{auth} ({prov}.key)") if a.get("type") == "api_key" else (None, f"{cfg} (providers.{prov}.apiKey), {auth}")
        if got == "ok": print(f"model  {model} ok ({who})"); continue
        bad = 1
        if got == "REJECTED":
            junk = " (the key there ends in or holds whitespace or terminal characters)" if isinstance(key, str) and re.search(r"\s|[\x00-\x1f\x7f]|\[20[01]~", key) else ""
            print(f"model  {model} REJECTED key ({why}) for {who}{junk}; put the key the model proxy issued for provider {prov} in {where} or its environment, exactly, no trailing characters, then rerun just install-check-models")
        elif got == "UNREACHABLE":
            url = p.get("baseUrl")
            base = f"{url} ({cfg}, providers.{prov}.baseUrl)" if url else f"the endpoint Pi has built in for {prov}"
            print(f"model  {model} UNREACHABLE ({why}) for {who}; the model proxy for provider {prov} did not answer: check this box reaches {base} and the proxy is up, then rerun just install-check-models")
        else: print(f"model  {model} FAILED ({why}) for {who}; run pi --model {model} -p ok by hand for the full error Pi gives, then rerun just install-check-models")
    print(f"models spend {spend:.4f} USD ({len(results)} calls, Pi usage cost)")
    sys.exit(bad)' "$root"

# Start the director in Herdr workspace `director` (docs/adr/0011).
start cwd=invocation_directory():
    octo-feather-start --director --cwd "$1"

# Start one supervisor for a ticket as the tracker writes it (12, ENG-123) in workspace named by its lane key (gh12, eng-123), tab `supervisor`.
supervise issue cwd=invocation_directory():
    octo-feather-start --issue "$1" --cwd "$2"

# Product QC (docs/adr/0022, octo-feather-qc): each claimed criterion its qc.toml declares a demo for is captured and decided by the demo's checks; the rest a fresh cross-family judge; passed ones become built. Never inside `just check`.
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
