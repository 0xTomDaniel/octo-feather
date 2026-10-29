#!/usr/bin/env bash
# Integration test for qc capture (quality spec #qc-capture, #qc-judgment, #qc-results), through `just qc` /
# octo-feather-qc and octo-feather-evidence read, with a fake herdr and no model: a scratch target whose qc.toml
# declares a passing and a failing demo is judged twice at one head. Each run appends one evidence record per
# demo at that head (command, exit status, output, criterion text hash, contract version) and names it; both
# runs give pass and fail, evidence complete, decision source the demo's checks (#acceptance-qc-capture,
# #acceptance-qc-same-verdict). A criterion with no declared demo goes to the agent fallback (a fake pi),
# alone in its brief, its result labelled agent fallback with its own record (tests/qc-fallback.sh). An invalid demo declaration is refused before anything runs.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN   # a test harness, as tests/qc.sh: qc refuses only under the gate's marker
[[ "$(uname -s)" != Darwin ]] || { echo "qc-capture: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "qc-capture test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME" "$TMPDIR" "$t/bin" "$t/repo/docs/specs"
# Fake Herdr (the sandbox pins a per-run session through it) and a fake judge that refuses a brief naming a demo's criterion.
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
cat > "$t/bin/pi" <<'EOF'
#!/usr/bin/env bash
[[ "${1:-}" == --version ]] && exit 0
h="$(grep -o 'head [0-9a-f]\{40\}' <<< "$*" | head -1 | cut -d' ' -f2)"
grep -q -- '- acceptance-a:' <<< "$*" && { echo "BRIEF NAMES acceptance-a"; exit 0; }
printf '```json\n{"head": "%s", "criteria": [{"id": "acceptance-b", "verdict": "pass", "command": "judge b", "output": "ok", "why": "judged"}]}\n```\n' "$h"
EOF
chmod +x "$t/bin/herdr" "$t/bin/pi"
export PATH="$t/bin:$kit/scripts:$PATH"
ev="$kit/scripts/octo-feather-evidence"

cd "$t/repo"; git init -q -b main .
git commit -qm accepted --allow-empty
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" docs/specs/
git add -A; git commit -qm spec
octo-feather-spec-status init docs/specs/demo.spec.html "$(git rev-parse --short HEAD)" >/dev/null
contract() { cat > qc.toml <<EOF
format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = 'echo "a checks pass in \$QC_REPO"'
covers = ["src/a"]
tests = ["tests/a.sh"]
$1
EOF
git add -A; git commit -qm "contract $2"; }
contract '[demo."demo#acceptance-b"]
command = "echo b checks fail >&2; exit 3"
covers = ["src/b"]
tests = ["tests/b.sh"]' "two demos"
head="$(git rev-parse HEAD)"
qcrun() { set +e; out="$(timeout -k 5 120 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 acceptance-a acceptance-b 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "qc hung: $(tail -20 "$t/err")"; }
rid='[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}'
ids=()
for n in 1 2; do
  git reset -q --hard "$head"
  qcrun
  [[ "$rc" == 1 ]] || fail "run $n: want exit 1 (one failed), got $rc: $out $(tail -20 "$t/err")"
  a="$(grep -A2 '^PASS acceptance-a: \$ echo "a checks pass in \$QC_REPO"$' <<< "$out" | sed -nE "s/^  evidence complete; decision demo checks; record ($rid)$/\1/p")"
  b="$(grep -A2 '^FAIL acceptance-b: \$ echo b checks fail >&2; exit 3$' <<< "$out" | sed -nE "s/^  evidence complete; decision demo checks; record ($rid)$/\1/p")"
  [[ -n "$a" && -n "$b" ]] || fail "run $n: want PASS acceptance-a and FAIL acceptance-b, evidence complete, decision demo checks, each naming its record: $out"
  ! grep -q 'pi-role\|qc-judge' "$t/err" || fail "run $n: a judge started with every criterion declared: $(cat "$t/err")"
  ids+=("$a" "$b")
  st="$(git show HEAD:docs/specs/demo.status.json)"
  [[ "$(git log -1 --format=%s)" == "qc: built acceptance-a (judged ${head:0:12})" ]] \
    && python3 -c 'import json,sys; c=json.loads(sys.argv[1])["criteria"]; sys.exit(c["acceptance-a"] != {"status": "built", "pr": 9} or c["acceptance-b"]["status"] != "planned")' "$st" \
    || fail "run $n: status commit: $(git log -1 --format=%s) $st"
  # The report's results: one per criterion, its evidence state, decision source, record and the judged head.
  rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"
  python3 - "$rep" "$head" "$a" "$b" <<'EOF' || fail "run $n: report results: $(cat "$rep")"
import json, sys
rep, head, a, b = sys.argv[1:]
r = {x["id"]: x for x in json.load(open(rep))["results"]}
assert sorted(r) == ["acceptance-a", "acceptance-b"], r
for i, v, rec in (("acceptance-a", "pass", a), ("acceptance-b", "fail", b)):
    x = r[i]
    assert (x["verdict"], x["evidence"], x["decision"], x["record"], x["head"]) == (v, "complete", "demo checks", rec, head), x
EOF
done
[[ "$(printf '%s\n' "${ids[@]}" | sort -u | wc -l)" == 4 ]] || fail "two runs must append four distinct records: ${ids[*]}"

# Each record, read back through the store's command: at the head, clean, the demo's command, exit status and output,
# the criterion text's hash (the fixture spec's text, a worked literal), the contract's format and the hash of its bytes.
rd="$("$ev" read --repo . --commit "$head" --json)"
python3 - "$rd" "$head" "$(sha256sum < qc.toml | cut -d' ' -f1)" "$t/repo" "${ids[@]}" <<'EOF' || fail "records: $rd"
import hashlib, json, os, sys
rd, head, csha, repo, *ids = sys.argv[1:]
recs = {x["record"]["id"]: x for x in json.loads(rd)}
assert sorted(recs) == sorted(ids), (sorted(recs), ids)
want = {"demo#acceptance-a": ("Given a user, When acceptance-a runs, then it prints ok.", 'echo "a checks pass in $QC_REPO"', "0", f"a checks pass in {repo}\n", ""),
        "demo#acceptance-b": ("Given a user, When acceptance-b runs, then it prints ok.", "echo b checks fail >&2; exit 3", "3", "", "b checks fail\n")}
for x in recs.values():
    r, out = x["record"], os.path.join(x["dir"], "outputs")
    text, cmd, code, so, se = want[r["criterion"]["id"]]
    assert r["revision"] == head and r["dirty"] is False, r
    assert r["criterion"]["text_sha256"] == hashlib.sha256(text.encode()).hexdigest() and r["criterion"]["text_from"] == "spec", r
    assert r["contract"] == {"format": 1, "sha256": csha}, r
    got = {n: open(os.path.join(out, n)).read() for n in ("demo.cmd", "demo.exit", "demo.stdout", "demo.stderr")}
    assert got == {"demo.cmd": cmd + "\n", "demo.exit": code + "\n", "demo.stdout": so, "demo.stderr": se}, got
EOF

# Only undeclared criteria get the agent fallback: acceptance-b without a demo goes to the (fake) judge alone; acceptance-a is captured.
git reset -q --hard "$head"; contract "" "one demo"
qcrun
[[ "$rc" == 0 ]] || fail "mixed run: want exit 0, got $rc: $out $(tail -20 "$t/err")"
grep -A2 '^PASS acceptance-a: ' <<< "$out" | grep -qE "^  evidence complete; decision demo checks; record $rid$" \
  && grep -A2 '^PASS acceptance-b: \$ judge b$' <<< "$out" | grep -qE "^  evidence complete; decision agent fallback; record $rid$" \
  || fail "mixed run: want acceptance-a from its demo and acceptance-b from the agent fallback: $out"
! grep -q 'BRIEF NAMES' "$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/*.json | head -1)" || fail "mixed run: the judge's brief named the demo's criterion"

# An invalid demo declaration: refused (exit 64) naming the problem, no demo run, no record appended.
git reset -q --hard "$head"; contract '[demo."demo#acceptance-b"]
command = "true"' "demo without covers or tests"
before="$("$ev" read --repo . --json | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
qcrun
[[ "$rc" != 0 ]] && grep -q 'qc.toml is not a valid contract' "$t/err" && grep -q 'demo.demo#acceptance-b: missing covers' "$t/err" \
  || fail "invalid contract: want refused naming the missing key, got exit $rc: $(cat "$t/err")"
[[ "$("$ev" read --repo . --json | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')" == "$before" ]] || fail "invalid contract: a record was appended"
echo "qc-capture: ok (two runs at one head: pass and fail from the demos' checks, evidence complete, four records at the head holding command, exit status, output, criterion text hash and contract version, each named in the report; an undeclared criterion alone to the agent fallback; an invalid demo refused before running)"
