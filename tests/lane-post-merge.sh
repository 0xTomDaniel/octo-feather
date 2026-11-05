#!/usr/bin/env bash
# Integration test for scripts/octo-feather-lane post-merge, the director's post-merge routine (owner ruling
# 2026-10-29 on issue 206; steps 1-2, issue 396), offline: a fake gh on PATH holds PR #7 and the push runs of
# its merge commit, and logs every call. Step 1 stops, exit 1, on a PR not merged and on one merged at another
# head; step 2 stops on a red run naming its URL, on no run within the --wait bound, and on a watch that fails
# with its run unfinished; all runs concluded success passes. Every run ends with a one-line summary of each
# step's outcome, and only gh reads run (rerun safe). Step 3 (issue 397) refreshes a throwaway kit install clone
# (OCTO_FEATHER_KIT_INSTALL, always set here: never the live kit), its origin a local bare repo behind a GitHub URL;
# fake mise, just, uv and pnpm log each call. Step 4 (issue 398, tests/lane-post-merge-tell.sh) reads a throwaway
# state dir (XDG_STATE_HOME) with no lane record here, so it tells no pane; step 5 (issue 399,
# tests/lane-post-merge-teardown.sh) finds no archived record, so it is pending and a green run exits 3. Run by `just check`.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
L="$kit/scripts/octo-feather-lane"
t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
fail() { echo "lane-post-merge test: $*" >&2; exit 1; }
export HOME="$t/home" XDG_STATE_HOME="$t/state" GH_LOG="$t/gh.log" GH_STORE="$t/gh.json" GH_LISTS="$t/lists" TOOL_LOG="$t/tools.log"
export OCTO_FEATHER_KIT_INSTALL="$t/kit" GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
unset GH_REPO GH_TOKEN TOOL_FAIL HERDR_SESSION
mkdir -p "$HOME" "$t/bin" "$t/target"
git -C "$t/target" init -q   # the director's target repo, the current directory of every run
cd "$t/target"
# Fake gh: pr view from .pr; run list (only --commit <full merge sha> --event push) answers its Nth call with
# .lists[N] (the last one repeated); run watch exits .watch[id] (default 0); api repos/<repo>/git/trees/<sha> (the no-CI
# fact) answers from .trees; anything else is refused.
cat > "$t/bin/gh" <<'EOF'
#!/usr/bin/env python3
import json, os, re, sys
a = sys.argv[1:]; open(os.environ["GH_LOG"], "a").write(" ".join(a) + "\n")
db = json.load(open(os.environ["GH_STORE"]))
def opt(f): return a[a.index(f) + 1] if f in a else None
if a[:3] == ["pr", "view", "7"]:
    print(json.dumps({k: db["pr"][k] for k in opt("--json").split(",")})); sys.exit(0)
if a[:2] == ["run", "list"]:
    n = len(open(os.environ["GH_LISTS"]).read()) if os.path.exists(os.environ["GH_LISTS"]) else 0
    open(os.environ["GH_LISTS"], "a").write("x")
    ok = opt("--commit") == db["pr"]["mergeCommit"]["oid"] and opt("--event") == "push"
    runs = db["lists"][min(n, len(db["lists"]) - 1)] if ok else []
    print(json.dumps([{k: r[k] for k in opt("--json").split(",")} for r in runs])); sys.exit(0)
if a[:2] == ["repo", "view"] and opt("--json") == "nameWithOwner":   # no repo: this directory's, o/r
    r = a[2] if a[2] != "--json" else "o/r"
    print(json.dumps({"nameWithOwner": r.removeprefix("https://github.com/").removesuffix(".git")})); sys.exit(0)
if a[0] == "api" and (m := re.fullmatch(r"repos/(?:o/r|\{owner\}/\{repo\})/git/trees/(\w+)", a[1])) and m[1] in db["trees"]:
    print(json.dumps({"sha": m[1], "tree": [dict(zip(("path", "type", "sha"), x)) for x in db["trees"][m[1]]]})); sys.exit(0)
if a[:2] == ["run", "watch"] and "--exit-status" in a:
    rc = db.get("watch", {}).get(a[2], 0)
    print(f"Run {a[2]} watched", file=sys.stderr if rc else sys.stdout); sys.exit(rc)
