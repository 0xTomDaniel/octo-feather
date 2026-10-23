# gh124 smoke: code reviewer lists every restatement of an owned rule (`Owner:` lines)

Smoke: agents/code-reviewer.md .skillfile/patches/skills/code-review/SKILL.md.patch .agents/skills/code-review/
Removed: nothing from the reviewer's rules; adds the `Owner:` / `Owners: none` lines. Incident: class `duplicated-rule`, lane gh118 (archive gh118.handoffs.jsonl lines 70 and 79, PR #120 review rounds 6 and 7, fixes 61e2b8e and 5ad7429): restatements written in the same lane as the owner text, found a share per round.

Owed eval: docs/owed-evals/124.md.

## Harness (both runs)

- Kits: before = `git archive 78a097d` (main, gh124 base) into `<scratch>/kit-before`; after = this worktree (branch corrector-gh124) with this change.
- Fixture: scratch git repo, `main` (AGENTS.md rule "Each rule is stated once, where it is owned; every other file points to it", docs/adr/0001, README.md saying "the error should tell the user which command fixes it", agents/worker.md, src/app.py). Branch `lane-gh5` adds `docs/adr/0002-errors-name-the-fix.md` (errors name the fix command, usage errors exit 2) and in the same commit restates it in `AGENTS.md:9` and `agents/worker.md:5`, plus the src change. README.md unchanged (a prior restatement the new ADR now owns). One clone per run.
- Sandbox: `env -i` with only `PATH=<scratch>/bin:/usr/local/bin:/usr/bin:/bin` (`<scratch>/bin` holds `pi`, `fd`), `HOME=<scratch>/home` (copies of Pi's `models.json`, `auth.json`), `XDG_STATE_HOME=<scratch>/state`, `GH_CONFIG_DIR=<scratch>/ghcfg` (empty), `HERDR_SESSION=gh124-sandbox`, `PI_CODING_AGENT_SESSION_DIR=<scratch>/sess-<run>`, `TERM`, `LANG`, `PI_SKIP_VERSION_CHECK=1`. Checked first: `herdr`, `herdr-say`, `octo-feather-state`, `gh` not found; no `HERDR_*` or `OCTO_FEATHER_*` variable. No live pane touched.
- Command (cwd the clone): `env -i <sandbox> timeout -k 30 1200 <kit>/scripts/pi-role <kit>/agents/code-reviewer.md -p "Review lane gh5, ticket #5, diff main...lane-gh5 (this worktree). No supervisor exists in this run (herdr-say is not installed): message no one; print your full report as your final message."`
- Model `openai/gpt-6.1-sol`, thinking high. Both runs 2026-10-23, in parallel, rc 0.

## Run 1: before (kit 78a097d): FAIL

19 tool calls; read README.md but no repo-wide search. Report (trimmed):

```
- **class: duplicated-rule**: `AGENTS.md:9` and `agents/worker.md:5` restate the error policy owned by `docs/adr/0002-errors-name-the-fix.md:3`. ...
Checks: none
```

No `Owner:` line; unchanged `README.md:5` missed (the gh118 shape: a share of the restatements per round).

## Run 2: after (this change): PASS

21 tool calls, including `git grep -n -Ei 'error|usage|fix|check|test' -- '*.md'`. Report (trimmed):

```
1. **class: duplicated-rule**
   `AGENTS.md:9`, `agents/worker.md:5`, and unchanged `README.md:5` restate the new error-message rule owned by `docs/adr/0002-errors-name-the-fix.md:3`. ...
Checks: none

Owner: docs/adr/0002-errors-name-the-fix.md: error messages name the fix command | restated: AGENTS.md:9, agents/worker.md:5, README.md:5
Owner: docs/adr/0002-errors-name-the-fix.md: usage errors exit 2 | restated: AGENTS.md:9, agents/worker.md:5
```

Both runs wrote the verdict as a heading (`## Verdict: blocked`), not the `Verdict: blocking` line the helper reads; same as gh118 run 4, unchanged here. `scripts/octo-feather-lane verdict` matches only `^Check:` / `^Checks:` lines, so `Owner:` lines pass into the comment's findings body untouched.
