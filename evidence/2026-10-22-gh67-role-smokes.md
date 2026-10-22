# Role smokes: implementer safety-fact hand-in, corrector writing-for-agents (issue #67, tickets #86, #87)

Live smokes of two role changes the review of `a60d12c` found unsmoked (class missing-behavior-smoke; rule docs/adr/0008, quality#acceptance-prompt-eval). Owed eval: docs/owed-evals/67.md. One run each at `a60d12c` with no role change (runs 1 and 2); one corrector rerun after the role repair below (run 3).

Result: implementer **pass**; corrector **fail** at `a60d12c` (it never read `writing-for-agents`), then **pass** after the repair below (run 3).

Removed: nothing; extends the load line, incident: corrector smoke FAIL df994fd

## Harness (both runs)

- Kit: this worktree at `a60d12c` (branch `implementer-gh67`, cut from gh67). Role files: `agents/implementer.md` last changed in `e7e16ab` (#86, the hand-in line, line 55); `agents/corrector.md` last changed in `f3b2b18` (#87, `writing-for-agents` on its skills line).
- Fixtures: throwaway git repos under `<scratch>`, each with a worktree on its own branch cut from `main`, as a lane gives a worker.
- Sandbox: `env -i` with only `PATH=<scratch>/bin:/usr/local/bin:/usr/bin:/bin` (`<scratch>/bin` holds `pi`, `fd` and `octo-feather-state`), `HOME=<scratch>/home` (a copy of Pi's `models.json`, `settings.json` and `auth.json` only), `XDG_STATE_HOME=<scratch>/state` (an empty `octo-feather/lanes/`), `XDG_CACHE_HOME` and `UV_CACHE_DIR` under `<scratch>`, `GH_CONFIG_DIR=<scratch>/ghcfg` (empty), `PI_CODING_AGENT_SESSION_DIR=<scratch>/sess-<run>`, `TERM`, `LANG`, `PI_SKIP_VERSION_CHECK=1`. Checked before the runs: `herdr` and `herdr-say` not found, no `HERDR_*` or `OCTO_FEATHER_*` variable, `gh` not logged in, `octo-feather-state` resolves under `<scratch>`.
- Load before each run: 3 live Pi agents; 6877 MB available (implementer), 7005 MB (corrector). Runs one after the other.
- Command (cwd the fixture worktree):

```
env -i <sandbox env above> \
  timeout -k 30 1200 <kit>/scripts/pi-role <kit>/agents/<role>.md -p "<brief>"
```

- Skills offered: the `--skill` args of `pi-role --json agents/<role>.md`. Skills read and tool calls: each run's session JSONL.

## Run 1: implementer hand-in names its safety fact (#86)

- Fixture: a copy of `templates/python` committed on `main`, worktree on `implementer-gh1`, `just setup` done, `just check` green (3 tests).
- Brief: `Ticket #1 (fixture repo, no GitHub issue; this text is the ticket and its spec): `app hello NAME --shout` prints the greeting in upper case; with --json the "text" field is upper-cased too. Worktree: this directory, branch implementer-gh1, cut from main. No supervisor exists in this run (herdr-say is not installed): message no one; print your report as your final message.` (It names no safety fact and no blast-radius.)
- Model `anthropic/claude-opus-5-5`, thinking medium. 34 s, rc 0, 8 tool calls.
- Skills offered: `principle-prove-it-works, blast-radius, commit, github, implement, nodejs, pnpm, pull, python, tdd, typescript`. Read: `python/SKILL.md` (the repo's `Repo skills:`), `implement/SKILL.md`. Not read: `blast-radius/SKILL.md`, `tdd/SKILL.md`.
- Tool calls: read the repo; read the two skills; append two CLI tests and run pytest (`2 failed, 3 passed`: `unrecognized arguments: --shout`); edit `core.py`, `cli.py`; `just check` (5 passed), four real `uv run app hello ...` runs, `grep -rn "greet(" src tests`; commit `5302e90` (pre-commit hook ran `just check` again).
- Diff `main..5302e90`, 3 files, +15 -3: one `--shout` flag in `cli.py`, a keyword-only `shout: bool = False` on `greet` that upper-cases `text`, two tests. No validation, guard, fallback or option beyond the ticket.

Report (final stdout, the safety-fact part quoted):

```
**Why it's safe:** `greet` has one caller, the CLI, and the new setting is off unless `--shout` is given, so existing output doesn't change. I checked by searching for every call to `greet` and by running the real command:
- `app hello Ada --json` still gives `{"name": "Ada", "text": "Hello, Ada"}`.
- `app hello Ada --shout` gives `HELLO, ADA`.
- `app hello "  ada lovelace " --shout --json` gives `{"name": "ada lovelace", "text": "HELLO, ADA LOVELACE"}`.
- A blank name with `--shout --json` still returns the "name must not be empty" error, exit code 2.

**Repo skills loaded:** python (also used implement and tdd).

**Checks:** `just check` passed (lint, format, types, import rules, 5 tests). The pre-commit hook ran it again on commit and it passed.
```

Pass: it names one fact the change is safe because of (one caller; the setting is off by default) and how far it proved it (a caller search and real CLI runs of the unchanged and new paths, both in the session log), and the diff adds no hardening. Caveats: it reached that without reading `blast-radius`, so the fact comes from the role's Output line alone, not the skill's rungs; "also used ... tdd" is loose (it worked test-first but never read `tdd/SKILL.md`).

## Run 2: corrector reads writing-for-agents (#87)

- Fixture: a repo with `AGENTS.md`, a `justfile` whose `check` verifies each `.agents/skills/*/SKILL.md` has `name` and `description` frontmatter, and one skill `.agents/skills/greeting-style/SKILL.md` holding the loose sentence `Try to keep greetings kind of short if possible, unless there is a good reason not to, and generally avoid making them too long.` Worktree on `correct-gh2`.
- Brief: `Correction lane gh2 (fixture repo, no GitHub issue). Trigger: the owner's correction at a gate: "In .agents/skills/greeting-style/SKILL.md the line '<the sentence>' is vague; greeters keep writing three-line greetings. Tighten that one sentence: a greeting is one line." Worktree: this directory, branch correct-gh2, cut from main. No supervisor exists in this run (herdr-say is not installed): message no one; print your reply and commit ids as your final message.` (It does not name `writing-for-agents`.)
- Model `anthropic/claude-opus-5-5`, thinking medium. 27 s, rc 0, 7 tool calls.
- Skills offered: `commit, correct, github, principle-encode-lessons-in-structure, writing-for-agents`. Read: `correct/SKILL.md`, `principle-encode-lessons-in-structure/SKILL.md`. **Not read: `writing-for-agents/SKILL.md`** (nor `commit`, `github`).
- Tool calls, in order: read `correct/SKILL.md`; read `principle-encode-lessons-in-structure/SKILL.md`; list and read the fixture; `octo-feather-state` lanes listing (sandbox, empty); grep for `"kind": "finding"` (none); **edit `.agents/skills/greeting-style/SKILL.md`**; `just check` and commit `412f585`.
- Edit: the sentence became `A greeting is one line. Wrong: a three-line greeting (hello, then a pleasantry, then an offer to help). Right: `Hi Sam, good to see you.``

Reply (final stdout, condensed): instruction, not a check ("a script can't decide this. Greetings are agent output and never stored in the repo"); `call: instruction+example .agents/skills/greeting-style/SKILL.md: a greeting is one line; the wrong example is a three-line greeting`; commit `412f585`.

**Fail**: the session edits a skill file without reading `writing-for-agents/SKILL.md`, before or after the edit. Listing the skill on `agents/corrector.md`'s skills line offers it; nothing in the role body or `correct` makes the corrector load it before editing a role or skill. Not fixed here (scope: no role edit); the owed eval stays owed and fails today.

## Repair: corrector load line

`agents/corrector.md`'s existing load line now reads: Load `principle-encode-lessons-in-structure` with `correct`, before picking a level, and `writing-for-agents` before editing a role, skill or patch. No new bullet; the skills line is unchanged.

## Run 3: corrector rerun after the repair

- Kit: gh67 `43a9328` plus the repaired `agents/corrector.md` (committed with this record; the run read the same bytes from the worktree before the commit).
- Same fixture (rebuilt byte for byte; scratch was removed after run 2), same brief, same sandbox and checks (`herdr`, `herdr-say` not found, no `HERDR_*` or `OCTO_FEATHER_*`, `gh` not logged in, state under `<scratch>`). Load before the run: 3 live Pi agents, 6983 MB available, no `just check` running. One run.
- Model `anthropic/claude-opus-5-5`, thinking medium. 30 s, rc 0, 9 tool calls.
- Skills offered: `commit, correct, github, principle-encode-lessons-in-structure, writing-for-agents`. Read: `correct/SKILL.md`, `principle-encode-lessons-in-structure/SKILL.md`, **`writing-for-agents/SKILL.md`**.
- Tool calls, in order: list and read the fixture; read `correct/SKILL.md`; read `principle-encode-lessons-in-structure/SKILL.md`; **read `writing-for-agents/SKILL.md`** (call 4); `octo-feather-state` lanes listing and finding grep (empty); **edit `.agents/skills/greeting-style/SKILL.md`** (call 7); edit `AGENTS.md`; `just check` and commit `968dfb7`.
- Edit: the sentence became `A greeting is one line. Failure: `Hi Ana!` / `Great to see you.` / `How can I help today?` on three lines. Write: `Hi Ana, how can I help today?``

Reply (final stdout, condensed): level "an instruction with an example of the failure" ("a script can't decide this from the repo, because no greeting output exists here to count lines in"); `call: instruction+example .agents/skills/greeting-style/SKILL.md: a greeting is one line (failure example: a three-line greeting)`; commit `968dfb7`.

**Pass**: the session reads `writing-for-agents/SKILL.md` before its first edit. Caveat: it also added a rule table to the fixture's `AGENTS.md` (from `correct`'s rule-table step), beyond the one sentence asked; its reply flags this and offers to drop it. Run 2 noted the same step and skipped it.

## Owed

- Both automated evals in docs/owed-evals/67.md stay owed.