print(f"fake gh: refused {' '.join(a)}", file=sys.stderr); sys.exit(1)
EOF
chmod +x "$t/bin/gh"
# Fake refresh tools: log `<tool> <args> @ <cwd>`; the one TOOL_FAIL names (`uv sync`) fails, exit 3. With PY_MISSING
# set, the install's pinned Python is absent, as uv 0.13 answers it: uv sync downloads it (logged `download <pin>`)
# unless UV_PYTHON_DOWNLOADS=never, then fails in uv's words, exit 2; uv python find fails likewise.
cat > "$t/bin/tool" <<'EOF'
#!/usr/bin/env bash
c="$(basename "$0") $*"; echo "$c @ $PWD" >> "$TOOL_LOG"
[[ "$c" != "mise -C "*" ls --local --json" ]] || { printf '{"just": [{"source": {"path": "%s/mise.toml"}}]}\n' "$2"; exit 0; }   # the install's own tools
if [[ -n "${TOOL_FAIL:-}" && "$c" == "$TOOL_FAIL"* ]]; then echo "progress" ; echo "boom: $c" >&2; exit 3; fi
if [[ -n "${PY_MISSING:-}" && ( "$c" == "uv sync"* || "$c" == "uv python find"* ) ]]; then
  pin="$(cat .python-version)"
  if [[ "$c" == "uv sync"* && "${UV_PYTHON_DOWNLOADS:-}" != never ]]; then echo "download $pin" >> "$TOOL_LOG"
  else echo "error: No interpreter found for Python $pin in managed installations or search path" >&2; exit 2; fi
fi
echo "$c done"
EOF
chmod +x "$t/bin/tool"; for x in mise just uv pnpm; do ln -s tool "$t/bin/$x"; done
# The kit's origin: B, then M (the merge commit), then P past it with a mise.toml.
git init -q --bare -b main "$t/origin.git"; git clone -q "$t/origin.git" "$t/seed" 2>/dev/null
echo 3.11.7 > "$t/seed/.python-version"; git -C "$t/seed" add .python-version   # the pin, not the box's
for f in a m mise.toml; do touch "$t/seed/$f"; git -C "$t/seed" add "$f"; git -C "$t/seed" commit -qm "$f"; done
git -C "$t/seed" push -q origin HEAD:main
B="$(git -C "$t/seed" rev-parse HEAD~2)" M="$(git -C "$t/seed" rev-parse HEAD~1)" P="$(git -C "$t/seed" rev-parse HEAD)"
install() { # AT [REPO]: a fresh install clone detached at AT, origin https://github.com/REPO.git (default o/r)
  rm -rf "$t/kit"; git clone -q "$t/origin.git" "$t/kit"; git -C "$t/kit" checkout -q --detach "$1"
  git -C "$t/kit" remote set-url origin "https://github.com/${2:-o/r}.git"
  git -C "$t/kit" config "url.$t/origin.git.insteadOf" "https://github.com/${2:-o/r}.git"; : > "$TOOL_LOG"
}
install "$B" o/kit   # steps 1-2 below: the PR's repo is not the install's, step 3 leaves it unchanged
H=1234567890abcdef1234567890abcdef12345678
store() { # STATE HEAD LISTS-JSON [WATCH-JSON]; env WF: the merge commit's .github/workflows entries, JSON
  # [[name, type]...] (default a check.yml), or null for no .github at all
  jq -n --arg s "$1" --arg h "$2" --arg m "$M" --argjson l "$3" --argjson w "${4:-{\}}" --argjson wf "${WF-[[\"check.yml\", \"blob\"]]}" \
    '{pr: {state: $s, headRefOid: $h, mergeCommit: (if $s == "MERGED" then {oid: $m} else null end),
           baseRefName: "main", headRefName: "gh7"}, lists: $l, watch: $w,
      trees: (if $wf == null then {($m): [["README.md", "blob", "r"]]}
              else {($m): [["README.md", "blob", "r"], [".github", "tree", "g"]], g: [["workflows", "tree", "w"]],
                    w: [$wf[] | . + ["b"]]} end)}' > "$GH_STORE"
  rm -f "$GH_LISTS"; : > "$GH_LOG"
}
run1() { # name status conclusion id
  jq -nc --arg n "$1" --arg s "$2" --arg c "$3" --argjson i "$4" \
    '{databaseId: $i, status: $s, conclusion: $c, workflowName: $n, url: "https://github.com/o/r/actions/runs/\($i)"}'
}
run() { # WANT ARGS...: octo-feather-lane with the fake gh first on PATH
  local want="$1" rc; shift
  set +e; out="$(PATH="$t/bin:$PATH" "$L" "$@" 2>"$t/err")"; rc=$?; set -e; err="$(cat "$t/err")"
  [[ "$rc" == "$want" ]] || fail "'$*' want exit $want, got $rc: $out $err"
  ! grep -q Traceback <<<"$err" || fail "'$*' printed a traceback: $err"
  last="$(tail -n1 <<<"$out")"
  ! grep -qv '^\(pr view\|run list\|run watch\|repo view\|api repos/[^ ]*/git/trees/[^ ]*$\)' "$GH_LOG" || fail "'$*' ran a gh write: $(cat "$GH_LOG")"
}
green="$(run1 check completed success 11)" lint="$(run1 lint completed success 12)"
red="$(run1 check completed failure 13)" busy="$(run1 check in_progress '' 11)"

