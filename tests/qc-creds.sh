#!/usr/bin/env bash
# gate: e2e
# Integration test for who gets the owner's model credentials in `just qc` (owner ruling 2026-10-29, #438; docs/adr/0022,
# the sandbox paragraph), through `just qc` with a fake herdr and a fake pi at the model boundary, no model: a scratch
# target declares one demo that tries to read Pi's auth.json and models.json; a second criterion has none and goes to the
# agent fallback. The demo's sandbox holds neither file (its proof says so, its stored record shows both unreadable, no
# secret in it); the fallback judge and the advisory classify run each find both per-run copies, so they reach the model.
# The OAuth warning shows once for a run where a Pi got copies, never for a run whose sandboxes copied nothing.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc-capture.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN   # a test harness, as tests/qc.sh: qc refuses only under the gate's marker
[[ "$(uname -s)" != Darwin ]] || { echo "qc-creds: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "qc-creds test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR PI_CODING_AGENT_DIR
unset STUB_KIT STUB_WANT STUB_CONFIDENCE
export STUB_ANSWER=shows
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME/.pi/agent" "$TMPDIR" "$t/bin" "$t/repo/docs/specs"
# The owner's credentials: an OAuth entry (qc warns once its refresh would be discarded) and a provider key.
pa="$HOME/.pi/agent/auth.json" pm="$HOME/.pi/agent/models.json"
echo '{"anthropic": {"type": "oauth", "refresh": "SECRET-pi-oauth-r", "access": "SECRET-pi-oauth-a", "expires": 1}}' > "$pa"; chmod 600 "$pa"
echo '{"providers": {"p": {"apiKey": "SECRET-pi-models-0123456789"}}}' > "$pm"
cp -p "$pa" "$t/auth0"; cp -p "$pm" "$t/models0"
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
# Fake pi: a Pi that runs reaches the model only with both credential files. Without them it fails as a Pi
# with no model access would; with them the classify path (-e) goes to the stub classifier, the judge reports
# on its brief's one criterion, its why naming the credentials it found.
cat > "$t/bin/pi" <<EOF
#!/usr/bin/env bash
[[ "\${1:-}" == --version ]] && exit 0
for f in auth.json models.json; do grep -q SECRET-pi "\$HOME/.pi/agent/\$f" 2>/dev/null || { echo "fake pi: no \$f: no model access" >&2; exit 9; }; done
for a in "\$@"; do [[ "\$a" == -e ]] && exec "$kit/tests/fixtures/classify-stub/pi" "\$@"; done
b="\${*: -1}"; h="\$(grep -o 'head [0-9a-f]\{40\}' <<< "\$b" | head -1 | cut -d' ' -f2)"
printf '\`\`\`json\n{"head": "%s", "criteria": [{"id": "acceptance-b", "verdict": "pass", "command": "judge b", "output": "ok", "why": "model reached: auth.json and models.json copies"}]}\n\`\`\`\n' "\$h"
EOF
chmod +x "$t/bin/herdr" "$t/bin/pi"
export PATH="$t/bin:$kit/scripts:$PATH"
# The fake, never the box's pi, is the pi a recipe resolves (a real one would reach a model): checked before any run.
rp="$(cd "$t" && PATH="$(just --justfile "$kit/justfile" --evaluate PATH)" command -v pi)"
echo "qc-creds: recipe pi: $rp"
[[ "$rp" == "$t/bin/pi" ]] || fail "a recipe resolves pi to $rp, not the fake $t/bin/pi: nothing run"
M="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["model"])' "$kit/evals/judgment-model.json")"
ev="$kit/scripts/octo-feather-evidence"

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
command = 'for f in auth.json models.json; do cat "$HOME/.pi/agent/$f" && exit 1; done; echo neither readable'
covers = ["src/a"]
tests = ["tests/a.sh"]
EOF
git add -A; git commit -qm contract
head="$(git rev-parse HEAD)"
rid='[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}'
warn='qc: warning: auth.json has OAuth credentials: a token refresh during this run is discarded'
qcrun() { git reset -q --hard "$head"; set +e
  out="$(timeout -k 5 180 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 "$@" 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "qc hung: $(tail -20 "$t/err")"
  [[ "$rc" == "${want:-0}" ]] || fail "$*: want exit ${want:-0}, got $rc: $out $(tail -20 "$t/err")"
  rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"
  cmp -s "$pa" "$t/auth0" && cmp -s "$pm" "$t/models0" || fail "$*: box auth.json or models.json changed"; }
# demo ID: acceptance-a passed from its demo: its stored record says neither file was readable, no secret in it;
# its sandbox's proof states it holds no Pi model credentials.
demo() {
  a="$(grep -A2 '^PASS acceptance-a: ' <<< "$out" | sed -nE "s/^  evidence complete; decision demo checks; record ($rid)$/\1/p")"
  [[ -n "$a" ]] || fail "$1: want PASS acceptance-a from its demo: $out $(tail -20 "$t/err")"
  python3 - "$("$ev" read --repo . --commit "$head" --json)" "$a" "$rep" <<'EOF' || fail "$1: the demo read a credential: $(cat "$rep")"
import json, os, sys
rd, a, rep = sys.argv[1:]
x = [r for r in json.loads(rd) if r["record"]["id"] == a][0]
got = {n: open(os.path.join(x["dir"], "outputs", n)).read() for n in ("demo.exit", "demo.stdout", "demo.stderr")}
assert got["demo.exit"] == "0\n" and got["demo.stdout"] == "neither readable\n", got
assert all(f"/.pi/agent/{f}: No such file or directory" in got["demo.stderr"] for f in ("auth.json", "models.json")), got
for root, _, files in os.walk(x["dir"]):
    for f in files:
        assert b"SECRET-pi" not in open(os.path.join(root, f), "rb").read(), (root, f)
proof = json.load(open(rep))["captures"][0]["sandbox"]["proof"]
assert any(l.startswith("qc sandbox: ok   no Pi model credentials (no Pi runs here): auth.json and models.json absent from ") for l in proof), proof
assert not any("SECRET-pi" in l for l in proof), proof
EOF
}

# A demo alone: its sandbox none; the advisory classify run on its record reaches the model, so one OAuth warning.
qcrun acceptance-a
demo "demo alone"
grep -A4 "^PASS acceptance-a: " <<< "$out" | grep -qxF "  advisory model judgment (no gate reads it): shows, confidence 0.910 (criterion-evidence by $M; uncalibrated)" \
  || fail "demo alone: want the advisory answered (the classify run found both copies): $out"
[[ "$(grep -cxF "$warn" "$t/err")" == 1 ]] || fail "demo alone: want one OAuth warning (the advisory's copies): $(cat "$t/err")"

# A demo, a fallback judge and the advisory: the judge and the advisory classify run reach the model (both copies there);
# the demo still none; one OAuth warning for the run.
qcrun acceptance-a acceptance-b
demo "mixed"
grep -A2 '^PASS acceptance-b: \$ judge b$' <<< "$out" | grep -qE "^  evidence complete; decision agent fallback; record $rid$" \
  || fail "mixed: want acceptance-b passed by the fallback judge (it found both copies): $out $(tail -20 "$t/err")"
for i in acceptance-a acceptance-b; do
  grep -A4 "^PASS $i: " <<< "$out" | grep -qxF "  advisory model judgment (no gate reads it): shows, confidence 0.910 (criterion-evidence by $M; uncalibrated)" \
    || fail "mixed: want $i's advisory answered (the classify run found both copies): $out"
done
python3 - "$rep" <<'EOF' || fail "mixed: judge proof: $(cat "$rep")"
import json, sys
proof = [l for f in json.load(open(sys.argv[1]))["fallback"].values() for l in f["sandbox"]["proof"]]
assert "qc sandbox: ok   Pi model credentials: auth.json models.json per-run copies on the hidden run tmpfs, never written back" in proof, proof
EOF
[[ "$(grep -cxF "$warn" "$t/err")" == 1 ]] || fail "mixed: want one OAuth warning: $(cat "$t/err")"
! grep -q 'SECRET-pi' <<< "$out$(cat "$t/err")" || fail "mixed: a credential value printed"

# A demo that cannot run to its end (exit 77): insufficient evidence, no advisory, no judge: no sandbox got copies,
# so no OAuth warning.
sed -i 's/; echo neither readable/; exit 77/' qc.toml; git commit -qam "demo stops"; head="$(git rev-parse HEAD)"
want=2 qcrun acceptance-a
grep -q '^INSUFFICIENT EVIDENCE acceptance-a: ' <<< "$out" || fail "exit 77: want insufficient evidence: $out"
! grep -q 'advisory' "$t/err" || fail "exit 77: an advisory ran: $(cat "$t/err")"
! grep -qF "$warn" "$t/err" || fail "exit 77: OAuth warning for a run whose sandboxes copied nothing: $(cat "$t/err")"
echo "qc-creds: ok (a declared demo's sandbox holds no auth.json or models.json: its proof says so, its record shows both unreadable, no secret stored; the fallback judge and the advisory classify run find both per-run copies and reach the model; box files unchanged; the OAuth warning once for a run with copies, none for a run whose only sandbox, a demo's, copied nothing)"
