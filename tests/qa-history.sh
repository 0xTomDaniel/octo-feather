#!/usr/bin/env bash
# Integration test for scripts/octo-feather-qa (factory evals) and scripts/check-evals (eval case shape), driven as
# commands with a stub `pi` and a fake `herdr` first on PATH: no model, no live Herdr (tests/lib/qa.sh).
# One section of the factory-evals test per gate item (#506): tests/qa.sh and each tests/qa-*.sh.
# Proves spec quality#acceptance-qa-history through a history fixture (the form: schema.md, Case): a stub case on the
# kit's own history at a commit runs its role on that whole tree, one on a named local clone too; check-evals refuses an
# unknown repo or commit, naming case and field.
# Run by `just check`; needs unprivileged user namespaces (`unshare -rm`), as tests/qc.sh does.
# shellcheck source=tests/lib/qa.sh
source "$(dirname "$0")/lib/qa.sh"
at="$(git -C "$kit" rev-parse 711392a)"   # a kit commit: the #532 base
want="$(git -C "$kit" ls-tree -r --name-only "$at" | wc -l)"
# A named local clone at ~/src/tgt (the throwaway HOME), its one commit.
git init -q "$HOME/src/tgt"; mkdir -p "$HOME/src/tgt/deep/er"; echo t > "$HOME/src/tgt/deep/er/leaf.txt"
git -C "$HOME/src/tgt" add -A; git -C "$HOME/src/tgt" -c user.name=t -c user.email=t@t.invalid -c commit.gpgsign=false commit -qm tgt
tgt="$(git -C "$HOME/src/tgt" rev-parse HEAD)"
mkdir -p "$t/hi/hi/reference" "$t/hi/fixtures"
echo '{"suite": "hi", "kind": "role-transcript", "description": "stub history", "max_tool_calls": 10, "timeout_s": 120}' > "$t/hi/hi/suite.json"
python3 - "$t/hi/hi" "$at" "$tgt" <<'PY'
import json, sys
d, at, tgt = sys.argv[1:]
look = "Look. STUB-STEPS:" + json.dumps([["bash", "echo files=$(git ls-files | wc -l); echo head={head}; git log --oneline | wc -l; "
                                                   "test -f .agents/skills/eval-cases/references/schema.md && echo deep=ok; test -f deep/er/leaf.txt && echo leaf=ok"]])
json.dump([{"id": "kit", "role": "implementer", "fixture": {"repo": "kit", "commit": at}, "task": look},
           {"id": "clone", "role": "implementer", "fixture": {"repo": "tgt", "commit": tgt}, "task": look}], open(f"{d}/cases.json", "w"))
json.dump({i: {"facts": [{"fact": "skill_not_read", "skill": "pull"}]} for i in ("kit", "clone")}, open(f"{d}/reference/expectations.json", "w"))
PY
cp -r "$t/hi" "$t/hi-good"

run 0 "$Q" --evals "$t/hi"
line() { grep -E "^$1 hi/$2: " <<< "$out" || fail "no $1 line for $2: $out"; }
line PASS kit > /dev/null; line PASS clone > /dev/null
d="$(ls -dt "$t"/out/*/ | head -1)"
tr_() { python3 -c 'import json, sys
for l in open(sys.argv[1]):
    e = json.loads(l)
    if e.get("type") == "tool_execution_end":
        print(e["result"]["content"][0]["text"])' "$d/hi/$1/transcript.jsonl"; }
k="$(tr_ kit)"; c="$(tr_ clone)"
grep -qx "files=$want" <<< "$k" && grep -qx "deep=ok" <<< "$k" || fail "the role did not see the kit's whole tree at $at ($want files): $k"
grep -qx "1" <<< "$k" || fail "the case repo is not one fixture commit on main: $k"
grep -qx "leaf=ok" <<< "$c" && grep -qx "files=1" <<< "$c" || fail "the clone's tree not the case repo: $c"
grep -q "\"fixture\": {" "$d/hi/kit/input.json" || fail "input.json does not record the history fixture"

# Shape: an unknown repo, a commit the repo lacks, a short sha.
bad 'c[0]["fixture"]["repo"] = "nosuch"' "hi/cases.json case kit: field fixture.repo: 'nosuch' is not kit or a git clone at ~/src/<name>" "$t/hi-good" hi
bad 'c[0]["fixture"]["commit"] = "0" * 40' "hi/cases.json case kit: field fixture.commit: no commit $(printf '0%.0s' {1..40}) in" "$t/hi-good" hi
bad 'c[1]["fixture"]["commit"] = c[1]["fixture"]["commit"][:9]' "hi/cases.json case clone: field fixture.commit: must be a full 40 character sha" "$t/hi-good" hi
bad 'del c[1]["fixture"]["commit"]' "hi/cases.json case clone: field fixture.commit: missing" "$t/hi-good" hi
echo "qa-history: ok (a history fixture on the kit's own history and a named clone: the role ran on the whole tree at that commit; unknown repo or commit refused naming case and field)"
