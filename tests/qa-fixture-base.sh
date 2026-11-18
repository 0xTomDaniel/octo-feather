#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape), driven as
# commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves based fixtures (rule: .agents/skills/eval-cases/references/schema.md, Fixtures, #988) in octo-feather-qa's case
# repo (main, head, head.then and branches: #991) and check-evals' fixture checks, --trees against a flat copy, and the refusals.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
e="$t/fb"; F="$e/fixtures"
mkdir -p "$e/fb/reference" "$F/root/tools" "$F/root/sub" "$F/mid/sub" "$F/over/sub" "$F/headover"
# root: a whole tree; mid over root, over over mid (a chain); headover over root. flat: over's tree written out whole.
echo root > "$F/root/README.md"; echo base > "$F/root/sub/keep.txt"; echo old > "$F/root/sub/swap.txt"
printf '#!/bin/sh\necho run\n' > "$F/root/tools/run.sh"; chmod +x "$F/root/tools/run.sh"; ln -s README.md "$F/root/link"
mkdir -p "$F/root/.agents/skills/base-only"
printf -- '---\nname: base-only\ndescription: a base fixture skill\n---\n\nDo it.\n' > "$F/root/.agents/skills/base-only/SKILL.md"
echo '{"base": "root"}' > "$F/mid/.eval-fixture.json"; echo mid > "$F/mid/sub/swap.txt"; ln -s sub/keep.txt "$F/mid/link"
echo '{"base": "mid"}' > "$F/over/.eval-fixture.json"; echo over > "$F/over/sub/new.txt"
echo '{"base": "root"}' > "$F/headover/.eval-fixture.json"; echo head > "$F/headover/README.md"
cp -a "$F/root" "$F/flat"; rm "$F/flat/link"; cp -a "$F/mid/sub" "$F/mid/link" "$F/over/sub" "$F/flat/"
echo '{"suite": "fb", "kind": "role-transcript", "description": "stub based fixtures", "max_tool_calls": 10, "timeout_s": 120}' > "$e/fb/suite.json"
python3 - "$e/fb" <<'PY'
import json, sys
d = sys.argv[1]
look = "Look. STUB-STEPS:" + json.dumps([["bash", "git ls-tree -r main; echo ===; git ls-tree -r HEAD; ls -a"]])
cases = [{"id": "main", "role": "implementer", "fixture": "over", "task": look},
         {"id": "head", "role": "implementer", "fixture": "root", "task": look,
          "head": {"fixture": "headover", "branch": "hb", "message": "head"}},
         {"id": "flat", "role": "implementer", "fixture": "flat", "task": look},
         {"id": "seq", "role": "implementer", "fixture": "root",
          "task": "Look. STUB-STEPS:" + json.dumps([["bash", "git ls-tree -r main; echo ===; git ls-tree -r HEAD; echo ===; git ls-tree -r bb"]]),
          "head": {"fixture": "headover", "branch": "hb", "message": "head", "then": [{"fixture": "over", "message": "then"}]},
          "branches": [{"fixture": "mid", "branch": "bb", "message": "b"}]}]
json.dump(cases, open(f"{d}/cases.json", "w"))
json.dump({c["id"]: {"facts": [{"fact": "skill_not_read", "skill": "pull"}]} for c in cases}, open(f"{d}/reference/expectations.json", "w"))
PY
cp -r "$e" "$t/fb-good"

