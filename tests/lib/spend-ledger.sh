# shellcheck shell=bash disable=SC2034  # v, ledger, out, rc, gitenv: used by the scripts that source this file
# Sourced by each tests/spend-ledger-*.sh (one gate item per case group, #509), never run
# itself: in tests/lib/ so the gate's tests/*.sh glob does not collect it. Real Pi at the kit's pin (pi-version),
# headless, against a fake OpenAI-compatible provider on 127.0.0.1 whose model has a catalog price (input $1000/M
# tokens, output $2000/M), then `octo-feather-lane spend`. Credential-free: Pi starts from an empty environment with an
# empty HOME, its own PI_CODING_AGENT_DIR and its own state dir; it reads nothing of the box's ~/.pi or ledger. Each
# item has its own throwaway dir ($t), provider, ledger and repo, so items run in parallel (which pi the box's
# 10-Pi limit counts: docs/adr/0005). Gives pienv, run, row, spend, calls, gitenv, mk_qcrepo, qc and seed (the ledger
# as the earlier cases leave it).
set -euo pipefail
kit="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
pin="$(tr -d '[:space:]' < "$kit/pi-version")"
install="npm install -g --ignore-scripts @earendil-works/pi-coding-agent@$pin"
command -v pi >/dev/null || { echo "spend-ledger test: pi not on PATH; install Pi $pin: $install" >&2; exit 1; }
v="$(pi --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
[[ "$v" == "$pin" ]] || { echo "spend-ledger test: pi reports ${v:-no version}, the kit pins $pin (pi-version); $install" >&2; exit 1; }
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; srv=""
trap '[[ -z "$srv" ]] || kill "$srv" 2>/dev/null || true; rm -rf "$t"' EXIT
fail() { echo "spend-ledger test: $*" >&2; exit 1; }

# The fake provider (tests/gate/kit/testkit/provider.py, its header: what it answers).
mkdir -p "$t/home" "$t/agent" "$t/repo"
XDG_STATE_HOME="$t/state" "$kit/scripts/pi-role" --set-identity t t@t >/dev/null   # the commit identity a role launch needs (#665)
git -c init.defaultBranch=main init -q "$t/repo"
echo '{"retry":{"enabled":false}}' > "$t/agent/settings.json"
python3 "$kit/tests/gate/kit/testkit/provider.py" > "$t/port" & srv=$!
for _ in $(seq 50); do [[ -s "$t/port" ]] && break; sleep 0.1; done
[[ -s "$t/port" ]] || fail "fake provider did not start"
printf '{"providers":{"fake":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"x","models":[{"id":"fake","cost":{"input":1000,"output":2000,"cacheRead":0,"cacheWrite":0}},{"id":"free","cost":{"input":0,"output":0,"cacheRead":0,"cacheWrite":0}}]}}}\n' \
  "$(cat "$t/port")" > "$t/agent/models.json"

state="$t/state/octo-feather"; ledger="$state/spend.jsonl"
mkdir -p "$state/lanes"; printf 'supervisor = "w37:p2"\n' > "$state/lanes/gh149.toml"
# Pi's environment: nothing inherited but PATH and mise's data dir (as mise reports it here: the qc sandbox's
# installs, scripts/octo-feather-qc-sandbox 6b), plus the given variables.
mdata="$(mise doctor --json | jq -r .dirs.data)"
pienv() { env -i PATH="$PATH" MISE_DATA_DIR="$mdata" HOME="$t/home" TMPDIR="$t" XDG_CACHE_HOME="$t/cache" XDG_STATE_HOME="$t/state" \
  PI_CODING_AGENT_DIR="$t/agent" PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0 "$@"; }
# run PROMPT [VAR=VALUE...]: one headless pi with the extension; $out, $rc, stderr in $t/err.
run() {
  local prompt="$1"; shift
  set +e
  out="$(cd "$t/repo" && pienv "$@" pi -e "$kit/extensions/spend-ledger.ts" -e "$kit/tests/fixtures/spend-ledger/nested-tool.ts" \
    --model "${model:-fake/fake}" --no-session -p "$prompt" 2>"$t/err")"; rc=$?
  set -e
}
row() { # OUT TITLE KEY USD CALLS UNKNOWN IN OUT: the KEY row under "By TITLE:" (tests/spend-out)
  local r; r="$("$kit/tests/spend-out" row "${@:2}" <<<"$1")" || fail "$r in: $1"; }
