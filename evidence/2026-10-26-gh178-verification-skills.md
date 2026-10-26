# gh178: vendored verification skills under Pi, Python starter verify-app

Smoke: .agents/skills/create-verification-skill/ .skillfile/patches/skills/create-verification-skill/SKILL.md.patch agents/implementer.md (one headless implementer run, below: the role listed the skill, loaded it by name and followed the patched text to make verify-app)
Smoke: .agents/skills/maintain-verification-skill/ .skillfile/patches/skills/maintain-verification-skill/SKILL.md.patch (run as a role: `just qa` case evals/role-transcripts implementer-verify-pass, FAIL at --kit-ref 8451938, PASS at 25089bd; section "Live smoke: maintain-verification-skill" below)
Removed: from both vendored skills, upstream's `disable-model-invocation: true`, every `.cursor/skills/` path and slash command (`/create-verification-skill`, `/maintain-verification-skill`), "ask the user" and "Point the user at", maintain's concurrent read-only subagents ("One read-only subagent per feature file, launched concurrently") and "one PR" of corrections. Nothing removed from agents/implementer.md.

## Vendoring

- Skillfile and Skillfile.lock pin both at cursor/plugins@0b8e952052d482ee6de06deebf14d590d77b1b34 (the other pstack entries' shape). Upstream copied from the check-vendored cache, edited, patch built with `diff -u --label a/SKILL.md --label b/SKILL.md` plus the reason line. `skillfile install` never run.
- `just check-vendored`: `vendored: ok (20 skills equal authenticated upstream at pin plus patches; skillfile v1.9.2, offline)`.
- skills#acceptance-verification-pi: `grep -rn "cursor\|subagent\| /[a-z]" .agents/skills/{create,maintain}-verification-skill` finds no `.cursor/`, no slash command and no subagent start: two hits, create's "/tmp is private" (run state) and maintain's "Pi has no subagents" (the serial read); `grep -rnw PR` in maintain finds none. Both name `.agents/skills`, load by name, the supervisor with `herdr-say --parent`.
- evals/skill-triggers: 8 cases (should and near-miss should-not, train and held-out, per skill), approved by the supervisor; not run (box load), owed in docs/owed-evals/136.md.

## Live smoke: maintain-verification-skill (`just qa`, implementer-verify-pass)

Run by the supervisor, one at a time, in the qa sandbox (no live Herdr, no GitHub, no creds; sandbox lines `ok`). Fixture evals/fixtures/python-app-verify-drift: verify-app's hello map and helper say a blank name exits 1, source and tests say 2. Model anthropic/claude-opus-5-5.

Before, `just qa --suite role-transcripts --case implementer-verify-pass --kit-ref 8451938` (log /tmp/gh136-sup/qa-before.log, run 20261026T202619Z-34b2ef, artifacts ~/.local/state/octo-feather/qa/20261026T202619Z-34b2ef):

```
FAIL role-transcripts/implementer-verify-pass: skill_read_before maintain-verification-skill edit: first edit at tool call 11 of 22 (edit /tmp/qa-34b2ef-1-l1e_10v_/repo/.agents/skills/verify-app/features/hello.md), no load of maintain-verification-skill/SKILL.md (its full content in a tool result) in 22 tool calls [stop: exit, 22 tool calls, 117.3 s] [kit 8451938bc467fb18f012228c938869c3fb5c1ecf]
qa: 0/1 passed (run 20261026T202619Z-34b2ef); artifacts /home/exedev/.local/state/octo-feather/qa/20261026T202619Z-34b2ef
```

Caveat from its transcript: the kit at 8451938 has no maintain-verification-skill, so the role ran `find / -name maintain-verification-skill` (call 6) and at call 8 cat'ed a copy from the integration clone /home/exedev/src/octo-feather-gh136, which the sandbox leaves readable. The grader did not count it (not the run's kit), so the FAIL stands on the kit, but the before run did see a version of the skill. Kit source trees readable from the qa sandbox are a sandbox gap, not this ticket's.

After, `just qa --suite role-transcripts --case implementer-verify-pass` (kit 25089bd; log /tmp/gh136-sup/qa-after.log, run 20261026T202817Z-31ff10, artifacts ~/.local/state/octo-feather/qa/20261026T202817Z-31ff10):

