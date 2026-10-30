#!/usr/bin/env bash
# Integration test for the agent fallback (quality spec #qc-fallback, #acceptance-qc-fallback), through `just qc` /
# octo-feather-qc and octo-feather-evidence read, with a fake herdr and the stub judge tests/fixtures/qc-judge/pi (no model): a scratch target whose
# qc.toml declares no demo. acceptance-a and acceptance-b each get their own fresh qc judge, one
# sandbox each, its brief naming that criterion alone, run under the fixed time cap (the judge's parent
# is coreutils timeout at that cap); each result is labelled agent fallback and names the evidence record the judge's report was
# stored as, which reads back at the head (a declared one beside them: tests/qc-capture.sh). A judge the cap stops
# (the stub fires its timeout's alarm) leaves a record with no report: evidence incomplete, the run exits 3
# naming it as insufficient evidence (exit 2) and the status file is unchanged.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh.
set -euo pipefail
unset OCTO_FEATHER_CHECK_RUN   # a test harness, as tests/qc.sh: qc refuses only under the gate's marker
[[ "$(uname -s)" != Darwin ]] || { echo "qc-fallback: skipped, not on macOS (just qc needs Linux; CI runs it)"; exit 0; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t" 2>/dev/null; rm -rf "$t"' EXIT
t="$(cd "$t" && pwd -P)"
fail() { echo "qc-fallback test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" TMPDIR="$t/tmp"
unset XDG_CONFIG_HOME XDG_CACHE_HOME GH_CONFIG_DIR HERDR_SESSION HERDR_SOCKET_PATH HERDR_BIN_PATH HERDR_ENV OCTO_FEATHER_QC_DIR FAKE_QC_JUDGE
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
chmod +x "$t/bin/herdr"
export PATH="$t/bin:$kit/scripts:$PATH"
# The stub judge (tests/fixtures/qc-judge/pi) first on the sandbox's PATH: passes the brief's criterion unless FAKE_QC_FAIL names it.
export OCTO_FEATHER_QC_PATH="$kit/tests/fixtures/qc-judge" FAKE_QC_FAIL=acceptance-a
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
EOF
git add -A; git commit -qm "contract: no demo"
head="$(git rev-parse HEAD)"
rid='[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}'
qcrun() { set +e; out="$(timeout -k 5 120 just --justfile "$kit/justfile" qc docs/specs/demo.status.json 9 "$@" 2>"$t/err")"; rc=$?; set -e
  [[ "$rc" != 124 && "$rc" != 137 ]] || fail "qc hung: $(tail -20 "$t/err")"; }

qcrun acceptance-a acceptance-b
[[ "$rc" == 1 ]] || fail "want exit 1 (acceptance-a failed), got $rc: $out $(tail -20 "$t/err")"
c="$(grep -A2 '^FAIL acceptance-a: \$ judge acceptance-a$' <<< "$out" | sed -nE "s/^  evidence complete; decision agent fallback; record ($rid)$/\1/p")"
b="$(grep -A2 '^PASS acceptance-b: \$ judge acceptance-b$' <<< "$out" | sed -nE "s/^  evidence complete; decision agent fallback; record ($rid)$/\1/p")"
[[ -n "$b" && -n "$c" ]] || fail "want acceptance-a fail and acceptance-b pass, each labelled agent fallback naming its record: $out"
[[ "$(grep -c '^qc: agent fallback demo#acceptance-[ab]: a fresh qc judge, time cap 900 s$' "$t/err")" == 2 ]] \
  || fail "want one capped judge announced per undeclared criterion: $(cat "$t/err")"
[[ "$(git log -1 --format=%s)" == "qc: built acceptance-b (judged ${head:0:12})" ]] || fail "status commit: $(git log -1 --format=%s)"
# The report: one judge per undeclared criterion, each its own sandbox, its brief naming it alone, under timeout's cap.
rep="$(ls -t "$XDG_STATE_HOME"/octo-feather/qc/"$head"-*.json | head -1)"
python3 - "$rep" "$head" "$b" "$c" <<'EOF' || fail "report: $(cat "$rep")"
import json, sys
rep, head, b, c = sys.argv[1:]
r = json.load(open(rep))
assert r["cap_s"] == 900 and sorted(r["fallback"]) == ["acceptance-a", "acceptance-b"], r.keys()
for i, rec in (("acceptance-b", b), ("acceptance-a", c)):
    f = r["fallback"][i]
    lines = f["stdout"].splitlines()
    assert [l for l in lines if l.startswith("BRIEF ")] == [f"BRIEF - {i}: Given a user, When {i} runs, then it prints ok."], lines
    assert next(l for l in lines if l.startswith("PARENT ")).startswith("PARENT timeout --foreground -k 10 900 "), lines
    assert f["exit"] == 0 and f["record"] == rec, f
assert len({r["fallback"][i]["sandbox"]["session"] for i in r["fallback"]}) == 2, "the judges shared a sandbox"
res = {x["id"]: x for x in r["results"]}
assert [(res[i]["verdict"], res[i]["evidence"], res[i]["decision"], res[i]["record"], res[i]["head"]) for i in ("acceptance-b", "acceptance-a")] \
    == [("pass", "complete", "agent fallback", b, head), ("fail", "complete", "agent fallback", c, head)], res
EOF
# Each judge's report reads back as its criterion's evidence record at the head.
for x in "acceptance-b $b pass" "acceptance-a $c fail"; do set -- $x
  rd="$("$ev" read --repo . --criterion "demo#$1" --commit "$head" --json)"
  python3 - "$rd" "$head" "$1" "$2" "$3" <<'EOF' || fail "record of $1: $rd"
import json, os, sys
rd, head, i, rid, v = sys.argv[1:]
(x,) = json.loads(rd)
r, out = x["record"], os.path.join(x["dir"], "outputs")
assert r["id"] == rid and r["revision"] == head and r["dirty"] is False, r
assert sorted(r["outputs"]) == ["judge.exit", "judge.report.json", "judge.stdout"], r["outputs"]
rep = json.load(open(os.path.join(out, "judge.report.json")))
assert rep == {"head": head, "criteria": [{"id": i, "verdict": v, "command": f"judge {i}", "output": f"out {i}", "why": f"why {i}"}]}, rep
assert open(os.path.join(out, "judge.exit")).read() == "0\n"
EOF
done

# The cap stops a judge: its record holds no report, insufficient evidence naming it (exit 2), status unchanged. A judge that
# ignores TERM (stubborn) is stopped by timeout's KILL after -k, timeout exiting 137 instead of 124: the same result.
for mode in "cap 124" "stubborn 137"; do set -- $mode
  git reset -q --hard "$head"
  SECONDS=0; FAKE_QC_JUDGE=$1 qcrun acceptance-b
  [[ "$rc" == 2 && "$SECONDS" -lt 60 ]] || fail "$1 judge: want exit 2 well before its 60 s sleep, got $rc after $SECONDS s: $(tail -20 "$t/err")"
  grep -A2 '^INSUFFICIENT EVIDENCE acceptance-b: ' <<< "$out" | grep -A1 '^  missing: the judge hit its 900 s time cap before reporting; outputs missing: judge.report.json$' \
    | grep -qE "^  evidence incomplete; decision agent fallback; record $rid$" || fail "$1 judge not named: $out $(tail -20 "$t/err")"
  [[ "$(git rev-parse HEAD)" == "$head" && -z "$(git status --porcelain)" ]] || fail "$1 judge: status file changed"
  "$ev" read --repo . --criterion demo#acceptance-b --commit "$head" --json | python3 -c '
import json, os, sys
x = json.load(sys.stdin)[-1]
assert sorted(x["record"]["outputs"]) == ["judge.exit", "judge.stdout"], x["record"]["outputs"]
assert open(os.path.join(x["dir"], "outputs", "judge.exit")).read() == sys.argv[1] + "\n"' "$2" || fail "$1 judge: its record"
done
echo "qc-fallback: ok (two undeclared criteria: a fresh capped judge each, alone in its brief, own sandbox; results labelled agent fallback, each naming the record its report reads back from at the head; a judge stopped by the cap, by TERM or by the later KILL: record without a report, insufficient evidence naming it (exit 2), status unchanged)"
