#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane tickets|ticket (spec issue-lifecycle
# #acceptance-tracer-tickets), no network: `tickets` reads tickets only through the target's tracker
# skill's issue-view (parent's children, then bodies; comms #octo-lane-record-tickets). GitHub is a
# snapshot, taken by octo-feather-qc-ghsnap from a fake GitHub gh and served by the qc judge's
# offline gh (.agents/skills/github-pr/scripts/gh), so the check is proven to work under it and to ask only
# fields octo-feather-qc-ghsnap stores; a Linear target (tracker = "linear") reads the same through
# the offline fake linear (.agents/skills/linear/scripts/linear, a JSON store). Proves: a parent whose tickets all name criteria
# and end on a demo passes; #10's real body fails naming layer-only-ticket and the fix;
# no criterion, unknown anchor or spec, gate-only demo, demo not last each fail with their
# class; rule tickets pass or fail as octo-feather-lane --help (ticket) says; a demo passes only through a surface the repo declares (tracked executable, justfile
# recipe as `just --dump` lists it, #172; pyproject/package.json bin, HTTP URL, UI driver), so the qc judge's printf draft and
# a test script fail; checks are facts only, never prose meaning (the qc judge's persistence-only
# draft passes: whether its demo shows the behavior What to build describes is review's, #118); an Expand-contract ticket passes without a
# demo; interpreter-run scripts, <template> content, fenced code and HTML comments: the #121 D11 D17 D18 D21
# cases (owners: ADR 0002, #145); a demo through a command the ticket creates passes only with an exact `Creates:`
# line, bad-creates and unused-creates otherwise (#240, ADR 0009, ADR 0008); `ticket -` checks stdin. Hermetic: PATH is built here, so no host gh is reachable. Errors
# (gh down, gh missing, bad JSON, missing ticket midway, paged sub-issues, no specs, unreadable
# draft, usage, no just or an unreadable justfile) exit 2 naming the fix, no traceback, nothing reported as passed, no file
# written. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"; F="$kit/tests/fixtures/lane-tickets/bodies"
t="$(mktemp -d)"; trap 'chmod -R u+w "$t"; rm -rf "$t"' EXIT
fail() { echo "lane-tickets test: $*" >&2; exit 1; }
export HOME="$t/home" GH_LOG="$t/gh.log" OCTO_FEATHER_GHSNAP="$t/snap" OCTO_FEATHER_GHSNAP_MISS="$t/miss.log"
unset GH_REPO GH_TOKEN FAKE_GH
mkdir -p "$HOME" "$t/bin" "$t/sys" "$t/repo/docs/specs"
# The only PATH: $t/bin (the fake gh) and $t/sys (the tools this test and the scripts run).
# No host directory is on it, so a host gh (a CI runner's, asking for GH_TOKEN) is never reached.
for c in bash python3 git env sha256sum find sort xargs grep sed cut tr cat chmod rm mkdir cp ls id dirname jq head just; do
  p="$(command -v "$c")" || fail "tool $c not found on the host"; ln -s "$p" "$t/sys/$c"
done
export PATH="$t/sys"

