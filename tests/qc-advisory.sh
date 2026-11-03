#!/usr/bin/env bash
# Integration test for qc's advisory model judgment (quality spec #qc-judgment, #qc-results, #acceptance-qc-advisory;
# judgment spec #question-criterion-evidence, #rule-advisory), through `just qc` with a fake herdr and the stub
# classifier pi (tests/fixtures/classify-stub/pi) at the model boundary, no model: a scratch target declares a passing
# and a failing demo. Each recorded criterion gets the criterion-evidence question through the one classify path, its
# state the criterion's text, the demo's command and output; the answer and confidence show beside the result,
# labelled an advisory model judgment, and in the report's results. Whatever the model says (does-not-show on the
# passing demo, shows on the failing one) or when it fails (unavailable), the verdicts, exit status and status commit
# are the same.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc-capture.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN   # a test harness, as tests/qc.sh: qc refuses only under the gate's marker
[[ "$(uname -s)" != Darwin ]] || { echo "qc-advisory: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "qc-advisory test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR
unset STUB_KIT STUB_ANSWER STUB_WANT STUB_CONFIDENCE
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME" "$TMPDIR" "$t/bin" "$t/repo/docs/specs"
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
chmod +x "$t/bin/herdr"; ln -s "$kit/tests/fixtures/classify-stub/pi" "$t/bin/pi"
export PATH="$t/bin:$kit/scripts:$PATH"
# The stub, never the box's pi, is the pi a recipe resolves (the kit justfile rebuilds PATH; a mise shim or ~/.local/bin
# ahead of the stub would reach a real model): checked before any run.
rp="$(cd "$t" && PATH="$(just --justfile "$kit/justfile" --evaluate PATH)" command -v pi)"
echo "qc-advisory: recipe pi: $rp"
[[ "$rp" == "$t/bin/pi" ]] || fail "a recipe resolves pi to $rp, not the stub $t/bin/pi: nothing run"
M="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["model"])' "$kit/evals/judgment-model.json")"

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
command = "echo a checks pass"
covers = ["src/a"]
tests = ["tests/a.sh"]
[demo."demo#acceptance-b"]
command = "echo b checks fail >&2; exit 3"
covers = ["src/b"]
tests = ["tests/b.sh"]
EOF
git add -A; git commit -qm contract
head="$(git rev-parse HEAD)"
rid='[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}'
# qcrun: the same head judged again; PASS a and FAIL b from the demos' checks, exit 1, a built and b planned, whatever
# the advisory said. Sets out (stdout) and rep (the run's report).
qcrun() { git reset -q --hard "$head"; set +e
  out="$(timeout -k 5 180 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 acceptance-a acceptance-b 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "qc hung: $(tail -20 "$t/err")"
  [[ "$rc" == 1 ]] || fail "want exit 1 (b failed), got $rc: $out $(tail -20 "$t/err")"
  grep -A3 '^PASS acceptance-a: \$ echo a checks pass$' <<< "$out" | grep -qE "^  evidence complete; decision demo checks; record $rid$" \
    && grep -A3 '^FAIL acceptance-b: \$ echo b checks fail >&2; exit 3$' <<< "$out" | grep -qE "^  evidence complete; decision demo checks; record $rid$" \
    || fail "want PASS acceptance-a and FAIL acceptance-b from the demos' checks: $out"
  [[ "$(git log -1 --format=%s)" == "qc: built acceptance-a (judged ${head:0:12})" ]] || fail "status commit: $(git log -1 --format=%s)"
  rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"; }
# adv ID LINE: the advisory line right under ID's record line is exactly LINE.
adv() { grep -A4 "^[A-Z]* $1: " <<< "$out" | grep -A1 -E "^  evidence complete; decision demo checks; record $rid$" | sed -n 2p | grep -qxF -- "$2" \
  || fail "$1: want the advisory line '$2': $out"; }
# results ID ANSWER CONF|UNAVAILABLE...: the report's results entry for ID holds that advisory, labelled a model judgment.
results() { python3 - "$rep" "$M" "$@" <<'EOF' || fail "report advisory: $(cat "$rep")"
import json, sys
rep, m, i, *want = sys.argv[1:]
x = {r["id"]: r for r in json.load(open(rep))["results"]}[i]
a = x["advisory"]
assert a["judgment"].startswith("model judgment") and "advisory: no gate reads it" in a["judgment"], a
assert (a["question"], a["model"]) == ("criterion-evidence", m), a
assert (want == ["unavailable", a.get("unavailable")]) if want[0] == "unavailable" else ((a["answer"], a["confidence"]) == (want[0], float(want[1]))), (want, a)
EOF
}

# The model, induced, says the passing demo's evidence does not show its criterion: the criterion still passes.
# STUB_WANT: the classifier refuses a state without a's output, so b's answer is unavailable (its state differs).
STUB_ANSWER=does-not-show STUB_WANT=$'\nOutput:\na checks pass' qcrun
grep -qF "qc: advisory criterion-evidence question to $M for 2 recorded criteria (no gate reads it)" "$t/err" || fail "no advisory ask said: $(cat "$t/err")"
adv acceptance-a "  advisory model judgment (no gate reads it): does-not-show, confidence 0.910 (criterion-evidence by $M; uncalibrated)"
adv acceptance-b "  advisory model judgment unavailable (criterion-evidence by $M): stub: state lacks \"\\nOutput:\\na checks pass\"; the result stands as decided"
results acceptance-a does-not-show 0.91
results acceptance-b unavailable 'stub: state lacks "\nOutput:\na checks pass"'

# The failing demo, the model says shows: still a failure. Its state is exactly the criterion's text, command and output.
STUB_ANSWER=shows STUB_CONFIDENCE=0.77 STUB_WANT=$'Criterion demo#acceptance-b: Given a user, When acceptance-b runs, then it prints ok.\nCommand: echo b checks fail >&2; exit 3\nOutput:\nb checks fail' qcrun
adv acceptance-b "  advisory model judgment (no gate reads it): shows, confidence 0.770 (criterion-evidence by $M; uncalibrated)"
results acceptance-b shows 0.77

# The classifier fails on every call: both show unavailable, the results as decided.
qcrun
for i in acceptance-a acceptance-b; do
  adv "$i" "  advisory model judgment unavailable (criterion-evidence by $M): stub: provider error; the result stands as decided"
  results "$i" unavailable "stub: provider error"
done

# From a bare pane (#465): the node first on PATH is mise's shim (a link to mise named node). In qc's advice run (a
# scratch dir pinning no node; the sandbox turns the shims' system fallback off) it resolves no version; the answer still comes.
mkdir "$t/shim"; ln -s "$(command -v mise)" "$t/shim/node"
PATH="$t/shim:$PATH" STUB_ANSWER=does-not-show qcrun
adv acceptance-a "  advisory model judgment (no gate reads it): does-not-show, confidence 0.910 (criterion-evidence by $M; uncalibrated)"
# No pi on the box (#493 AC1): the sandbox's pi shim finds no real pi and refuses (exit 127), so the advice shows
# unavailable naming pi's exit and the run ends in seconds, never re-running the shim. A pi on PATH that only leads back to
# the shim (one that runs the bare name pi): refused the same way. PATH with every pi gone: each dir holding one is
# mirrored minus it (the stub's dir first loses the stub: a mirror's links into /tmp would not survive the sandbox's
# private /tmp).
rm "$t/bin/pi"
nopi="$(python3 -c 'import os, sys, tempfile
out = []
for d in filter(None, sys.argv[2].split(":")):
    if not os.path.lexists(os.path.join(d, "pi")): out.append(d); continue
    m = tempfile.mkdtemp(prefix="nopi.", dir=sys.argv[1])
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f != "pi": os.symlink(os.path.join(d, f), os.path.join(m, f))
    out.append(m)
print(":".join(out), end="")' "$t" "$PATH")"
rp="$(cd "$t" && PATH="$nopi" && PATH="$(just --justfile "$kit/justfile" --evaluate PATH)" && command -v pi)" && fail "pi hidden, yet a recipe resolves $rp"
mkdir "$t/loop"; printf '#!/bin/sh\nexec pi "$@"\n' > "$t/loop/pi"; chmod +x "$t/loop/pi"
for c in "nopi:$nopi:pi exit 127" "loop:$t/loop:$nopi:pi exit 127"; do   # the shim refused: 127, not a hang
  name="${c%%:*}"; why="${c##*:}"; p="${c#*:}"; p="${p%:*}"; SECONDS=0
  PATH="$p" qcrun
  ((SECONDS < 90)) || fail "$name: qc took $SECONDS s"
  for i in acceptance-a acceptance-b; do
    grep -A4 "^[A-Z]* $i: " <<< "$out" | grep -qE "^  advisory model judgment unavailable \(criterion-evidence by $M\): .*$why.*; the result stands as decided$" \
      || fail "$name: $i: want the advisory unavailable naming '$why': $out $(tail -20 "$t/err")"
  done
done
echo "qc-advisory: ok (no pi, or a pi leading back to the sandbox shim: advisory unavailable, no loop; each recorded criterion asked criterion-evidence of the kit's judgment model on its criterion text, command and output; answer and confidence beside the result and in the report, labelled an advisory model judgment; a pass the model says does-not-show still passes, a fail it says shows still fails, a classifier error shows unavailable, node a mise shim first on PATH too; verdicts, exit and status commit unchanged)"
