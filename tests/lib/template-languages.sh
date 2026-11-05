# shellcheck shell=bash
# Sourced by tests/template-languages.sh (the Python repo) and tests/template-languages-typescript.sh (one gate item per
# template, #509), never run itself: in tests/lib/ so the gate's tests/*.sh glob does not collect it. Gives each item
# its own throwaway dir ($t, the trust store under it), the recording Python and uv stubs ($t/nopy), and
# check_template LANG: the repo `just new-repo LANG DEST --no-spec-chat` makes, green fresh, then each rule broken once;
# check_tiers and check_acceptance below.
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
  # ShellCheck's recipe out of the gate (GATE_RECIPES in each repo).
  sed -i -e 's/^export GATE_RECIPES := "check-languages check-scripts /export GATE_RECIPES := "check-languages /' "$d/justfile"
  g "$d" add -A
  check; [[ "$rc" != 0 ]] || fail "$lang: shellcheck's recipe out of the gate passed"
  s="shellcheck gates BASH, but its recipe check-scripts is not in the gate"
  grep -qxF -- "check-languages: $s" <<<"$out" || fail "$lang: output lacks: $s"
}

# check_tiers LANG: the created repo's two gate tiers (templates spec #acceptance-fresh-fast, #acceptance-test-kinds,
# #acceptance-shared-fixture), after check_template, with a second module and its integration test committed. The
# full tier's tests show each kind, integration and e2e, and the shared fixture prepared once with two workers; then
# just fast after a one-file change names only that module's test, and after a justfile change (on its
# shared-machinery.txt) every integration test; neither shows an e2e test. The Python repo's static checks cut to one
# with just's own command line (--set GATE_RECIPES); the TypeScript repo's run in full (just check is one Vitest run
# holding them, tests/gate.test.ts; fast runs check-static first).
check_tiers() {
  local lang="$1" other other_t full fast integ e2e
  g "$d" reset -q --hard; g "$d" clean -qfd -e node_modules -e .venv
  if [[ "$lang" == python ]]; then
    other=src/app/other.py
    printf 'def double(n: int) -> int:\n    return n * 2\n' >"$d/$other"
    printf 'from app.other import double\n\n\ndef test_double() -> None:\n    assert double(2) == 4\n' >"$d/tests/integration/test_other.py"
    # Two workers: the shared fixture across xdist workers (a nested gate is otherwise -n 0, #208; two tiny tests).
    full=(env -u GATE_NESTED GATE_WORKERS=2 just --set GATE_RECIPES check-lint check)
    fast=(just --set GATE_RECIPES check-lint fast)
    other_t="PASSED tests/integration/test_other.py::test_double"; integ="PASSED tests/integration/test_cli.py::"
    e2e="tests/e2e/test_cli_e2e.py::test_installed_command_end_to_end"
  else
    other=src/other.ts
    printf 'export function double(n: number): number {\n  return n * 2;\n}\n' >"$d/$other"
    printf 'import { expect, it } from "vitest";\nimport { double } from "../src/other.ts";\n\nit("doubles", () => {\n  expect(double(2)).toBe(4);\n});\n' >"$d/tests/other.test.ts"
    full=(just check); fast=(just fast)
    other_t="✓ |integration| tests/other.test.ts > doubles"; integ="✓ |integration| tests/cli.test.ts > "
    e2e="|e2e| tests/cli.e2e.test.ts"
  fi
  g "$d" add -A; g "$d" commit -qm other
  # The TypeScript repo's tiers with the recording Python stubs first on PATH, as its check above.
  local path="$PATH"; [[ "$lang" == python ]] || path="$t/nopy:$PATH"
  tier() { set +e; out="$(cd "$d" && PATH="$path" "$@" 2>&1)"; rc=$?; set -e; [[ "$rc" == 0 ]] || fail "$lang: $* exited $rc: $out"; }
  tier "${full[@]}"
  [[ "$out" == *"$integ"* && "$out" == *"$other_t"* && "$out" == *"$e2e"* ]] || fail "$lang: just check does not show its integration and e2e tests by kind"
  [[ "$(grep -c "shared fixture greetings.json: prepared once" <<<"$out")" == 1 ]] || fail "$lang: just check did not show the shared fixture prepared exactly once"
  sed -i 's/n \* 2/n + n/' "$d/$other"
  tier "${fast[@]}"
  [[ "$out" == *"$other_t"* && "$out" != *"$integ"* && "$out" != *"$e2e"* ]] || fail "$lang: just fast after a one-file change ($other) did not run exactly its test"
  g "$d" checkout -q -- "$other"; printf '# changed\n' >>"$d/justfile"
  tier "${fast[@]}"
  [[ "$out" == *"fast: every integration test: justfile changed since main, on shared-machinery.txt"* && "$out" == *"$other_t"* \
    && "$out" == *"$integ"* && "$out" != *"$e2e"* ]] || fail "$lang: just fast after a justfile change did not run every integration test, and only those"
}