# Step 1: not merged, merged at another head, gh failing: stop at step 1, step 2 not run, no run list.
store OPEN "$H" "[[$green]]"
run 1 post-merge 7 "${H:0:7}" --lane gh7
[[ "$out" == *"step 1 merged: stopped: PR #7 is OPEN, not merged"* ]] || fail "not merged: $out"
[[ "$last" == "post-merge gh7 PR #7: step 1 merged stopped; step 2 main CI not run; step 3 kit refresh not run; step 4 tell supervisors not run; step 5 teardown not run" ]] || fail "not merged summary: $last"
! grep -q '^run ' "$GH_LOG" || fail "not merged still listed runs: $(cat "$GH_LOG")"
store MERGED "abcdef0$H" "[[$green]]"
run 1 post-merge 7 "${H:0:12}" --lane gh7
[[ "$out" == *"step 1 merged: stopped: PR #7 merged at head abcdef012345, not at the pinned head ${H:0:12}"* ]] || fail "other head: $out"
[[ "$last" == "post-merge gh7 PR #7: step 1 merged stopped; step 2 main CI not run; step 3 kit refresh not run; step 4 tell supervisors not run; step 5 teardown not run" ]] || fail "other head summary: $last"
run 1 post-merge 8 "$H" --lane gh7
[[ "$out" == *"step 1 merged: stopped: gh pr view 8 failed"* && "$last" == *"step 1 merged stopped"* ]] || fail "gh failing: $out"

# Step 2 green: a run in progress is watched to its end, a second workflow joins; every run success: exit 0.
store MERGED "$H" "[[$busy], [$green, $lint]]"
run 3 post-merge 7 "$H" --lane gh7 --repo o/r
[[ "$(head -n1 <<<"$out")" == "step 1 merged: ok: PR #7 (gh7) merged into main at head ${H:0:12}, merge commit ${M:0:12}" ]] || fail "step 1 line: $out"
[[ "$out" == *"step 2 main CI: ok: 2 push runs on ${M:0:12} concluded success: check https://github.com/o/r/actions/runs/11, lint https://github.com/o/r/actions/runs/12"* ]] || fail "green line: $out"
[[ "$out" == *"step 3 kit refresh: ok: kit install unchanged: PR in o/r, install is o/kit"* ]] || fail "other repo: $out"
[[ "$out" == *"step 4 tell supervisors: ok: no other open lane in $t/state/octo-feather/lanes to tell"* ]] || fail "step 4: $out"
[[ "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI ok; step 3 kit refresh ok; step 4 tell supervisors ok; step 5 teardown pending" ]] || fail "green summary: $last"
[[ "$(git -C "$t/kit" rev-parse HEAD)" == "$B" && ! -s "$TOOL_LOG" ]] || fail "other repo moved or refreshed the install"
grep -qx "run watch 11 --exit-status -R o/r" "$GH_LOG" || fail "running run not watched with --exit-status in o/r: $(cat "$GH_LOG")"
grep -qx "pr view 7 --json state,headRefOid,mergeCommit,baseRefName,headRefName -R o/r" "$GH_LOG" || fail "pr view: $(cat "$GH_LOG")"
[[ "$(wc -l <<<"$out")" == 6 ]] || fail "green prints one line per step and the summary: $out"
run 3 post-merge 7 "$H" --lane gh7 --repo o/r   # rerun: same result, still reads only
[[ "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI ok; step 3 kit refresh ok; step 4 tell supervisors ok; step 5 teardown pending" ]] || fail "rerun: $out"

# A run that appears within the bound is waited for.
store MERGED "$H" "[[], [$green]]"
run 3 post-merge 7 "$H" --lane gh7 --wait 1
[[ "$out" == *"step 2 main CI: ok: 1 push run on ${M:0:12} concluded success"* ]] || fail "late run: $out"