spendcmd=(env -i PATH="$PATH" HOME="$t/home" XDG_STATE_HOME="$t/state" "$L" spend)
spend() { "${spendcmd[@]}"; }
# calls N: wait up to 10 s for `spend` to count N calls in all (the writer runs detached; tests/spend-out).
calls() { local r; r="$("$kit/tests/spend-out" calls "$1" -- "${spendcmd[@]}")" || fail "$r"; }
gitenv=(GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t)
# mk_qcrepo: $qcrepo, a repo holding the spec-status fixture spec and its status, and Pi's agent dir under HOME
# (kept in the qc sandbox).
mk_qcrepo() {
  qcrepo="$t/qcrepo"; mkdir -p "$qcrepo/docs/specs" "$t/home/.pi"; cp -r "$t/agent" "$t/home/.pi/agent"   # under HOME: kept in the sandbox
  cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$qcrepo/docs/specs/"
  (cd "$qcrepo" && git init -q -b main && git add -A && env "${gitenv[@]}" git commit -qm spec \
    && "$kit/scripts/octo-feather-spec-status" init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null \
    && git add -A && env "${gitenv[@]}" git commit -qm status)
}
# qc SPACE: one `just qc` of acceptance-a in $qcrepo (mk_qcrepo); $out, $rc, stderr in $t/err.
qc() { set +e
  out="$(cd "$qcrepo" && pienv HERDR_WORKSPACE_ID="$1" PI_CODING_AGENT_DIR="$t/home/.pi/agent" OCTO_FEATHER_QC_MODEL=fake/fake "${gitenv[@]}" \
    "$kit/scripts/octo-feather-qc" docs/specs/demo.status.json 5 acceptance-a 2>"$t/err")"; rc=$?
  set -e; }
# seed N: the ledger's first N records as the cases before leave it (each through `spend record`, the extension's
# writer): 8, tests/gate/kit/spend_ledger.py's cases agents to zero-priced (gh149 implementer: fake/fake 100 in 20 out $0.14,
# 150 in 10 out $0.17 three times, tool/nested_work 7 in 3 out $0.004, fake/free 150 in 10 out unknown cost; no lane:
# agent and code-reviewer, fake/fake 150 in 10 out $0.17 each); 10, then the qc case's (gh149 judge and qc-judge).
seed() {
  local m='"model":"fake/fake"' u='"input_tokens":150,"output_tokens":10,"cost_usd":0.17'
  printf '%s\n' "{$m,\"purpose\":\"implementer\",\"input_tokens\":100,\"output_tokens\":20,\"cost_usd\":0.14}" \
    "{$m,\"purpose\":\"implementer\",$u}" "{\"model\":\"tool/nested_work\",\"purpose\":\"implementer\",\"input_tokens\":7,\"output_tokens\":3,\"cost_usd\":0.004}" \
    "{$m,\"purpose\":\"implementer\",$u}" "{$m,\"purpose\":\"implementer\",$u}" \
    '{"model":"fake/free","purpose":"implementer","input_tokens":150,"output_tokens":10,"cost_usd":null}' |
    env -i PATH="$PATH" HOME="$t/home" XDG_STATE_HOME="$t/state" "$L" spend record --lane gh149
  printf '%s\n' "{$m,\"purpose\":\"agent\",$u}" "{$m,\"purpose\":\"code-reviewer\",$u}" |
    env -i PATH="$PATH" HOME="$t/home" XDG_STATE_HOME="$t/state" "$L" spend record
  if [[ "$1" == 10 ]]; then
    printf '%s\n' '{"model":"openrouter/typesafe/jev-1.13","purpose":"judge","input_tokens":500,"output_tokens":40,"cost_usd":0.0001}' \
      "{$m,\"purpose\":\"qc-judge\",$u}" | env -i PATH="$PATH" HOME="$t/home" XDG_STATE_HOME="$t/state" "$L" spend record --lane gh149
  fi
  calls "$1"
}
