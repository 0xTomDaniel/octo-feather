#!/usr/bin/env bash
# gate: e2e
# criterion: quality#acceptance-qc-carry
# Integration test for qc carry (quality spec #qc-carry), through `just qc` / octo-feather-qc, the status file and the qc
# report, with a fake herdr and a fake pi that reaches no model (the advisory's). A scratch target on a lane
# branch: its earlier head passes demos a, b, c and the tagged tests g and h (h with no covered path), fails e and gets
# insufficient evidence on i and on f (an entry with covers, no demo, no tagged test: neither). Each later head is a merge of main changing one thing; what qc on it carries or
# judges again: quality spec #qc-carry, each case below. Needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN OCTO_FEATHER_QC_CLAIMS   # a test harness, as tests/qc.sh: the scratch gate sets its own
[[ "$(uname -s)" != Darwin ]] || { echo "qc-carry: skipped, not on macOS (the qc sandbox needs Linux; CI runs it)"; exit 77; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
UV_CACHE_DIR="$(uv cache dir)"; UV_PYTHON_INSTALL_DIR="$(uv python dir)"; export UV_CACHE_DIR UV_PYTHON_INSTALL_DIR   # the kit's locked pytest, offline
for d in data cache config; do v="MISE_${d^^}_DIR"; [[ -n "${!v:-}" ]] || export "$v=$(mise doctor --json | jq -r --arg d "$d" '.dirs[$d]')"; done
fail() { echo "qc-carry test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp" KIT="$kit"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME" "$TMPDIR" "$t/bin" "$t/stub" "$t/repo/docs/specs" "$t/repo/tests/gate" "$t/repo/src" "$t/repo/fixtures"
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
printf '#!/bin/sh\necho "fake pi: no model here" >&2; exit 9\n' > "$t/stub/pi"
chmod +x "$t/bin/herdr" "$t/stub/pi"
export PATH="$t/bin:$kit/scripts:$PATH" OCTO_FEATHER_QC_PATH="$t/stub"

cd "$t/repo"; git init -q -b main .
git commit -qm accepted --allow-empty
crit() { echo "<p data-acceptance-criterion data-anchor=\"acceptance-$1\"><span data-acceptance-scenario>Given a user, When $1 runs,</span> <span data-acceptance-outcome>then it prints ${2:-ok}.</span></p>"; }
spec() { { echo '<!doctype html><html><body><article data-spec-contract="shaped-sections-v1">'
  echo '<section data-spec-section="acceptance" data-anchor="acceptance" id="acceptance"><h2>Acceptance criteria</h2>'
  crit a; crit b; crit c "$1"; crit e; crit f; crit g; crit h; crit i; echo '</section></article></body></html>'; } > docs/specs/carry.spec.html; }
spec ok; git add -A; git commit -qm spec
octo-feather-spec-status init docs/specs/carry.spec.html "$(git rev-parse --short HEAD)" >/dev/null
cp "$kit/tests/gate/conftest.py" "$kit/tests/gate/test_gate.py" tests/gate/
printf '.pytest_cache/\n__pycache__/\n' > .gitignore
printf '[pytest]\ntestpaths = tests/gate\naddopts = --strict-markers --junitxml=.pytest_cache/junit.xml\n' > pytest.ini
cat > justfile <<'EOF'
set positional-arguments
export GATE_RECIPES := "check-ok"
export OCTO_FEATHER_CHECK_RUN := `check-gate-free --run`
check: check-tests
check-ok:
    @true
check-tests *args:
    uv run --project "$KIT" --locked --offline --no-sync pytest -n 2 "$@"
EOF
for p in g h; do printf '#!/usr/bin/env bash\n# criterion: carry#acceptance-%s\necho %s ok\n' $p $p > tests/$p.sh; chmod +x tests/$p.sh; done
for p in a b c f g; do echo "$p v1" > "src/$p"; done
echo "seed v1" > fixtures/seed
demo() { printf '[demo."carry#acceptance-%s"]\ncommand = %s\ncovers = ["src/%s"]\n' "$1" "$2" "$1"; }
{ printf 'format = 2\n[entry]\ncommand = "true"\n[services]\n[fixture.seed]\nreset = "true"\npath = "fixtures/seed"\n[values]\n'
  demo a '"echo a ok"'; demo b '"echo b ok"'; demo c '"echo c ok"'; demo e '"echo e broke >&2; exit 3"'
  printf '[demo."carry#acceptance-%s"]\ncovers = ["src/%s"]\n' f f g g; demo i '"echo needs a GPU, none here >&2; exit 77"'; } > qc.toml
git add -A; git commit -qm target
git checkout -qb lane
gate() { set +e; out="$(timeout -k 5 300 env OCTO_FEATHER_QC_CLAIMS="carry#acceptance-g carry#acceptance-h" just check 2>&1)"; rc=$?; set -e
  [[ "$rc" == 0 ]] || fail "claims gate at $(git rev-parse --short HEAD): $rc: $out"; }
qcrun() { # WANT-EXIT ID...: just qc for PR ${PR:-9} on the lane's head
  local want="$1"; shift; head="$(git rev-parse HEAD)"
  set +e; out="$(timeout -k 5 300 just --justfile "$kit/justfile" qc docs/specs/carry.status.json "${PR:-9}" "${@/#/acceptance-}" 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "qc at ${head:0:12} on $*: want exit $want, got $rc: $out $(tail -20 "$t/err")"
  rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"; }
merge() { # MSG: commit this change on main, merge main into the lane (a new lane head)
  git stash -q -u; git checkout -q main; git stash pop -q; git add -A; git commit -qm "$1"
  git checkout -q lane; git merge -q --no-edit main; }
# results ID=WANT...: each result in the latest report; WANT carried@<head var>:<record> or judged:<verdict>
results() { python3 - "$rep" "$head" "$@" <<'EOF' || fail "report at ${head:0:12}: $(cat "$rep") $out"
import json, sys
rep, head, *want = sys.argv[1:]
r = {x["id"]: x for x in json.load(open(rep))["results"]}
for w in want:
    i, how = w.split("=", 1); x = r["acceptance-" + i]
    if how.startswith("carried@"):
        at, rec = how.removeprefix("carried@").split(":")
        assert x.get("carried") is True and (x["verdict"], x["head"], x["record"]) == ("pass", at, rec), (i, x)
    else:
        assert not x.get("carried") and x["verdict"] == how.removeprefix("judged:") and x["head"] == head, (i, x)
EOF
}
row() { python3 -c 'import json,sys; c=json.load(open("docs/specs/carry.status.json"))["criteria"]["acceptance-"+sys.argv[1]]; print(c.get("record"), c.get("commit"), c["status"])' "$1"; }
said() { grep -q -- "$1" "$t/err" || fail "qc at ${head:0:12}: want stderr naming '$1': $(cat "$t/err")"; }

# The earlier head: every kind of result.
gate; h0="$(git rev-parse HEAD)"
qcrun 1 a b c e f g h i
read -r a0 _ _ <<< "$(row a)"; read -r c0 _ _ <<< "$(row c)"; read -r g0 _ _ <<< "$(row g)"
results a=judged:pass b=judged:pass c=judged:pass e=judged:fail f="judged:insufficient evidence" g=judged:pass h=judged:pass i="judged:insufficient evidence"

# A merge of main changes src/b, which only b covers: b judged again; a, c and g carried with their head and record,
# g with no gate run here; h with no covered path, the failed e and the insufficient f and i judged again.
echo "b v2" > src/b; merge "main: src/b"
qcrun 1 a b c e f g h i
results a="carried@$h0:$a0" c="carried@$h0:$c0" g="carried@$h0:$g0" b=judged:pass e=judged:fail f="judged:insufficient evidence" h="judged:insufficient evidence" i="judged:insufficient evidence"
grep -A1 '^PASS acceptance-a: ' <<< "$out" | grep -q "carried: judged at ${h0:0:12}, record $a0" || fail "carried a not shown with its head and record: $out"
grep -c '^qc: demo ' "$t/err" | grep -qx 3 || fail "want only b, e and i's demos run: $(cat "$t/err")"
[[ "$(row a)" == "$a0 $h0 built" && "$(row b | cut -d' ' -f2-)" == "$head built" ]] || fail "want a and b built, a at $h0, b at $head: $(row a); $(row b)"
said "covered path src/b changed"; said "acceptance-h again: no covered path"

# The gate configuration (the justfile) moves: g judged again from its new gate record; a carried.
echo "# a comment" >> justfile; merge "main: justfile"
gate; qcrun 0 a g
results a="carried@$h0:$a0" g=judged:pass; said "acceptance-g again: gate configuration"

# c's text moves, and g's named test: both judged again (g with no gate record here, so insufficient); a carried.
spec "OK"; echo '{"at": "2026-11-05T00:00:00Z", "lane": "gh12", "role": "supervisor", "kind": "clarifies", "anchors": ["acceptance-c"], "criteria": ["acceptance-c"], "what": "w", "why": "w", "passes_as_written": false, "evidence": "e"}' > docs/specs/carry.calls.jsonl
echo 'echo g2' >> tests/g.sh; merge "main: c text, tests/g.sh"
qcrun 2 a c g
results a="carried@$h0:$a0" c=judged:pass g="judged:insufficient evidence"; said "acceptance-c again: .*criterion text changed"; said "acceptance-g again: .*test file tests/g.sh changed"

# A test newly tagged with c: c judged again (no gate record here, so insufficient); a carried.
printf '#!/usr/bin/env bash\n# criterion: carry#acceptance-c\necho c2 ok\n' > tests/c2.sh; chmod +x tests/c2.sh; merge "main: tests/c2.sh"
qcrun 2 a c
results a="carried@$h0:$a0" c="judged:insufficient evidence"; said "acceptance-c again: newly tagged at ${head:0:12}: tests/gate/test_gate.py::test_script\[tests/c2.sh\]"

# The fixture moves, then the contract: a judged again each time.
echo "seed v2" > fixtures/seed; merge "main: fixture"
qcrun 0 a; results a=judged:pass; said "acceptance-a again: fixture"
echo "# a comment" >> qc.toml; merge "main: contract"
qcrun 0 a; results a=judged:pass; said "acceptance-a again: contract"
# Another lane (PR 10) naming a: judged again, never carried from lane 9's pass.
echo "b v3" > src/b; merge "main: src/b again"
PR=10 qcrun 0 a; results a=judged:pass; said "acceptance-a again: built in PR #9"
echo "qc-carry: ok (a merge of main: the criterion whose covered path moved judged again, the others carried with their judged head and record, both built; failed and insufficient criteria, and moved text, named test, a newly tagged test, gate configuration, fixture and contract, or another lane, judged again)"
