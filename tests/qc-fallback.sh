#!/usr/bin/env bash
# gate: e2e
# criterion: quality#acceptance-qc-fallback
# Integration test for a claimed criterion with neither a tagged acceptance test nor a declared demo (quality spec
# #qc-fallback, #acceptance-qc-fallback, ADR 0035), through `just qc` with a fake herdr and a tripwire pi (no model): a
# scratch target whose qc.toml declares a demo for acceptance-a only. acceptance-b alone: INSUFFICIENT EVIDENCE naming
# that it has neither, no record, no sandbox and no pi or judge started, no `fallback` report key, exit 2, still planned
# and the head unchanged. Mixed (acceptance-a's demo beside it): the demo's pass, acceptance-b the same insufficient
# evidence, exit 2, one status-only commit building acceptance-a alone.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN OCTO_FEATHER_QC_CLAIMS   # a test harness, as tests/qc.sh: qc refuses only under the gate's marker
[[ "$(uname -s)" != Darwin ]] || { echo "qc-fallback: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "qc-fallback test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME" "$TMPDIR" "$t/bin" "$t/stub" "$t/repo/docs/specs"
cat > "$t/bin/herdr" <<'EOF'
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
# The tripwire pi, first on PATH and on the sandbox's (never a model): each run outside a sandbox leaves its argv in
# $t/pi.log (inside one, the write dies with the overlay); it reaches no model, so the advisory is unavailable.
cat > "$t/stub/pi" <<EOF
#!/bin/sh
echo "pi \$*" >> "$t/pi.log" 2>/dev/null
echo "tripwire pi: no model here" >&2; exit 9
EOF
chmod +x "$t/bin/herdr" "$t/stub/pi"
export PATH="$t/stub:$t/bin:$kit/scripts:$PATH" OCTO_FEATHER_QC_PATH="$t/stub"

cd "$t/repo"; git init -q -b main .
git commit -qm accepted --allow-empty
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" docs/specs/
git add -A; git commit -qm spec
octo-feather-spec-status init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null
cat > qc.toml <<'EOF'
format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = "echo a ok"
covers = ["src/a"]
tests = ["tests/a.sh"]
EOF
git add -A; git commit -qm "contract: a demo for acceptance-a only"
head="$(git rev-parse HEAD)"
qcrun() { set +e; out="$(timeout -k 5 120 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 "$@" 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "qc hung: $(tail -20 "$t/err")"; }
neither() {   # $1 the run: acceptance-b's result in its stdout, its report's results and no judge's trace
  grep -A2 '^INSUFFICIENT EVIDENCE acceptance-b: ' <<< "$out" | grep -A1 '^  missing: no tagged acceptance test and no declared demo$' \
    | grep -qx '  evidence incomplete; decision none; record none' || fail "$1: acceptance-b not insufficient evidence naming neither: $out $(tail -20 "$t/err")"
  ! grep -q 'pi-role\|qc-judge\|agent fallback' "$t/err" || fail "$1: a judge was started: $(cat "$t/err")"
  rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"
  python3 - "$rep" "$head" <<'EOF' || fail "$1: report: $(cat "$rep")"
import json, sys
r = json.load(open(sys.argv[1]))
assert "fallback" not in r and "cap_s" not in r and "model" not in r, sorted(r)
b = next(x for x in r["results"] if x["id"] == "acceptance-b")
assert {k: b[k] for k in ("verdict", "evidence", "missing", "record", "head")} == {
    "verdict": "insufficient evidence", "evidence": "incomplete", "missing": ["no tagged acceptance test and no declared demo"],
    "record": None, "head": sys.argv[2]}, b
assert "advisory" not in b, b
EOF
  python3 -c 'import json, sys; c = json.load(open(sys.argv[1]))["criteria"]["acceptance-b"]; assert c == {"status": "planned", "pr": None}, c' \
    docs/specs/demo.status.json || fail "$1: acceptance-b not planned"
}

# Neither alone: nothing runs at all, no sandbox, no pi.
qcrun acceptance-b
[[ "$rc" == 2 ]] || fail "neither: want exit 2, got $rc: $out $(tail -20 "$t/err")"
neither neither
! grep -q 'qc sandbox' "$t/err" || fail "neither: a sandbox started: $(cat "$t/err")"
[[ ! -e "$t/pi.log" ]] || fail "neither: pi started: $(cat "$t/pi.log")"
[[ "$(git rev-parse HEAD)" == "$head" && -z "$(git status --porcelain)" ]] || fail "neither: head or status file changed"

# Mixed: acceptance-a's demo passes from its record, acceptance-b the same insufficient evidence.
qcrun acceptance-a acceptance-b
[[ "$rc" == 2 ]] || fail "mixed: want exit 2, got $rc: $out $(tail -20 "$t/err")"
grep -A2 '^PASS acceptance-a: \$ echo a ok$' <<< "$out" | grep -qE '^  evidence complete; decision demo checks; record [0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$' \
  || fail "mixed: want acceptance-a passed by its demo: $out $(tail -20 "$t/err")"
neither mixed
[[ "$(git log -1 --format=%s)" == "qc: built acceptance-a (judged ${head:0:12})" ]] || fail "mixed: status commit: $(git log -1 --format=%s)"
[[ "$(git diff --name-only "$head" HEAD)" == docs/specs/demo.status.json ]] || fail "mixed: the commit touched more than the status file"
echo "qc-fallback: ok (neither a tagged test nor a declared demo: insufficient evidence naming neither, no record, no sandbox, pi or judge, no fallback report key, exit 2, planned; mixed with a demo: the demo's pass beside it, exit 2, acceptance-a alone built)"