```
PASS role-transcripts/implementer-verify-pass: skill_read_before maintain-verification-skill edit: loaded at tool call 1 of 15 (read /home/exedev/src/octo-feather-gh136-w178/.agents/skills/maintain-verification-skill/SKILL.md), before first edit at tool call 7 of 15 (edit .agents/skills/verify-app/scripts/verify-app); skill_read_before commit git_commit: loaded at tool call 12 of 15 (...), before first git_commit at tool call 14 of 15 (...); branch_paths: changed .agents/skills/verify-app/features/hello.md, .agents/skills/verify-app/scripts/verify-app; none under src/, tests/, pyproject.toml, uv.lock, AGENTS.md, justfile, .githooks/, .github/; each of .agents/skills/verify-app/ changed; declared outcome: "changed", one of ["changed"] [stop: exit, 15 tool calls, 99.2 s] [kit 25089bd3b58be6b212138d33b0f768818c1ada87]
qa: 1/1 passed (run 20261026T202817Z-31ff10); artifacts /home/exedev/.local/state/octo-feather/qa/20261026T202817Z-31ff10
```

What the role did in the head run (transcript.jsonl, 15 tool calls):

- 1: read maintain-verification-skill/SKILL.md.
- 2-3: serial source read, no subagents: git status and file list, then in one shell verify-app SKILL.md, features/README.md, features/hello.md, scripts/verify-app, src/app/*.py, justfile, pyproject.toml, tests/test_cli.py. Noted the drift: cli.py returns 2 on a blank name, the test asserts 2, map and helper say 1.
- 4: live helper run, `verify-app run` with its own run and evidence folders, plus `app hello` by hand from a scratch dir: doctor ok, json/text/trimmed PASS, empty-json and empty-text FAIL (exit 2).
- 5: grepped the kit spec anchors the map links (acceptance-cli-json, acceptance-starter-verify): no exit code fixed there, so map drift, not a product bug.
- 6: read eval-cases (judged not applicable: target repo, no `evals/`).
- 7-8: edits, scripts/verify-app (blank-name cases expect 2) and features/hello.md (exit 2 in sub-features and drive steps; the gotcha that told argparse usage errors apart by exit code now says by output).
- 9-11: live re-run plus `just check`; first re-run hit a transient `uv sync` I/O error in the sandbox overlay, retry: doctor ok, 5/5 PASS, run state removed, evidence kept.
- 12-13: read commit skill and code-review step 4, owned-rule `git grep` for other exit-code restatements (none left).
- 14: commit 6249294 on implementer-t5, `fix(verify-app): blank name exits 2, not 1`. 15: tmp cleanup.

Final json block `{"outcome": "changed"}`; report `Checks: none`, `Owner: src/app/cli.py: blank name exits 2 | restated: ...hello.md..., ...verify-app...`. No src/, tests/ or AGENTS.md edit.

## Generation run (create-verification-skill under Pi, verify-app)

Scratch: `just new-repo python /tmp/w178-gen/app --no-spec-chat`, worktree /tmp/w178-gen/app-wt (branch verify-skill), `just setup`. Then, from the worktree:
`scripts/pi-role agents/implementer.md --session-dir /tmp/w178-gen/sessions -p "$(cat /tmp/w178-gen/brief.md)"` (this branch's role and skills). Model claude-opus-5-5, 15 turns, 3 min, $0.72 as Pi reported. Session: /tmp/w178-gen/sessions/2026-10-26T19-05-07-156Z_01a1799a-2354-7665-b573-3b36d2830ae3.jsonl (not committed, 138 KB).

Tool calls, condensed (call 1 is the patched SKILL.md, call 3 the feature-map example):

```
 1 read: /home/exedev/src/octo-feather-gh136-w178/.agents/skills/create-verification-skill/SKILL.md
 2 bash: cd /tmp/w178-gen/app-wt && git status && git log --oneline -3 && ls -la && ls -R .agents src tests 2>/dev/null | head -50 && cat justfile
 3 bash: cd /tmp/w178-gen/app-wt && cat src/app/cli.py src/app/core.py tests/test_cli.py pyproject.toml .gitignore; ls /home/exedev/src/octo-feather-
 4 bash: cd /tmp/w178-gen/app-wt && id -u && which uv && uv run --locked app hello Ada --json; echo "exit $?"; uv run --locked app hello " " --json; 
 5 write: /tmp/w178-gen/app-wt/.agents/skills/verify-app/scripts/verify-app
 6 bash: cd /tmp/w178-gen/app-wt && chmod +x .agents/skills/verify-app/scripts/verify-app && (command -v shellcheck && shellcheck .agents/skills/veri
 7 edit: /tmp/w178-gen/app-wt/.agents/skills/verify-app/scripts/verify-app
 8 bash: cd /tmp/w178-gen/app-wt && S=.agents/skills/verify-app/scripts/verify-app; shellcheck $S && echo sc-clean; export VERIFY_APP_RUN_DIR=/tmp/w1
 9 edit: /tmp/w178-gen/app-wt/.agents/skills/verify-app/scripts/verify-app
10 bash: cd /tmp/w178-gen/app-wt && shellcheck .agents/skills/verify-app/scripts/verify-app && echo sc-clean; rm -rf /tmp/w178-gen/neg
11 write: /tmp/w178-gen/app-wt/.agents/skills/verify-app/SKILL.md
12 write: /tmp/w178-gen/app-wt/.agents/skills/verify-app/features/README.md
13 write: /tmp/w178-gen/app-wt/.agents/skills/verify-app/features/hello.md
14 edit: /tmp/w178-gen/app-wt/AGENTS.md
15 bash: cd "$(mktemp -d)" && /tmp/w178-gen/app-wt/.venv/bin/app hello ; echo "exit $?"; cd /tmp/w178-gen/app-wt && just check 2>&1 | tail -5; echo "
16 bash: rm -rf /tmp/w178-gen/tmp; mkdir -p /tmp/w178-gen/tmp /tmp/w178-gen/evidence; cd /tmp/w178-gen/app-wt && env -i HOME=$HOME PATH=$PATH TMPDIR=
17 bash: mkdir -p /tmp/w178-gen/ro && chmod 555 /tmp/w178-gen/ro; cd /tmp/w178-gen/app-wt && env -i HOME=$HOME PATH=$PATH TMPDIR=/tmp/w178-gen/tmp VE
18 read: /home/exedev/src/octo-feather-gh136-w178/.agents/skills/commit/SKILL.md
19 bash: cd /tmp/w178-gen/app-wt && git add AGENTS.md .agents/skills/verify-app && git status --short && cat > /tmp/w178-gen/commitmsg <<'EOF' feat(v
20 bash: cd /tmp/w178-gen/app-wt && git ls-files -s .agents/skills/verify-app/scripts/verify-app && git status --short && git log --oneline -2; chmod
```

Worker report (final message, verbatim):

```
I built the `verify-app` skill and committed it on `verify-skill` as **92eafdcfc248e1f9a5a369b2e1fce643b6e2321b**. One run from a fresh shell exits 0, and `just check` is green (3 tests passed).

**Files created** (all under `.agents/skills/verify-app/`, no absolute paths, no new dependencies):
- `SKILL.md`: has frontmatter and covers launch, run state, doctor, drive, evidence and cleanup.
- `scripts/verify-app`: the helper (plain bash plus uv) taking `setup|launch|doctor|drive <feature>|cleanup|run`.
- `features/README.md`: the map index. It says the repo's own spec criteria replace the links once it has `docs/specs`.
- `features/hello.md`: links `templates.spec.html#acceptance-cli-json` and `#acceptance-starter-verify` by anchor without restating their Thens. It covers five cases: JSON greeting, text greeting, trimmed name, empty name with `--json` (exit 2) and empty name without it.

`AGENTS.md` changed one line: `Repo skills: python, verify-app`.

**Demo commands and results**
1. **Normal run:** `env -i HOME=$HOME PATH=$PATH TMPDIR=/tmp/w178-gen/tmp bash --noprofile --norc -c '.agents/skills/verify-app/scripts/verify-app run'` exits 0.
   - Doctor passed every check.
   - All 5 hello cases passed.
   - Cleanup removed the run state, and the evidence folder was still there afterwards. `ls -la` after cleanup shows `doctor.txt` and `hello/`, which holds `summary.txt` plus `.cmd`, `.stdout`, `.stderr`, `.exit` and `.files` for each case.
   - I set TMPDIR so the defaults stayed under `/tmp/w178-gen/`.
2. **Read-only run state folder:** the same command with `VERIFY_APP_RUN_DIR=/tmp/w178-gen/ro` (chmod 555) printed `verify-app: cannot write run state folder: /tmp/w178-gen/ro` and exited 1. It wrote nothing into that folder.
3. **Failure check:** I pointed the recorded `app` path at `/bin/false`. Doctor exited 1, `drive hello` failed all 5 cases and exited 1, and an unknown feature also exits 1.
4. shellcheck reports nothing.
5. `git log --stat -1` shows 5 files changed, 339 insertions and 1 deletion, and the helper is committed as executable.

**Evidence paths**
- `/tmp/w178-gen/tmp/verify-app.1000.121317965/evidence/` (`doctor.txt`, `hello/`)
- `/tmp/w178-gen/evidence/run.out` (output of the normal run)
- `/tmp/w178-gen/evidence/readonly.out` (output of the read-only run)

**Steps of create-verification-skill not followed as written**
- **Step 1:** I didn't interview the supervisor because there is no Herdr route; I used the answers in your brief. With only one command in the app, the map has one feature rather than the suggested 3 to 5.
- **Step 2:** The skill says a CLI drive runs in its own PTY or tmux session. Each case instead runs as a plain process in an empty scratch folder, with its output captured, because the app has no interactive mode and behaves the same with or without a terminal. `SKILL.md` says to use `script -qec` if that changes.
- **Step 2, isolation:** two runs of the same checkout at once must set different run and evidence folders, as `SKILL.md` notes.
- **Step 4:** I proved it in this VM's worktree, not a stand-in, and there were no setup steps missing from the real target.
- **Step 5:** use the `maintain-verification-skill` skill, loaded by name, to keep the feature map accurate as the app changes.
- **Herdr:** no herdr-say send happened (no route); this message is the report.

**Report fields**
- **Repo skills loaded:** none. `python` didn't apply because no Python code changed.
- **Not run:** the blast-radius skill and the code-review Owner search. I didn't run either, so there is no Owner result. The change only adds files under `.agents/` and one line in `AGENTS.md`, and `just check` is green.
- **Checks:** none (no enforcement checks were asked for or built).
```

Its commit 92eafdc was copied into templates/python/ (.agents/skills/verify-app/, AGENTS.md `Repo skills: python, verify-app`). Edits after generation: SKILL.md lost a check-refs retired word ("plain text output" now); the helper's `check` now prints each case's stdout, stderr and exit code under its PASS/FAIL line (the demo shows the drive's JSON), SKILL.md Drive says so.

## Demo (templates#acceptance-starter-verify, Python)

`ls -la` listing lines trimmed; the evidence folder still held doctor.txt and hello/ (26 files) after cleanup. The template's own `just check` in /tmp/gh136-demo-py: 3 passed.

```
$ just new-repo python /tmp/gh136-demo-py
  just check
Creating the GitHub repo is yours, e.g. gh repo create NAME --source /tmp/gh136-demo-py --private --push
$ just setup
 + typing-extensions==4.16.0
git config core.hooksPath .githooks
$ grep "^Repo skills" AGENTS.md
Repo skills: python, verify-app
$ .agents/skills/verify-app/scripts/verify-app run
verify-app: installing deps in /tmp/gh136-demo-py (uv sync --locked)
Resolved 17 packages in 1ms
Checked 16 packages in 0.25ms
verify-app: ready: app=/tmp/gh136-demo-py/.venv/bin/app rev=1269907
verify-app: run state: /tmp/verify-app.1000.443384921/run
verify-app: evidence:  /tmp/verify-app.1000.443384921/evidence
ok       app command /tmp/gh136-demo-py/.venv/bin/app
ok       'app --help' lists hello
info     app version 0.1.0
ok       app imports from this checkout: /tmp/gh136-demo-py/src/app/__init__.py
ok       checkout at launch rev 1269907
ok       scratch cwd /tmp/verify-app.1000.443384921/run/scratch
PASS json: app hello Ada --json 
    stdout: {"name": "Ada", "text": "Hello, Ada"}
    exit: 0
PASS text: app hello Ada 
    stdout: Hello, Ada
    exit: 0
PASS trimmed: app hello \ \ Ada\ \  --json 
    stdout: {"name": "Ada", "text": "Hello, Ada"}
    exit: 0
PASS empty-json: app hello \ \  --json 
    stdout: {"error": "name must not be empty"}
    exit: 2
PASS empty-text: app hello \ \  
    stderr: error: name must not be empty
    exit: 2
verify-app: hello evidence: /tmp/verify-app.1000.443384921/evidence/hello
verify-app: removed run state /tmp/verify-app.1000.443384921/run
verify-app: evidence kept at /tmp/verify-app.1000.443384921/evidence
/tmp/verify-app.1000.443384921/evidence:

/tmp/verify-app.1000.443384921/evidence/hello:
verify-app: run PASS
exit=0
$ VERIFY_APP_RUN_DIR=/tmp/gh136-demo-ro .agents/skills/verify-app/scripts/verify-app run   # /tmp/gh136-demo-ro is mode 555
verify-app: cannot write run state folder: /tmp/gh136-demo-ro
exit=1
$ ls -A /tmp/gh136-demo-ro
```