# Step 2 red: one run failed: stop naming its URL, never healthy.
store MERGED "$H" "[[$red, $lint]]" '{"13": 1}'
run 1 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 2 main CI: stopped: main CI red on ${M:0:12}: check failure https://github.com/o/r/actions/runs/13"* ]] || fail "red: $out"
[[ "$out" != *"concluded success"* && "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI stopped; step 3 kit refresh not run; step 4 tell supervisors not run; step 5 teardown not run" ]] || fail "red summary: $out"
# A watch that fails while its run reads unfinished: stop naming it, never healthy.
store MERGED "$H" "[[$busy]]" '{"11": 1}'
run 1 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 2 main CI: stopped: gh run watch 11 failed"*"https://github.com/o/r/actions/runs/11"* ]] || fail "watch failed: $out"
# No run within the bound: stop naming it.
store MERGED "$H" "[[]]"
run 1 post-merge 7 "$H" --lane gh7 --wait 0
[[ "$out" == *"step 2 main CI: stopped: no push run on merge commit ${M:0:12} within 0s, its workflows .github/workflows/check.yml"* ]] || fail "no run: $out"
[[ "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI stopped; step 3 kit refresh not run; step 4 tell supervisors not run; step 5 teardown not run" ]] || fail "no run summary: $last"
# A workflow file of either suffix, beside other files, still means CI: no run within the bound stops.
WF='[["deploy.yaml", "blob"], ["README.md", "blob"], ["ci", "tree"]]' store MERGED "$H" "[[]]"
run 1 post-merge 7 "$H" --lane gh7 --wait 0 --repo o/r
[[ "$out" == *"stopped: no push run on merge commit ${M:0:12} within 0s, its workflows .github/workflows/deploy.yaml:"* ]] || fail "yaml workflow: $out"
grep -qx "api repos/o/r/git/trees/$M" "$GH_LOG" || fail "--repo tree read: $(cat "$GH_LOG")"

# The no-CI fact (issue 569, owner ruling 2026-10-29 on issue 206): no run listed and no workflow file in the merge
# commit's tree (no .github; .github/workflows with no .yml or .yaml file): step 2 ok at once naming the fact and its
# source, one run list and no wait (a --wait bound that would stop a CI repo), steps 3-5 run; a rerun gives the same.
noci="step 2 main CI: ok: no CI: no workflow file under .github/workflows at merge commit ${M:0:12} (gh api repos/<this repo>/git/trees/${M:0:12}), so no push run can appear; nothing to wait for"
for wf in null '[["README.md", "blob"], ["ci.yml.off", "blob"], ["old.yml", "tree"]]' null; do
  WF="$wf" store MERGED "$H" "[[]]"
  run 3 post-merge 7 "$H" --lane gh7 --wait 1
  grep -qxF "$noci" <<<"$out" || fail "no CI ($wf): $out"
  [[ "$last" == "post-merge gh7 PR #7: step 1 merged ok; step 2 main CI ok; step 3 kit refresh ok; step 4 tell supervisors ok; step 5 teardown pending" ]] || fail "no CI summary: $out"
  [[ "$(grep -c '^run ' "$GH_LOG")" == 1 ]] || fail "no CI listed runs again or watched: $(cat "$GH_LOG")"
done

