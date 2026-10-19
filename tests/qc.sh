#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qc with a fake `pi` on PATH (no model
# call): only passed criteria become built, one status-only commit, a same-family
# judge, a dirty tree, an unusable report and a judge that writes are refused.
# Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
Q="$kit/scripts/octo-feather-qc"; S="$kit/scripts/octo-feather-spec-status"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
export OCTO_FEATHER_QC_DIR="$t/reports" XDG_CACHE_HOME="$t/cache"
mkdir -p "$t/bin" "$t/repo/docs/specs"
cat > "$t/bin/pi" <<'EOF'
#!/usr/bin/env bash
# Fake judge: FAKE_QC picks the reply.
case "$FAKE_QC" in
  mixed) printf 'done\n```json\n{"head": "x", "criteria": [{"id": "acceptance-a", "verdict": "pass", "command": "app a --json", "output": "{\\"ok\\": true}", "why": "shown"}, {"id": "acceptance-b", "verdict": "fail", "command": "app b --json", "output": "error", "why": "no b"}]}\n```\n' ;;
  garbage) echo "I think it works." ;;
  writes) echo hacked > judge-was-here; printf '```json\n{"criteria": []}\n```\n' ;;
esac
EOF
chmod +x "$t/bin/pi"; export PATH="$t/bin:$PATH"
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$t/repo/docs/specs/"
cd "$t/repo"; git init -q -b main .
"$S" init docs/specs/demo.spec.html 0123abc >/dev/null; git add -A; git commit -qm spec
st=docs/specs/demo.status.json
run() { local want="$1"; shift; set +e; out="$(FAKE_QC="$1" "$Q" "${@:2}" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || { echo "qc test: FAKE_QC=$1 '${*:2}' want exit $want, got $rc: $out" >&2; exit 1; }; }
OCTO_FEATHER_QC_MODEL=anthropic/claude-opus-5-5 run 64 mixed $st 5 acceptance-a acceptance-b   # judge of the implementer's family
echo x > dirty; run 65 mixed $st 5 acceptance-a; rm dirty                                      # dirty worktree
before="$(git rev-parse HEAD)"
run 3 garbage $st 5 acceptance-a acceptance-b                                                   # no json report
run 3 writes $st 5 acceptance-a                                                                 # judge wrote a file
[[ "$(git rev-parse HEAD)" == "$before" ]] || { echo "qc test: refused run moved the head" >&2; exit 1; }
git clean -qfd
run 1 mixed $st 5 acceptance-a acceptance-b                                                     # a passes, b fails
python3 - "$st" <<'EOF'
import json, sys
c = json.load(open(sys.argv[1]))["criteria"]
assert c["acceptance-a"] == {"status": "built", "pr": 5}, c
assert c["acceptance-b"] == {"status": "planned", "pr": None}, c
EOF
[[ "$(git diff --name-only "$before" HEAD)" == "$st" && "$(git rev-list --count "$before"..HEAD)" == 1 ]] \
  || { echo "qc test: expected one commit touching only the status file" >&2; exit 1; }
[[ -s "$t/reports/$before.json" ]] || { echo "qc test: no report for the judged head" >&2; exit 1; }
echo "qc: ok (pass flips built, fail stays planned, status-only commit, same family, dirty, unusable report, judge wrote)"