# check_acceptance LANG: the created repo's starter criterion proven by its tagged acceptance test (templates spec
# #acceptance-starter-acceptance-test), after check_tiers, the repo reset to its commits and its status file made. A
# claims run narrowed, or naming no criterion, is refused before any test runs; the full gate told the claim
# (OCTO_FEATHER_QC_CLAIMS) stores one record naming the tagged case passed; `just qc` on the starter criterion judges
# it PASS from that record, reruns nothing (no new record, no demo, no judge) and builds it naming the test. Fake
# Herdr and the kit's stub classifier pi (tests/fixtures/classify-stub/pi): no model. A test harness, as tests/qc.sh:
# the kit gate's check-run marker unset, so just qc runs. The qc sandbox needs Linux.
check_acceptance() {
  local lang="$1" cid=app#acceptance-hello-json test narrow h rec
  if [[ "$(uname -s)" == Darwin ]]; then echo "$lang: starter acceptance skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; return; fi
  if [[ "$lang" == python ]]; then test=tests/e2e/test_cli_e2e.py; narrow=(just check-tests tests/e2e)
  else test=tests/cli.e2e.test.ts; narrow=(just check-tests --project e2e); fi
  g "$d" reset -q --hard; g "$d" clean -qfd -e node_modules -e .venv
  mkdir -p "$t/acc/bin" "$t/acc/stub"; ln -sf "$kit/tests/fixtures/classify-stub/pi" "$t/acc/stub/pi"
  cat >"$t/acc/bin/herdr" <<'EOF'
#!/usr/bin/env bash
C="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"; s=default; a=()
while (($#)); do case "$1" in --session) s="$2"; shift 2;; --remote|--machine) shift 2;; *) a+=("$1"); shift;; esac; done
[[ "$s" == default ]] && sock="$C/herdr.sock" || sock="$C/sessions/$s/herdr.sock"
case "${a[*]}" in
  server) mkdir -p "${sock%/*}"; echo "$s" > "$sock"; exec sleep 600;;
  "session stop "*) rm -f "$C/sessions/${a[2]}/herdr.sock"; exit 0;;
  "session delete "*) rm -rf "${C:?}/sessions/${a[2]}"; exit 0;;
  "pane list") exit 0;;
esac
[[ -f "$sock" ]] || { echo server_not_running >&2; exit 1; }
echo "{\"session\":\"$(cat "$sock")\"}"
EOF
  chmod +x "$t/acc/bin/herdr"
  acc() { set +e; out="$(cd "$d" && env -u OCTO_FEATHER_CHECK_RUN -u HERDR_SESSION -u HERDR_SOCKET_PATH -u HERDR_ENV XDG_STATE_HOME="$t/acc/state-$lang" \
    OCTO_FEATHER_QC_PATH="$t/acc/stub" PATH="$t/acc/bin:$kit/scripts:$PATH" "$@" 2>&1)"; rc=$?; set -e; }
  records() { acc octo-feather-evidence read --repo . --json; python3 -c 'import json,sys; print(len(json.loads(sys.argv[1])))' "$out"; }
  acc octo-feather-spec-status init docs/specs/app.spec.html "$(g "$d" rev-parse --short HEAD)"; [[ "$rc" == 0 ]] || fail "$lang: status init"
  g "$d" add -A; g "$d" commit -qm status; h="$(g "$d" rev-parse HEAD)"
  acc env OCTO_FEATHER_QC_CLAIMS="$cid" "${narrow[@]}"
  [[ "$rc" != 0 && "$out" == *"OCTO_FEATHER_QC_CLAIMS needs the full gate"*"nothing ran"* && "$out" != *"Hello, Grace"* ]] \
    || fail "$lang: a narrowed claims run (${narrow[*]}) was not refused before any test: exit $rc"
  acc env OCTO_FEATHER_QC_CLAIMS="app#acceptance-nope" just check
  [[ "$rc" != 0 && "$out" == *"app#acceptance-nope names no criterion"* && "$out" != *"Hello, Grace"* ]] \
    || fail "$lang: a claim naming no criterion was not refused before any test: exit $rc"
  [[ "$(records)" == 0 ]] || fail "$lang: a refused claims run stored a record"
  acc env OCTO_FEATHER_QC_CLAIMS="$cid" just check
  rec="$(sed -nE "s|^qc capture: $cid: record ([0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}), 1 case\(s\): $test passed\$|\1|p" <<<"$out")"
  [[ "$rc" == 0 && -n "$rec" ]] || fail "$lang: the claims gate: want exit 0 and one record naming $test passed, got $rc"
  acc just qc docs/specs/app.status.json 7 acceptance-hello-json
  [[ "$rc" == 0 ]] && grep -A2 '^PASS acceptance-hello-json: ' <<<"$out" | grep -qx "  evidence complete; decision tagged test assertions; record $rec" \
    && grep -qF "qc: tagged test $cid: judged from the gate's record $rec at ${h:0:12}, not rerun" <<<"$out" \
    && ! grep -q '^qc: demo \|agent fallback' <<<"$out" || fail "$lang: just qc did not judge the starter criterion PASS from record $rec"
  [[ "$(records)" == 1 ]] || fail "$lang: just qc reran something: $(records) records"
  python3 -c 'import json,sys; c=json.loads(sys.argv[1])["criteria"]["acceptance-hello-json"]; sys.exit(c != {"status": "built", "pr": 7, "record": sys.argv[2], "commit": sys.argv[3], "tests": [sys.argv[4]]})' \
    "$(g "$d" show HEAD:docs/specs/app.status.json)" "$rec" "$h" "$test" || fail "$lang: status: $(g "$d" show HEAD:docs/specs/app.status.json)"
}
