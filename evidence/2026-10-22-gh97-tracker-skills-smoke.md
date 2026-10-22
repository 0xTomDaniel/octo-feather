# Tracker per target: github-pr and github-issues loaded per role (issue #97, lane gh82)

Live smoke of the role change (docs/adr/0008): the `github` skill splits into `github-pr` and the tracker skill `github-issues`; role `skills:` lines name `github-pr` and, where the role does ticket work, `{tracker}`, which `pi-role` resolves from the target's `.octo-feather.toml`. Owed eval: docs/owed-evals/97.md.

## Setup

- Kit: worktree on `implementer-gh97`, uncommitted tree of this change (`<kit>` below).
- Target: `/tmp/gh97-fixture`, a fresh `git init` with one `AGENTS.md` line and no `.octo-feather.toml`.
- Each run headless, Herdr ids and `OCTO_FEATHER_PARENT` unset, the role's own model with `--thinking off`:
  `<kit>/scripts/pi-role <kit>/agents/<role>.md --thinking off -p "Do not use tools. List, one per line and nothing else, the name of every skill in your available_skills list."`

## Runs: skills each role reports (target with no tracker set)

Smoke: agents/supervisor.md .agents/skills/github-pr/SKILL.md .agents/skills/github-issues/SKILL.md .agents/skills/github/SKILL.md

```
commit
github-pr
github-issues
herdr-comms
implement-spec
push
to-tickets
```

Smoke: agents/director.md

```
herdr-comms
github-pr
github-issues
```

Smoke: agents/implementer.md

```
principle-prove-it-works
blast-radius
commit
github-pr
github-issues
implement
nodejs
pnpm
pull
python
tdd
typescript
```

Smoke: agents/code-reviewer.md

```
code-review
github-pr
```

Smoke: agents/corrector.md

```
commit
correct
github-pr
principle-encode-lessons-in-structure
writing-for-agents
```

No role reports `github` or `linear`; `{tracker}` became `github-issues` in the three roles that list it.

## Run: the supervisor uses the tracker skill

Same target, tools allowed: "You may read your skill files; change nothing and message nobody. Using only your loaded skills: which exact command (script path and args) prints the lane key for issue 82, which prints the line a lane PR body starts with for issue 82, and which command closes ticket 82 after the merge? Run the first two (they need no network) and give their output."

```
I found these in the `github-issues` skill. Its scripts are in `<kit>/.agents/skills/github-issues/scripts/`.

- **Lane key:** `scripts/lane-key 82` printed `gh82`.
- **PR body first line:** `scripts/pr-line 82` printed `Closes #82`.
- **Close ticket 82:** `scripts/issue-done 82`. I didn't run this one. It prints nothing, and an issue that's already closed stays closed. The skill says tracker writes need consent, as set out in the `github-pr` skill's Consent section.

I changed nothing and messaged nobody.
```

A first run with tools barred named the merge section correctly but found that `agents/supervisor.md` line 62 still says "the `github` skill"; that prose is ticket #100's sweep.

## Demo: pi-role in the fixture, no config, then `tracker = "jira"`

```
$ cd /tmp/gh97-fixture && <kit>/scripts/pi-role --json <kit>/agents/supervisor.md
{"args": ["--approve", "--model", "anthropic/claude-opus-5-5", "--thinking", "high", "--tools", "read,grep,find,ls,bash,edit,write", "--no-mcp", "--no-skills", "--skill", "<kit>/.agents/skills/commit", "--skill", "<kit>/.agents/skills/github-pr", "--skill", "<kit>/.agents/skills/github-issues", "--skill", "<kit>/.agents/skills/herdr-comms", "--skill", "<kit>/.agents/skills/implement-spec", "--skill", "<kit>/.agents/skills/push", "--skill", "<kit>/.agents/skills/to-tickets", "--append-system-prompt", "<cache>/octo-feather/roles/supervisor-570879c34b1c.md"]}
rc=0
$ echo 'tracker = "jira"' > .octo-feather.toml && <kit>/scripts/pi-role --json <kit>/agents/supervisor.md
pi-role: unknown tracker 'jira' in /tmp/gh97-fixture/.octo-feather.toml; the kit has: github
rc=1
```

## Result

- Every changed role reports `github-pr`; director, supervisor and implementer also report `github-issues`; none reports `github` or `linear`.

Removed: the `github` skill (`.agents/skills/github/SKILL.md`), now `github-pr` (PRs, merge, consent) plus `github-issues` (tickets through seven scripts); its `gh issue view` and `gh issue close` lines, and "GitHub Issues is the only tracker". From the role files: `github` on each changed `skills:` line.

## Follow-up run: renamed references (same fixture, rebuilt fresh)

After the dangling references to the old `github` skill were renamed (supervisor merge line, push's consent link, the implement-spec and to-tickets tracker line and their patches) and `issue-view` state became `open` or `done`. Supervisor, headless, `--thinking off`, tools allowed: "You may read your skill files; change nothing and message nobody. Answer in four short lines: (1) follow the consent link in the push skill: which file and section does it open, and does that file exist? (2) per the to-tickets skill, through which skill are tickets filed? (3) per the implement-spec skill, the same question. (4) which skill's command does your role file say you merge with, and what is that command? Then (5) run the issue-view script of the tracker skill on issue 1 and give its exact output or error."

Smoke: agents/supervisor.md .agents/skills/push/SKILL.md .agents/skills/to-tickets/SKILL.md .agents/skills/implement-spec/SKILL.md .skillfile/patches/skills/to-tickets/SKILL.md.patch .skillfile/patches/skills/implement-spec/SKILL.md.patch .agents/skills/github-issues/SKILL.md

```
1. The consent link opens `../github-pr/SKILL.md#consent`, which is the `## Consent` section of `github-pr/SKILL.md`. The file exists.
2. to-tickets files tickets through the tracker skill (GitHub Issues, which is `github-issues`).
3. implement-spec says the same: through the tracker skill (GitHub Issues, `github-issues`).
4. My role file says to merge with the `github-pr` skill's command: `gh pr merge <N> --merge --match-head-commit <head>`.
5. `github-issues/scripts/issue-view 1` printed `no git remotes found` and exited with code 1.
```

(5) is the real `gh` in a target with no remote: a non-zero exit with the reason, as spec skills#tracker-scripts says.

Removed: "the `github` skill" from the supervisor's merge line, the implement-spec and to-tickets tracker line (and their patches), and push's `../github/SKILL.md` consent link; `issue-view`'s raw `OPEN`/`CLOSED` state.