# The target repo: the kit's real specs (for #10's ids) plus a demo spec with acceptance-a, -b.
cp "$kit"/docs/specs/*.spec.html "$t/repo/docs/specs/"
cp "$kit/tests/fixtures/spec-status/good/demo.spec.html" "$t/repo/docs/specs/"
# Its declared surface: bin/demo (tracked executable), pyproject's `app`, justfile `serve`;
# tests/demo.sh is tracked and executable but a test, not the app's surface.
mkdir -p "$t/repo/bin" "$t/repo/tests"
printf '#!/bin/sh\necho ok\n' >"$t/repo/bin/demo"; cp "$t/repo/bin/demo" "$t/repo/tests/demo.sh"
printf 'print("score")\n' >"$t/repo/harness.py"   # a runnable script, not executable (ADR 0002)
mkdir -p "$t/repo/scripts"; cp "$t/repo/bin/demo" "$t/repo/scripts/octo-feather-lane"   # as in the kit, where the judge ran
chmod +x "$t/repo/bin/demo" "$t/repo/tests/demo.sh" "$t/repo/scripts/octo-feather-lane"
mkdir -p "$t/repo/docs/adr"; printf '# Integration is a script\n' >"$t/repo/docs/adr/0017-integration-is-a-script.md"   # the owner rule tickets name
printf '[project]\nname = "app"\n\n[project.scripts]\napp = "app.cli:main"\n' >"$t/repo/pyproject.toml"
# zz: criteria only inside a <template> (nested too), #121 D17; acceptance-ok outside one.
printf '<template><li data-acceptance-criterion data-anchor="acceptance-zz">x</li><template><p id="in"></p></template>\n<li data-acceptance-criterion data-anchor="acceptance-zz2">y</li></template>\n<ol><li data-acceptance-criterion data-anchor="acceptance-ok">z</li></ol>\n' >"$t/repo/docs/specs/zz.spec.html"
printf 'check:\n    true\n\nserve port="8000":\n    true\n\nqc:\n    true\n' >"$t/repo/justfile"
git -C "$t/repo" init -q -b main . && git -C "$t/repo" add -A

# GitHub for repo o/r: parent -> sub-issues ([total] when gh would page); ticket N's body from bodies/.
python3 - "$F" "$t/github.json" <<'EOF'
import json, sys, pathlib
F = pathlib.Path(sys.argv[1])
bodies = {int(p.stem.split("-")[0]): p.read_text() for p in F.glob("*.md")}
# 10.json: #10's body as `gh issue view 10 --json body` returns it, one paragraph trimmed (said in place).
bodies |= {int(p.stem): json.loads(p.read_text())["body"] for p in F.glob("*.json")}
parents = {100: [101, 102, 103, 104, 105, 106, 107], 8: [10, 101], 20: [21, 22, 23, 24, 25, 26, 27, 28, 33, 35, 36, 40, 41], 30: [], 50: ([101], 3), 60: [101, 199], 70: [101, 108]}
def node(n): return {"number": n, "state": "OPEN", "title": f"t{n}", "url": f"u{n}"}
iss = {}
for p, subs in parents.items():
    subs, total = subs if isinstance(subs, tuple) else (subs, len(subs))
    iss[p] = {"body": "parent", "subIssues": {"nodes": [node(n) for n in subs], "totalCount": total}}
for n, b in bodies.items():
    iss[n] = {"body": b, "subIssues": {"nodes": [], "totalCount": 0}}
iss = {n: {"number": n, "title": f"t{n}", "state": "OPEN", "updatedAt": "2026-10-20T00:00:00Z", **d} for n, d in iss.items()}
pathlib.Path(sys.argv[2]).write_text(json.dumps(iss))
EOF
# A fake GitHub gh, used only to take the snapshot: like real gh it answers every --json field
# asked (stored value or null), so the snapshot holds exactly the fields the snapshot CLI asks for.
mkdir -p "$t/github"
cat > "$t/github/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
iss = {int(k): v for k, v in json.load(open(os.environ["FAKE_GITHUB"])).items()}
def out(x): print(json.dumps(x)); sys.exit(0)
def pick(d): return {f: d.get(f) for f in a[a.index("--json") + 1].split(",")}
c = a[:2]
if c == ["repo", "view"]: out(pick({"nameWithOwner": "o/r", "name": "r", "owner": {"login": "o"}, "defaultBranchRef": {"name": "main"}}))
if c == ["issue", "list"]: out([pick(d) for d in iss.values()])
if c in (["pr", "list"], ["run", "list"]): out([])
if c == ["issue", "view"]: out(pick(iss[int(a[2])]))
if a[0] == "api":
    p = a[-1]
    if "sub_issues" in p or "dependencies" in p: sys.exit(print("gh: Not Found (HTTP 404)", file=sys.stderr) or 1)
    out([[]] if p.endswith(("/branches", "/labels", "/timeline")) else [{"full_name": "o/r"}])
sys.exit(print(f"fake github gh: unexpected {a}", file=sys.stderr) or 2)
EOF
chmod +x "$t/github/gh"
FAKE_GITHUB="$t/github.json" PATH="$t/github:$t/sys" "$kit/scripts/octo-feather-qc-ghsnap" o/r "$t/snap" >/dev/null \
  || fail "octo-feather-qc-ghsnap could not snapshot the fake GitHub"
cat > "$t/bin/gh" <<EOF
#!/usr/bin/env bash
# Logs argv, then serves the offline gh; FAKE_GH=down|garbage stand for execution failures.
printf '%s\n' "\$*" >> "\$GH_LOG"
case "\${FAKE_GH:-}" in
  down) echo "error connecting to api.github.com" >&2; exit 1 ;;
  garbage) echo "<html>rate limited</html>"; exit 0 ;;
esac
exec "$kit/.agents/skills/github-pr/scripts/gh" "\$@"
EOF
chmod +x "$t/bin/gh"; export PATH="$t/bin:$t/sys"
cd "$t/repo"
sums() { (cd "$t" && find repo snap -path repo/.git -prune -o -type f -print0 | sort -z | xargs -0r sha256sum); }
start="$(sums)"; status="$(git status --porcelain)"

run() { # WANT ARGS...: run in the target repo, exit WANT, no traceback; output in $out
  local want="$1" rc; shift
  set +e; out="$("$L" "$@" 2>&1)"; rc=$?; set -e
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out"
  ! grep -q Traceback <<<"$out" || fail "'$*' printed a traceback: $out"
}
has() { grep -qF -- "$1" <<<"$out" || fail "${2:-output} lacks '$1': $out"; }
hasnt() { ! grep -qF -- "$1" <<<"$out" || fail "${2:-output} has '$1': $out"; }

# Passing parent: criteria ids (plain and backticked), demo last (wrapped lines, gate plus a real
# command), demos through each declared surface (tracked bin/ by name and path after an env
# assignment with $(...), `uv run app` from pyproject, a justfile recipe plus curl to a URL,
# pnpm exec playwright), and an Expand-contract ticket without a demo.
run 0 tickets 100
for n in 101 102 103 104 105 106 107; do has "$n: ok"; done; has "100: 7 of 7 tickets pass"
run 0 tickets '#100'

# #10's real body: layer-only-ticket and the fix; its sibling passes; exit 1.
run 1 tickets 8
has "10: class: layer-only-ticket: demo names no backticked command"
has "fix: end the acceptance list on \`demo: \` with a backticked command"
has "Expand-contract: expand|migrate|contract"
has "101: ok"; has "8: 1 of 2 tickets pass, 1 fail"
hasnt "10: class: unknown-criterion" "10's ids exist in the kit specs:"

# Each failing class.
run 1 tickets 20
has "21: class: no-criterion: no acceptance item names a criterion id; fix: start each item with the criterion it serves"
hasnt "21: class: layer-only"
has "22: class: unknown-criterion: demo#acceptance-zz: no anchor acceptance-zz in"
has "23: class: unknown-criterion: nospec#acceptance-a: no spec"
has "24: class: layer-only-ticket: demo is the gate alone (\`just check\`)"
has "25: class: no-criterion: no \`## Acceptance criteria\` section"
has "25: class: layer-only-ticket: last acceptance item is not a \`demo: \` line"
has "26: class: layer-only-ticket: last acceptance item is not a \`demo: \` line"
has "27: class: layer-only-ticket: Expand-contract line names \`maybe\`"
# The qc judge's draft (gh47 qc at 294ac1d), verbatim: a printf demo is no declared surface.
has "28: class: layer-only-ticket: demo runs no surface the repo declares (\`printf \"schema ready\\n\"\`: printf is not a program the repo declares)"
has "fix: make the demo a backticked command through the repo's own public surface (ADR 0009)"
has "33: class: layer-only-ticket: demo runs no surface the repo declares (\`tests/demo.sh\`: tests/demo.sh is a test or hook"
has "35: class: layer-only-ticket: demo runs no surface the repo declares (\`just qc\`: just qc runs qc, a gate or factory recipe, not the app; \`echo done\`: echo is not a program the repo declares)"
# The qc judge's second draft (gh47 qc at 4a95d10), verbatim: a persistence-only ticket whose demo runs
# a declared surface passes every fact; whether it is a real slice is review's, never a regex over
# What to build (deleted, #118, docs/adr/0008).
has "36: ok"
has "40: class: layer-only-ticket: demo runs no surface the repo declares (\`python3 -c"
# The qc judge's third draft (gh47 qc at 23f1a7a), verbatim: #47's body with a user-story anchor
# for the criterion id; only a data-acceptance-criterion anchor counts.
has "41: class: no-criterion: no acceptance item names an acceptance criterion: issue-lifecycle#story-tracer-tickets is not a data-acceptance-criterion anchor; fix: name the data-acceptance-criterion anchor it serves, e.g. issue-lifecycle#acceptance-"
hasnt "41: class: layer-only"
has "20: 1 of 13 tickets pass, 12 fail"
run 1 tickets 30; has "30: class: no-sub-issues"; has "fix: file each lane ticket as a sub-issue of 30"

# One draft: a file, stdin passing, stdin failing (#10), the waiver.
run 0 ticket "$F/101.md"; has "$F/101.md: ok"
set +e; out="$("$L" ticket - <"$F/101.md" 2>&1)"; rc=$?; set -e
[[ "$rc" == 0 && "$out" == "stdin: ok" ]] || fail "ticket - on a good draft: exit $rc: $out"
python3 -c 'import json,sys; sys.stdout.write(json.load(open(sys.argv[1]))["body"])' "$F/10.json" >"$t/10.md"
set +e; out="$("$L" ticket - <"$t/10.md" 2>&1)"; rc=$?; set -e
[[ "$rc" == 1 ]] || fail "ticket - on #10: exit $rc: $out"; has "stdin: class: layer-only-ticket"
run 0 ticket "$F/102.md"
run 1 ticket - <"$F/28-judge-printf.md"; [[ "$(grep -c '^stdin: class: ' <<<"$out")" == 1 ]] || fail "judge draft on stdin: $out"; has "stdin: class: layer-only-ticket: demo runs no surface the repo declares"
run 0 ticket "$F/104-uv-app.md"
run 1 ticket - <"$F/41-judge-story-anchor.md"; has "stdin: class: no-criterion: no acceptance item names an acceptance criterion"
printf '## What to build\n\n`demo a` greets.\n\n## Acceptance criteria\n\n- [ ] demo#acceptance: the section anchor\n- [ ] demo: `demo a` prints ok\n' >"$t/section.md"
run 1 ticket "$t/section.md"; has "demo#acceptance is not a data-acceptance-criterion anchor; fix: name the data-acceptance-criterion anchor it serves, e.g. demo#acceptance-a"
run 0 ticket - <"$F/36-judge-persistence.md"; has "stdin: ok"

# Rule tickets (spec #lanes-tickets; form: octo-feather-lane --help (ticket)).
run 0 tickets 70; has "108: ok"; has "70: 2 of 2 tickets pass"
rt() { printf '## What to build\n\nA rule fix.\n\n## Acceptance criteria\n\n%s\n' "$1" >"$t/rule.md"; }
for o in 'docs/adr/0017' 'docs/adr/0017-integration-is-a-script.md' 'ADR 0017' 'owner ruling 2026-10-23, #121' 'owner ruling #121'; do
  rt "- [ ] rule: integrate adds no integrate or qc recipe to a repo the kit did not create ($o)
- [ ] demo: \`demo a\` prints ok"; run 0 ticket "$t/rule.md"; [[ "$out" == "$t/rule.md: ok" ]] || fail "rule ticket ($o): $out"
done
rt "- [ ] demo#acceptance-a: x
- [ ] rule: a rule beside a criterion (ADR 0017)
- [ ] demo: \`demo a\` prints ok"; run 0 ticket "$t/rule.md"
rf="fix: write the rule item as \`rule: <rule> (<owner>)\`, owner kinds: octo-feather-lane --help (ticket)"
for c in 'integrate adds no recipe|`rule: integrate adds no recipe` names no owner in parentheses' \
         'integrate adds no recipe (docs/adr/9999)|owner `docs/adr/9999` names no ADR file in' \
         'integrate adds no recipe (ADR 0099)|owner `ADR 0099` names no ADR file in' \
         'integrate adds no recipe (docs/adr/0017-wrong-name.md)|owner `docs/adr/0017-wrong-name.md` names no ADR file in' \
         '(docs/adr/0017)|empty rule' '|empty rule' \
         'integrate adds no recipe (the supervisor)|owner `the supervisor` is neither an ADR nor an owner ruling' \
         'integrate adds no recipe (owner ruling)|owner `owner ruling` is neither an ADR nor an owner ruling'; do
  rt "- [ ] rule: ${c%%|*}
- [ ] demo: \`demo a\` prints ok"; run 1 ticket "$t/rule.md"
  has "$t/rule.md: class: unowned-rule: ${c#*|}"; has "$rf"; hasnt "class: no-criterion"; hasnt "ADR NNNN"; hasnt "owner ruling <"
done
rt "- [ ] demo#acceptance-a: x
- [ ] rule: no owner here
- [ ] demo: \`demo a\` prints ok"; run 1 ticket "$t/rule.md"; has "class: unowned-rule: \`rule: no owner here\` names no owner"
rt "- [ ] rule: integrate adds no recipe (docs/adr/0017)"; run 1 ticket "$t/rule.md"
has "$t/rule.md: class: layer-only-ticket: last acceptance item is not a \`demo: \` line"; hasnt "no-criterion"
rt "- [ ] rule: integrate adds no recipe (docs/adr/0017)
- [ ] demo: \`printf ok\`"; run 1 ticket "$t/rule.md"; has "class: layer-only-ticket: demo runs no surface the repo declares"
# Neither a criterion id nor a rule item: no-criterion, its fix naming both forms.
rt "- [ ] some item
- [ ] demo: \`demo a\` prints ok"; run 1 ticket "$t/rule.md"
has "class: no-criterion: no acceptance item names a criterion id; fix: start each item with the criterion it serves"
has "or, serving no criterion, add an item \`rule: <rule> (<owner>)\`, owner kinds: octo-feather-lane --help (ticket)"
hasnt "ADR NNNN"; hasnt "owner ruling <"
rm "$t/rule.md"; run 1 ticket - <<<"no section"
has "(or, serving no criterion, an item \`rule: <rule> (<owner>)\`, owner kinds: octo-feather-lane --help (ticket))"; hasnt "ADR NNNN"

# Interpreter-run scripts (owner: ADR 0002 fallback, #121 D11):
# this repo declares programs, so `python3 scripts/octo-feather-lane` (as in the kit) and harness.py are refused.
d11() { printf '## What to build\n\n`%s` checks.\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n- [ ] demo: `%s`\n' "$1" "$1" >"$t/d11.md"; }
for c in 'python3 scripts/octo-feather-lane' 'python harness.py' 'bash scripts/octo-feather-lane'; do
  d11 "$c"; run 1 ticket "$t/d11.md"; has "$t/d11.md: class: layer-only-ticket: demo runs no surface the repo declares (\`$c\`: "
  has "the repo declares a program"
done
run 1 ticket "$F/110-runnable-script.md"; has "uv run python harness.py score --json\`: the repo declares a program"
# A repo with no declared program (no executable, no recipe but its gate, no bin) demos through its script.
mkdir -p "$t/bare/docs/specs"; cp "$t/repo/docs/specs/demo.spec.html" "$t/bare/docs/specs/"; cp "$t/repo/harness.py" "$t/bare/"
printf 'check:\n    true\n' >"$t/bare/justfile"; git -C "$t/bare" init -q -b main . && git -C "$t/bare" add -A
(cd "$t/bare" && run 0 ticket "$F/110-runnable-script.md" && d11 'python harness.py' && run 0 ticket "$t/d11.md") || exit 1
# A module's gate is no declared program either: the script demo still passes (#172 final review).
mkdir -p "$t/bare/sub"; printf 'check:\n    true\n' >"$t/bare/sub/mod.just"; printf 'mod sub\n' >"$t/bare/justfile"; git -C "$t/bare" add -A
(cd "$t/bare" && JUST_UNSTABLE=1 run 0 ticket "$t/d11.md") || exit 1
# #172 (s20): a `just` demo passes exactly when `just --dump` lists the recipe (defaulted parameters,
# attribute lines, imports, aliases), never by a justfile header regex; gh136's install-check regression.
mkdir -p "$t/jrepo/docs/specs"; cp "$t/repo/docs/specs/demo.spec.html" "$t/jrepo/docs/specs/"
printf 'import "more.just"\nalias ic := install-check\nalias c := check\n\ncheck:\n    true\n\n[private]\nhidden:\n    true\n\n# doc\n[no-cd]\ninstall-check flag="x":\n    true\n\n@quiet a b="2" +rest="":\n    true\n' >"$t/jrepo/justfile"
printf 'demo:\n    true\n' >"$t/jrepo/more.just"; git -C "$t/jrepo" init -q -b main . && git -C "$t/jrepo" add -A
jd() { printf '## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n- [ ] demo: `%s` exits 0\n' "$1" >"$t/jd.md"; }
cd "$t/jrepo"
for c in 'just install-check' 'just install-check flag=y' 'just demo' 'just hidden' 'just ic' 'just quiet 1' 'just --yes demo'; do
  jd "$c"; run 0 ticket - <"$t/jd.md"; [[ "$out" == "stdin: ok" ]] || fail "$c: $out"
done
jd 'just nosuch'; run 1 ticket - <"$t/jd.md"; has "(\`just nosuch\`: just answers: error: Justfile does not contain recipe \`nosuch\`.)"
# A module recipe is `just MOD RECIPE`, as just runs it (just 1.21 runs modules only unstable, and refuses MOD::RECIPE).
mkdir -p "$t/jrepo/sub"; printf 'alias c := check\ninner:\n    true\ncheck:\n    true\n' >"$t/jrepo/sub/mod.just"; printf 'mod sub\n' >>"$t/jrepo/justfile"
jd 'just sub inner'; JUST_UNSTABLE=1 run 0 ticket - <"$t/jd.md"
# A module's gate, or a module alias to it, is the gate whatever path names it (#172 final review).
jd 'just sub check'; JUST_UNSTABLE=1 run 1 ticket - <"$t/jd.md"; has "(\`just sub check\`: just sub check runs check, a gate or factory recipe, not the app)"
jd 'just sub c'; JUST_UNSTABLE=1 run 1 ticket - <"$t/jd.md"; has "(\`just sub c\`: just sub c runs check, a gate or factory recipe, not the app)"
jd 'just sub::inner'; JUST_UNSTABLE=1 run 1 ticket - <"$t/jd.md"; has "(\`just sub::inner\`: just answers: error: Justfile does not contain recipe \`sub::inner\`.)"
sed -i '$d' "$t/jrepo/justfile"   # drop the mod line: the cases below run without JUST_UNSTABLE
jd 'just c'; run 1 ticket - <"$t/jd.md"; has "(\`just c\`: just c runs check, a gate or factory recipe, not the app)"
# Fails closed, never a fallback: a justfile just cannot read, or no just, is exit 2 naming why.
mkdir -p "$t/nojust"; cp -P "$t/sys"/* "$t/nojust/"; rm "$t/nojust/just"   # the hermetic PATH less just
jd 'just demo'; PATH="$t/nojust" run 2 ticket - <"$t/jd.md"; has "cannot read the justfile's recipes ($t/jrepo/justfile): just is not on PATH"; hasnt ": ok"
jd 'curl https://example.com'; PATH="$t/nojust" run 0 ticket - <"$t/jd.md"   # no just demo: justfile never read
printf 'broken (:\n' >>"$t/jrepo/justfile"
jd 'just demo'; run 2 ticket - <"$t/jd.md"; has "cannot read the justfile's recipes ($t/jrepo/justfile): just --dump: error:"; hasnt ": ok"
cd "$t/repo"
# #121 D17: criterion ids inside a <template>.
for a in acceptance-zz acceptance-zz2; do
  printf '## Acceptance criteria\n\n- [ ] zz#%s: x\n- [ ] demo: `demo a` prints ok\n' "$a" >"$t/d17.md"; run 1 ticket "$t/d17.md"
  has "class: unknown-criterion: zz#$a: no anchor $a in"; has "e.g. zz#acceptance-ok"
done
sed -i 's/zz#acceptance-zz2/zz#acceptance-ok/' "$t/d17.md"; run 0 ticket "$t/d17.md"
# #121 D18 D21 (#145): headings, items and an Expand-contract line in fenced code or an HTML comment;
# a fence inside the section.
for f in '```sh' '~~~' '````'; do
  e="${f%%sh}"
  printf '## Acceptance criteria\n\n%s\n# setup\n## Not a heading\n%s\n\n- [ ] demo#acceptance-a: ok\n- [ ] demo: `demo a` prints ok\n' "$f" "$e" >"$t/d18a.md"
  run 0 ticket "$t/d18a.md"
  printf '## What to build\n\nAn example:\n\n%s\n## Acceptance criteria\n\n- demo#acceptance-a: x\n%s\n\n## Acceptance criteria\n\n- [ ] demo#acceptance: the section\n- [ ] demo: `demo a` prints ok\n' "$f" "$e" >"$t/d18b.md"
  run 1 ticket "$t/d18b.md"; has "no acceptance item names an acceptance criterion: demo#acceptance is not"
  printf '## What to build\n\nA refactor step.\n\n%s\nExpand-contract: expand\n%s\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n' "$f" "$e" >"$t/d21.md"
  run 1 ticket "$t/d21.md"; has "class: layer-only-ticket: last acceptance item is not a \`demo: \` line"
done
# PR #140 review finding 2 (owner: markdown()'s scope, #145): 4-space indented backticks open no fence.
printf '## What to build\n\n    ```\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n- [ ] demo: `demo a` prints ok\n' >"$t/d18d.md"
run 0 ticket "$t/d18d.md"
printf '## What to build\n\n<!-- an example:\n## Acceptance criteria\n- demo#acceptance-a: x\n-->\n\n## Acceptance criteria\n\n- [ ] demo#acceptance: the section\n- [ ] demo: `demo a` prints ok\n' >"$t/d18c.md"
run 1 ticket "$t/d18c.md"; has "no acceptance item names an acceptance criterion: demo#acceptance is not"
for c in '<!--\nExpand-contract: expand\n-->' 'Draft <!-- note\nExpand-contract: expand\n-->' '  <!--\n- Expand-contract: expand -->'; do
  printf "## What to build\n\nA refactor step.\n\n$c\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n" >"$t/d21c.md"
  run 1 ticket "$t/d21c.md"; has "class: layer-only-ticket: last acceptance item is not a \`demo: \` line"
done

# #240 (owners: ADR 0009, ADR 0008): a demo through a command the ticket creates passes only when a
# `Creates:` line declares it exactly; every looser Creates or demo fails with its class and a fix naming the form.
cr() { # CREATES-LINES DEMO: a draft whose What to build holds the Creates lines and whose demo is DEMO
  printf '## What to build\n\nA new command.\n%s\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n- [ ] demo: `%s` prints ok\n' "$1" "$2"; }
cf="\`Creates: \`<path>\`\` or \`Creates: \`just <recipe>\`\`, form: octo-feather-lane --help (ticket)"
run 0 ticket - < <(cr $'\nCreates: `scripts/new-cmd`' 'scripts/new-cmd --json'); [[ "$out" == "stdin: ok" ]] || fail "Creates path: $out"
run 1 ticket - < <(cr '' 'scripts/new-cmd --json')
[[ "$(grep -c '^stdin: class: ' <<<"$out")" == 1 ]] || fail "no Creates: $out"
has "stdin: class: layer-only-ticket: demo runs no surface the repo declares (\`scripts/new-cmd --json\`: scripts/new-cmd is not an executable the repo tracks)"
has "$cf"
# ./ prefix, env and runner, list item and bold forms, repeated lines, a recipe, a path that already exists.
run 0 ticket - < <(cr $'\n- **Creates:** `./bin/x`\nCreates: `bin/x`' 'FOO=1 uv run ./bin/x a')
run 0 ticket - < <(cr $'\nCreates: `bin/x`\nCreates: `just new-recipe`' 'bin/x a && just --yes new-recipe b')
run 0 ticket - < <(cr $'\nCreates: `bin/demo`' 'bin/demo a')
# A module recipe the justfile lacks has no stand-in just can resolve: bad-creates, never a guess.
run 1 ticket - < <(cr $'\nCreates: `just sub new`' 'just sub new'); has "class: bad-creates: Creates \`just sub new\` is a module recipe the justfile lacks"
# In a fence or comment a Creates line is no declaration.
run 1 ticket - < <(cr $'\n```\nCreates: `bin/x`\n```\n<!-- Creates: `bin/x` -->' 'bin/x a'); has "class: layer-only-ticket"; hasnt "-creates"
# A Creates no demo command runs: a different path, a bare name (runs PATH, not the file), only as an argument.
for d in 'bin/y a' 'x a' 'bin/demo bin/x'; do
  run 1 ticket - < <(cr $'\nCreates: `bin/x`' "$d"); has "stdin: class: unused-creates: Creates \`bin/x\` but no demo command runs it; fix: "; has "$cf"
done
run 1 ticket - < <(cr $'\nCreates: `just new-recipe`' 'just other'); has "class: unused-creates: Creates \`just new-recipe\`"
# Malformed Creates: bad-creates, each naming its problem and the form.
for c in '`tests/new.sh`|`tests/new.sh` is under a test or hook directory' '`.githooks/x`|`.githooks/x` is under a test or hook directory' \
         '`just check`|`just check` is a gate or factory recipe' '`just check-fast`|`just check-fast` is a gate or factory recipe' \
         '`just integrate`|`just integrate` is a gate or factory recipe' '`just qc`|`just qc` is a gate or factory recipe' \
         '`just qa`|`just qa` is a gate or factory recipe' '`just sub check`|`just sub check` is a gate or factory recipe' \
         '`/usr/bin/x`|`/usr/bin/x` is not repo-relative' '`../x`|`../x` is not repo-relative' '`bin/../../x`|`bin/../../x` is not repo-relative' \
         '``|empty value' '`just`|empty value' 'bin/x|value `bin/x` is not one backticked path or `just <recipe>`' \
         '|value `` is not one backticked path or `just <recipe>`' '`bin/x` and more|value `` `bin/x` and more `` is not one backticked' \
         '`bin/x a`|`bin/x a` is not one path' '`bin//x`|`bin//x` is not a normalized path' '`just a:b`|`just a:b` is not one path'; do
  run 1 ticket - < <(cr $'\nCreates: '"${c%%|*}" 'bin/demo a'); has "stdin: class: bad-creates: "; has "${c#*|}"; has "; fix: "; has "$cf"
  hasnt "unused-creates"; hasnt "layer-only"
done
# A declared recipe that already exists as an alias to the gate is the gate.
printf 'alias c := check\n' >>justfile
run 1 ticket - < <(cr $'\nCreates: `just c`' 'just c'); has "class: bad-creates: Creates \`just c\` is a gate or factory recipe"
sed -i '$d' justfile
# #240 review: a declared recipe is the complete one just runs. A module prefix never stands for its gate
# (creates-recipe-prefix): the gate refusal holds and the declaration of the module itself is bad-creates.
printf 'check:\n    true\n' >sub.just; printf 'mod sub\n' >>justfile
JUST_UNSTABLE=1 run 1 ticket - < <(cr $'\nCreates: `just sub`' 'just sub check')
has "class: layer-only-ticket: demo runs no surface the repo declares (\`just sub check\`: just sub check runs check, a gate or factory recipe, not the app)"
has "class: bad-creates: Creates \`just sub\` is an existing module, not a recipe"; hasnt ": ok"
JUST_UNSTABLE=1 run 1 ticket - < <(cr $'\nCreates: `just sub new`' 'just sub new a'); has "class: bad-creates: Creates \`just sub new\` is a module recipe the justfile lacks"
sed -i '$d' justfile; rm sub.just
run 1 ticket - < <(cr $'\nCreates: `just serve x`' 'just serve x')
has "class: bad-creates: Creates \`just serve x\` goes through \`just serve\`, an existing recipe, not a module"
# #240 round 2: the recipes a just demo runs are just's own answer (check-gate-free just_runs: its argument
# parser, then its dry run, which names each recipe it runs), never a model of its options or arities.
# A parameter takes the word after it (serve port="8000"), a variadic takes every word (new *args).
printf 'new *args:\n    true\n\nrel: check\n    true\n\nv := "1"\n' >>justfile
run 0 ticket - < <(cr '' 'just serve check'); [[ "$out" == "stdin: ok" ]] || fail "just serve check: $out"
for d in 'just new check' 'just --shell-arg=-c new' 'just --shell-arg -c new a' 'just -v --set v 2 v=3 new' 'just --color=never --yes -- new a'; do
  run 0 ticket - < <(cr $'\nCreates: `just new`' "$d"); [[ "$out" == "stdin: ok" ]] || fail "$d: $out"
done
# A gate a recipe depends on runs too; an option just cannot dry-run with (-q) is just's answer, not a guess.
run 1 ticket - < <(cr '' 'just rel'); has "(\`just rel\`: just rel runs check, a gate or factory recipe, not the app)"
run 1 ticket - < <(cr $'\nCreates: `just new`' 'just -q new'); has "(\`just -q new\`: just answers: error: The argument '--quiet' cannot be used with '--dry-run'"
has "class: unused-creates: Creates \`just new\`"
# A subcommand that runs no recipe (show, list, command, a value option's operand) leaves the declaration
# unused, and asking just runs nothing: the --command demo touches no file, --fmt rewrites no justfile.
for d in 'just --show new' 'just -s new' 'just --justfile new check' 'just -f new check' 'just --list new' 'just --dump new' \
         'just --evaluate new' 'just --summary new' 'just -n new' 'just --dry-run new' 'just --command new' \
         "just --command touch $t/ran" "just -c touch $t/ran new" "just --command=touch $t/ran" 'just --fmt new' 'just --set new x serve'; do
  run 1 ticket - < <(cr $'\nCreates: `just new`' "$d"); has "class: unused-creates: Creates \`just new\` but no demo command runs it"
  has "just answers: error: "; [[ ! -e "$t/ran" ]] || fail "$d ran a command"
done
# A recipe the ticket creates gets a stand-in for every parameter count the words allow: the demo passes
# when every reading just runs is gate-free; `just fresh check` may run check (fresh with no parameter).
run 0 ticket - < <(cr $'\nCreates: `just fresh`' 'just fresh a b'); [[ "$out" == "stdin: ok" ]] || fail "fresh a b: $out"
run 0 ticket - < <(cr $'\nCreates: `just fresh`' 'just --shell-arg=-c fresh'); [[ "$out" == "stdin: ok" ]] || fail "fresh shell-arg: $out"
run 1 ticket - < <(cr $'\nCreates: `just fresh`' 'just fresh check')
has "(\`just fresh check\`: just fresh check runs check in a reading of a recipe the ticket creates, a gate or factory recipe, not the app)"; has "class: unused-creates: Creates \`just fresh\`"
git checkout -q justfile
# A created path stands for itself, never read as an interpreter or HTTP tool by its basename
# (creates-invocation-crash): it passes declared and run, and nothing prints a traceback (run asserts it).
for p in scripts/python scripts/curl bin/node bin/playwright; do
  run 0 ticket - < <(cr $'\nCreates: `'"$p"'`' "$p"); [[ "$out" == "stdin: ok" ]] || fail "$p: $out"
  run 0 ticket - < <(cr $'\nCreates: `'"$p"'`' "$p run x")
done
# The waiver: an Expand-contract ticket runs no demo, so its Creates is unused.
run 1 ticket - < <(printf 'Expand-contract: expand\nCreates: `bin/x`\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n')
has "class: unused-creates: Creates \`bin/x\` but no demo command runs it"

# The offline gh, serving the snapshot octo-feather-qc-ghsnap took, refused nothing: every field
# asked is one the snapshot CLI fetches.
[[ ! -s "$t/miss.log" ]] || fail "offline gh refused calls (a field the snapshot lacks?): $(cat "$t/miss.log")"

# Execution failures: exit 2, the fix named, no ticket reported as passed.
err() { # WANT_MSG ARGS...
  local msg="$1"; shift; run 2 "$@"; has "$msg" "'$*'"; hasnt ": ok" "'$*'"; hasnt "tickets pass" "'$*'"; }
err "tracker script github-issues/issue-view 199 failed" tickets 60   # sub-issue missing midway: 101 was read, not reported
has "fix the cause it names"
err "gh returned a partial or unreadable sub-issue list" tickets 50
FAKE_GH=down err "error connecting to api.github.com" tickets 100
FAKE_GH=garbage err "issue-view: #100: gh returned a partial or unreadable sub-issue list" tickets 100
PATH="$t/sys" err "gh: command not found" tickets 100
err "usage: octo-feather-lane tickets PARENT" tickets
err "usage: octo-feather-lane tickets PARENT" tickets 100 --repo x/y
err "abc is not a GitHub issue key" tickets abc
err "usage: octo-feather-lane ticket FILE|-" ticket
err "cannot read draft $t/nope.md" ticket "$t/nope.md"
printf '\xff\xfe\n' >"$t/bin.md"; err "cannot read draft $t/bin.md" ticket "$t/bin.md"
set +e; out="$("$L" ticket - </dev/null 2>&1)"; rc=$?; set -e
[[ "$rc" == 2 ]] && grep -qF "draft - is empty" <<<"$out" || fail "empty stdin: exit $rc: $out"
mkdir -p "$t/elsewhere"; cd "$t/elsewhere"
err "no spec dir $t/elsewhere/docs/specs: run this inside the target repo" tickets 100
err "no spec dir" ticket "$F/101.md"
cd "$t/repo"

# A Linear target: the same checks through the linear tracker skill's issue-view, against the fake linear.
LI="$kit/.agents/skills/linear/scripts"
cp -r "$t/repo" "$t/lrepo"; echo 'tracker = "linear"' >"$t/lrepo/.octo-feather.toml"
python3 - "$F" "$t/store.json" <<'PY'
import json, sys, pathlib
F = pathlib.Path(sys.argv[1])
b101 = (F / "101.md").read_text(); b10 = json.loads((F / "10.json").read_text())["body"]
def i(t, d, parent=None, state="Todo"): return {"title": t, "description": d, "state": state, "parent": parent, "blocked_by": []}
pathlib.Path(sys.argv[2]).write_text(json.dumps({"workspace": "acme", "issues": {
  "ENG-123": i("Lane", "parent"), "ENG-124": i("Pass", b101, "ENG-123"), "ENG-125": i("Layer only", b10, "ENG-123"),
  "ENG-200": i("Lane 2", "parent"), "ENG-210": i("Pass", b101, "ENG-200"), "ENG-201": i("Pass", b101, "ENG-200", "Done"),
  "ENG-300": i("Empty", "parent")}}))
PY
cd "$t/lrepo"; : >"$GH_LOG"
OCTO_FEATHER_LINEAR_STORE="$t/store.json" PATH="$LI:$PATH" run 1 tickets ENG-123
has "ENG-124: ok"; has "ENG-125: class: layer-only-ticket: demo names no backticked command"; has "ENG-123: 1 of 2 tickets pass, 1 fail"
OCTO_FEATHER_LINEAR_STORE="$t/store.json" PATH="$LI:$PATH" run 0 tickets eng-200
[[ "$out" == $'ENG-201: ok\nENG-210: ok\nENG-200: 2 of 2 tickets pass' ]] || fail "linear tickets eng-200, in key order: $out"
OCTO_FEATHER_LINEAR_STORE="$t/store.json" PATH="$LI:$PATH" run 1 tickets ENG-300; has "ENG-300: class: no-sub-issues"
OCTO_FEATHER_LINEAR_STORE="$t/store.json" PATH="$LI:$PATH" err "tracker script linear/issue-view ENG-999 failed" tickets ENG-999
OCTO_FEATHER_LINEAR_STORE="$t/store.json" PATH="$LI:$PATH" err "100 is not a Linear issue key" tickets 100
[[ ! -s "$GH_LOG" ]] || fail "a Linear target's tickets ran gh: $(cat "$GH_LOG")"
cd "$t/repo"

# Read-only: no run wrote to the repo or the snapshot.
[[ "$(sums)" == "$start" ]] || fail "a run changed files under the repo or snapshot"
[[ "$(git status --porcelain)" == "$status" ]] || fail "repo changed: $(git status --porcelain)"
echo "lane-tickets: ok (hermetic PATH, no host gh; snapshot taken by octo-feather-qc-ghsnap from a fake GitHub, served by the offline gh, nothing refused; all pass incl. demos via tracked bin, uv run app, just recipe + curl URL, playwright, a runnable script by its interpreter (uv run python harness.py) ; #121 D11 D17 D18 D21 cases; #172 just recipes as just --dump lists them (defaulted parameter, attribute, import, alias, alias to the gate, module gate, module alias to its gate, module gate as no program, no such recipe, no just, unreadable justfile); #10 layer-only-ticket with fix, no criterion, unknown anchor and spec, gate-only demo, demo not last, qc judge printf draft, test-script demo, persistence-only draft passes the facts, inline python, story or section anchor as criterion, factory recipe, bad and good Expand-contract; #240 Creates path and recipe pass, undeclared, unused, malformed, test, gate and alias-to-gate Creates fail, module prefix never its gate, non-running just options leave it unused and run nothing, just demos as just itself runs them (parameter, variadic, running options, a dependency gate, -q refused, stand-in readings of a created recipe), created python/curl paths pass; rule tickets by ADR path, ADR number and owner ruling pass, unowned, unknown ADR, empty rule, other owner and demo-less rule tickets fail; ticket file and stdin; gh down, missing, bad JSON, ticket missing midway, paged sub-issues, --repo refused, no specs, unreadable or empty draft, usage: exit 2, nothing passed, no traceback, no file written; Linear target through the fake linear: pass, fail, key order, no sub-issues, unknown and wrong-tracker key, no gh)"