# The case repo: main is over's whole tree, as flat's (git's own modes and blob ids, the oracle); head commits headover.
run 0 "$Q" --evals "$e"
for c in main head flat seq; do grep -qE "^PASS fb/$c: " <<< "$out" || fail "no PASS line for $c: $out"; done
d="$(ls -dt "$t"/out/*/ | head -1)"
tr_() { python3 -c 'import json, sys
for l in open(sys.argv[1]):
    e = json.loads(l)
    if e.get("type") == "tool_execution_end":
        print(e["result"]["content"][0]["text"])' "$d/fb/$1/transcript.jsonl"; }
m="$(tr_ main)"; h="$(tr_ head)"; want="$(tr_ flat)"
[[ "$(sed '/^===$/q' <<< "$m")" == "$(sed '/^===$/q' <<< "$want")" ]] || fail "main is not over's whole tree: $m  vs flat: $want"
grep -q "^100755 blob .*	tools/run.sh$" <<< "$m" && grep -q "^120000 blob .*	link$" <<< "$m" || fail "exec bit or symlink lost: $m"
grep -q "eval-fixture" <<< "$m$h" && fail "the base file reached the case repo: $m $h"
grep -q "^100644 blob $(git hash-object "$F/headover/README.md")	README.md$" <<< "$(sed '1,/^===$/d' <<< "$h")" \
  || fail "head is not headover's tree over root: $h"
grep -q "	tools/run.sh$" <<< "$(sed '1,/^===$/d' <<< "$h")" || fail "head lost root's files: $h"

# head.then and branches (schema.md, Case): then commits over's whole tree, as flat's; branch bb holds mid's tree.
s="$(tr_ seq)"; st="$(sed '1,/^===$/d' <<< "$s")"; bb="$(sed '1,/^===$/d' <<< "$st")"
[[ "$(sed '/^===$/,$d' <<< "$st")" == "$(sed '1,/^===$/d' <<< "$want" | grep $'\t')" ]] || fail "head.then is not over's whole tree: $s  vs flat: $want"
grep -q "^100644 blob $(git hash-object "$F/mid/sub/swap.txt")	sub/swap.txt$" <<< "$bb" && grep -q "^100755 blob .*	tools/run.sh$" <<< "$bb" \
  && grep -q "^120000 blob $(printf sub/keep.txt | git hash-object --stdin)	link$" <<< "$bb" && ! grep -q "sub/new.txt" <<< "$bb" \
  || fail "branch bb is not mid's tree over root: $s"

# --trees (schema.md, Fixtures): over hashes as flat; the history marker; a line for each head.then and branches tree.
run 0 "$C" --trees "$e"
sha() { grep -E "^fb $1 $2 " <<< "$out" | cut -d' ' -f4; }
[[ -n "$(sha seq 'head\.then\[0\]')" && "$(sha seq 'head\.then\[0\]')" == "$(sha flat fixture)" ]] || fail "--trees: no head.then[0] line as flat: $out"
[[ -n "$(sha seq 'branches\[0\]')" && "$(sha seq 'branches\[0\]')" != "$(sha seq fixture)" ]] || fail "--trees: no branches[0] line: $out"
[[ -n "$(sha main fixture)" && "$(sha main fixture)" == "$(sha flat fixture)" ]] || fail "--trees: over not hashed as flat: $out"
[[ -n "$(sha head head)" && "$(sha head head)" != "$(sha head fixture)" ]] || fail "--trees: no head tree line: $out"
python3 - "$e/fb" <<'PY'
import json, sys
p = f"{sys.argv[1]}/cases.json"; c = json.load(open(p)); c[2]["fixture"] = {"repo": "kit", "commit": "a" * 40}; json.dump(c, open(p, "w"))
PY
run 0 "$C" --trees "$e"; grep -qx "fb flat fixture history kit@$(printf 'a%.0s' {1..40})" <<< "$out" || fail "--trees: history not marked: $out"
rm -rf "$e"; cp -r "$t/fb-good" "$e"

# check-evals reads the materialized tree: a skill, test_write's pyproject and uv.lock only in root, graded on over.
printf '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n' > "$e/fixtures/root/pyproject.toml"; : > "$e/fixtures/root/uv.lock"
python3 - "$e/fb" <<'PY'
import json, sys
d = sys.argv[1]; p = f"{d}/reference/expectations.json"; x = json.load(open(p))
x["main"]["facts"] += [{"fact": "skill_read", "skill": "base-only"}, {"fact": "skill_read_before", "skill": "tdd", "before": "test_write"}]
json.dump(x, open(p, "w"))
PY
run 0 "$C" "$e"
# Coverage's tracker: root's .octo-feather.toml is over's too.
echo 'tracker = "jira"' > "$e/fixtures/root/.octo-feather.toml"; mkdir -p "$e/cov/reference"
echo '{"suite": "cov", "kind": "skill-trigger", "description": "coverage", "covers": "role-skills"}' > "$e/cov/suite.json"
echo '[]' > "$e/cov/cases.json"; echo '{}' > "$e/cov/reference/expectations.json"
run 1 "$C" "$e"; grep -qF "fixtures/over/.octo-feather.toml: field tracker: 'jira'" <<< "$out" || fail "over's tracker not read from root: $out"
rm -rf "$e"; cp -r "$t/fb-good" "$e"

# Refusals (schema.md, Fixtures); octo-feather-qa runs no case.
echo '{"base": "nosuch"}' > "$e/fixtures/mid/.eval-fixture.json"
run 1 "$C" "$e"; grep -qF "fixtures/mid/.eval-fixture.json: field base: no fixture dir $e/fixtures/nosuch" <<< "$out" || fail "missing base not refused: $out"
run 1 "$C" --trees "$e"; grep -qF "fb/cases.json case main: field fixture: fixtures/mid/.eval-fixture.json: field base: no fixture dir" <<< "$out" || fail "--trees: missing base: $out"
for f in "head.then[0]" "branches[0]"; do
  grep -qF "fb/cases.json case seq: field $f.fixture: fixtures/mid/.eval-fixture.json: field base: no fixture dir" <<< "$out" || fail "--trees: $f's missing base: $out"
done
run 2 "$Q" --evals "$e"; grep -qF "fixtures/mid/.eval-fixture.json: field base: no fixture dir" <<< "$out" || fail "qa ran on a missing base: $out"
echo '{"base": "over"}' > "$e/fixtures/mid/.eval-fixture.json"
run 1 "$C" "$e"; grep -qF "fixtures/over/.eval-fixture.json: field base: a cycle mid -> over -> mid" <<< "$out" || fail "cycle not refused: $out"
grep -qF "fixtures/mid/.eval-fixture.json: field base: a cycle over -> mid -> over" <<< "$out" || fail "cycle not refused from over: $out"
echo '{"base": "root", "x": 1}' > "$e/fixtures/mid/.eval-fixture.json"
run 1 "$C" "$e"; grep -qF "fixtures/mid/.eval-fixture.json: must be exactly {\"base\": <fixture name>}" <<< "$out" || fail "malformed base file not refused: $out"
echo "qa-fixture-base: ok (a based fixture chain materialized whole, exec bit and symlink kept, as the case repo's main, head, head.then and branches and in check-evals' fixture checks; --trees equal to the flat tree, a line per head.then and branches tree; missing, cyclic and malformed bases refused naming the fixture)"
