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
# class; a demo passes only through a surface the repo declares (tracked executable, justfile
# recipe, pyproject/package.json bin, HTTP URL, UI driver), so the qc judge's printf draft and
# a test script fail; checks are facts only, never prose meaning (the qc judge's persistence-only
# draft passes: whether its demo shows the behavior What to build describes is review's, #118); an Expand-contract ticket passes without a
# demo; a script run by its interpreter demos only a repo declaring no program (ADR 0002); <template> content, fenced code
# and HTML comments hold no criterion, heading or Expand-contract line (#121 D11 D17 D18 D21); `ticket -` checks stdin. Hermetic: PATH is built here, so no host gh is reachable. Errors
# (gh down, gh missing, bad JSON, missing ticket midway, paged sub-issues, no specs, unreadable
# draft, usage) exit 2 naming the fix, no traceback, nothing reported as passed, no file
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
for c in bash python3 git env sha256sum find sort xargs grep sed cut tr cat chmod rm mkdir cp ls id dirname jq head; do
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
printf '[project]\nname = "app"\n\n[project.scripts]\napp = "app.cli:main"\n' >"$t/repo/pyproject.toml"
# zz: criteria only inside an inert <template> (nested too) are no elements of the page; acceptance-ok is one.
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
parents = {100: [101, 102, 103, 104, 105, 106, 107], 8: [10, 101], 20: [21, 22, 23, 24, 25, 26, 27, 28, 33, 35, 36, 40, 41], 30: [], 50: ([101], 3), 60: [101, 199]}
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
has "35: class: layer-only-ticket: demo runs no surface the repo declares (\`just qc\`: just qc is a gate or factory recipe, not the app; \`echo done\`: echo is not a program the repo declares)"
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

# A tracked script run by its interpreter demos only a target with no CLI, HTTP or UI (ADR 0002, #121 D11):
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
# A criterion id is the data-anchor of a data-acceptance-criterion element; <template> content is none (#121 D17).
for a in acceptance-zz acceptance-zz2; do
  printf '## Acceptance criteria\n\n- [ ] zz#%s: x\n- [ ] demo: `demo a` prints ok\n' "$a" >"$t/d17.md"; run 1 ticket "$t/d17.md"
  has "class: unknown-criterion: zz#$a: no anchor $a in"; has "e.g. zz#acceptance-ok"
done
sed -i 's/zz#acceptance-zz2/zz#acceptance-ok/' "$t/d17.md"; run 0 ticket "$t/d17.md"
# Headings, items and the Expand-contract line inside fenced code or an HTML comment do not count;
# a fence inside the section does not end it (#121 D18, D21).
for f in '```sh' '~~~' '````'; do
  e="${f%%sh}"
  printf '## Acceptance criteria\n\n%s\n# setup\n## Not a heading\n%s\n\n- [ ] demo#acceptance-a: ok\n- [ ] demo: `demo a` prints ok\n' "$f" "$e" >"$t/d18a.md"
  run 0 ticket "$t/d18a.md"
  printf '## What to build\n\nAn example:\n\n%s\n## Acceptance criteria\n\n- demo#acceptance-a: x\n%s\n\n## Acceptance criteria\n\n- [ ] demo#acceptance: the section\n- [ ] demo: `demo a` prints ok\n' "$f" "$e" >"$t/d18b.md"
  run 1 ticket "$t/d18b.md"; has "no acceptance item names an acceptance criterion: demo#acceptance is not"
  printf '## What to build\n\nA refactor step.\n\n%s\nExpand-contract: expand\n%s\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n' "$f" "$e" >"$t/d21.md"
  run 1 ticket "$t/d21.md"; has "class: layer-only-ticket: last acceptance item is not a \`demo: \` line"
done
printf '## What to build\n\n<!-- an example:\n## Acceptance criteria\n- demo#acceptance-a: x\n-->\n\n## Acceptance criteria\n\n- [ ] demo#acceptance: the section\n- [ ] demo: `demo a` prints ok\n' >"$t/d18c.md"
run 1 ticket "$t/d18c.md"; has "no acceptance item names an acceptance criterion: demo#acceptance is not"
for c in '<!--\nExpand-contract: expand\n-->' 'Draft <!-- note\nExpand-contract: expand\n-->' '  <!--\n- Expand-contract: expand -->'; do
  printf "## What to build\n\nA refactor step.\n\n$c\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n" >"$t/d21c.md"
  run 1 ticket "$t/d21c.md"; has "class: layer-only-ticket: last acceptance item is not a \`demo: \` line"
done
printf '## What to build\n\nA refactor step. `<!--` opens no comment in code.\nExpand-contract: expand\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n' >"$t/d21ok.md"
run 0 ticket "$t/d21ok.md"
printf '## What to build\n\nNot closed before the blank line: <!--\n\nExpand-contract: expand\n\n-->\n\n## Acceptance criteria\n\n- [ ] demo#acceptance-a: x\n' >"$t/d21ok.md"
run 0 ticket "$t/d21ok.md"

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
echo "lane-tickets: ok (hermetic PATH, no host gh; snapshot taken by octo-feather-qc-ghsnap from a fake GitHub, served by the offline gh, nothing refused; all pass incl. demos via tracked bin, uv run app, just recipe + curl URL, playwright, a runnable script by its interpreter (uv run python harness.py) only in a repo declaring no program; interpreter-run scripts refused where the repo declares one; <template> criteria unknown; fenced (backtick or tilde, 3 or 4) or HTML-commented headings, items and Expand-contract lines ignored, a fence inside the section keeps it; #10 layer-only-ticket with fix, no criterion, unknown anchor and spec, gate-only demo, demo not last, qc judge printf draft, test-script demo, persistence-only draft passes the facts, inline python, story or section anchor as criterion, factory recipe, bad and good Expand-contract; ticket file and stdin; gh down, missing, bad JSON, ticket missing midway, paged sub-issues, --repo refused, no specs, unreadable or empty draft, usage: exit 2, nothing passed, no traceback, no file written; Linear target through the fake linear: pass, fail, key order, no sub-issues, unknown and wrong-tracker key, no gh)"