# Step 3, the PR's repo is the install's (o/r). Behind: fetch, fast-forward to M, still detached; no mise.toml at M,
# so no mise; each refresh command runs in the install, install-check for the target repo.
k() { git -C "$t/kit" "$@"; }
s3="post-merge gh7 PR #7: step 1 merged ok; step 2 main CI ok; step 3 kit refresh"
refresh="just vendored-fetch @ $t/kit
uv sync --locked @ $t/kit
pnpm install --frozen-lockfile @ $t/kit
just install-check $t/target @ $t/kit"
store MERGED "$H" "[[$green]]"; install "$B"
run 3 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 3 kit refresh: ok: kit install $t/kit fast-forwarded ${B:0:12}..${M:0:12}; just vendored-fetch ok; uv sync --locked ok; pnpm install --frozen-lockfile ok; just install-check $t/target ok (no mise.toml: mise install skipped)"* ]] || fail "behind: $out"
[[ "$last" == "$s3 ok; step 4 tell supervisors ok; step 5 teardown pending" && "$(k rev-parse HEAD)" == "$M" ]] || fail "behind did not reach M: $out"
! k symbolic-ref -q HEAD >/dev/null || fail "behind install left detached HEAD: $(k symbolic-ref HEAD)"
[[ "$(cat "$TOOL_LOG")" == "$refresh" ]] || fail "behind refresh calls: $(cat "$TOOL_LOG")"
# Rerun: no move, the refresh commands run again.
: > "$TOOL_LOG"; run 3 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 3 kit refresh: ok: kit install $t/kit at ${M:0:12}, at or past ${M:0:12}: no move; just vendored-fetch ok"* && "$(k rev-parse HEAD)" == "$M" ]] || fail "rerun: $out"
[[ "$(cat "$TOOL_LOG")" == "$refresh" ]] || fail "rerun refresh calls: $(cat "$TOOL_LOG")"
# Past M, with a mise.toml there: no move, the install of the kit's own locked tools first (only the tools its
# mise.toml requests, #493 AC5).
install "$P"; run 3 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 3 kit refresh: ok: kit install $t/kit at ${P:0:12}, at or past ${M:0:12}: no move; octo-feather-mise-install . ok; just vendored-fetch ok"* && "$(k rev-parse HEAD)" == "$P" ]] || fail "past: $out"
[[ "$(cat "$TOOL_LOG")" == "mise -C $t/kit ls --local --json @ $t/kit"$'\n'"mise -C $t/kit install --locked just @ $t/kit"$'\n'"$refresh" ]] || fail "past refresh calls: $(cat "$TOOL_LOG")"
# A failing refresh command stops naming it; later ones do not run.
install "$B"; TOOL_FAIL="uv sync" run 1 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 3 kit refresh: stopped: kit install $t/kit fast-forwarded ${B:0:12}..${M:0:12}; just vendored-fetch ok; uv sync --locked failed (exit 3: boom: uv sync --locked)"* ]] || fail "failing tool: $out"
[[ "$last" == "$s3 stopped; step 4 tell supervisors not run; step 5 teardown not run" && "$(cat "$TOOL_LOG")" != *pnpm* ]] || fail "failing tool ran on: $out $(cat "$TOOL_LOG")"
# The pinned Python absent: uv sync never downloads it, and the stop names the install command for the pin.
install "$B"; PY_MISSING=1 run 1 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 3 kit refresh: stopped: kit install $t/kit fast-forwarded ${B:0:12}..${M:0:12}; just vendored-fetch ok; uv sync --locked failed (exit 2: error: No interpreter found for Python 3.11.7 in managed installations or search path): the kit's pinned Python 3.11.7 (.python-version) is not installed and post-merge never downloads one: run \`uv python install --no-bin 3.11.7\` in $t/kit, then rerun"* ]] || fail "missing pin: $out"
[[ "$last" == "$s3 stopped; step 4 tell supervisors not run; step 5 teardown not run" ]] || fail "missing pin summary: $last"
! grep -q -e '^download' -e '^pnpm' "$TOOL_LOG" || fail "missing pin downloaded or ran on: $(cat "$TOOL_LOG")"
# Dirty: stop naming it, nothing changed (HEAD, the file, no refresh).
install "$B"; echo x > "$t/kit/stray"; run 1 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 3 kit refresh: stopped: kit install $t/kit is dirty (?? stray)"* && "$last" == "$s3 stopped; step 4 tell supervisors not run; step 5 teardown not run" ]] || fail "dirty: $out"
[[ "$(k rev-parse HEAD)" == "$B" && -f "$t/kit/stray" && ! -s "$TOOL_LOG" ]] || fail "dirty install changed"
# Diverged: a local commit off B; stop naming it, nothing changed.
install "$B"; touch "$t/kit/d"; k add d; k commit -qm d; D="$(k rev-parse HEAD)"; run 1 post-merge 7 "$H" --lane gh7
[[ "$out" == *"step 3 kit refresh: stopped: kit install $t/kit at ${D:0:12} has diverged from merge commit ${M:0:12}"* && "$last" == "$s3 stopped; step 4 tell supervisors not run; step 5 teardown not run" ]] || fail "diverged: $out"
[[ "$(k rev-parse HEAD)" == "$D" && ! -s "$TOOL_LOG" ]] || fail "diverged install changed"

# Usage: missing --lane, a HEAD that is no sha.
run 1 post-merge 7 "$H"; [[ "$err" == *"usage: octo-feather-lane post-merge PR HEAD --lane NAME"* ]] || fail "usage: $err"
run 1 post-merge 7 nothex --lane gh7; [[ "$err" == *"HEAD must be"* ]] || fail "bad head: $err"
echo "lane-post-merge: ok (step 1 stops on not merged, other head, gh failure; step 2 watches to the end, green passes," \
  "red names the run URL, failed watch and no run in bound stop (naming its workflows); no workflow file (no .github, or" \
  "none in .github/workflows) is the no-CI fact: step 2 ok naming it, no wait, steps 3-5 run, rerun the same; step 3 fast-forwards a behind install, no move at or" \
  "past, mise only with mise.toml, stops on dirty, diverged, a failing refresh, a missing pinned Python (no download," \
  "names uv python install --no-bin <pin>); other repo unchanged; summary last)"
