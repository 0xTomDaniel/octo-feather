# Linear tracker: the linear skill and vendored linear-cli (issue #98, lane gh82)

Live smoke of the role change (docs/adr/0008): a new tracker skill `linear` (seven tracker scripts over the `linear` CLI, plus the offline fake `linear` for tests), and `linear-cli` vendored from schpet/linear-cli@02571d3 (v3.1.0, ISC) with a Pi-only patch, loaded by no role. Owed eval: docs/owed-evals/98.md.

## Setup

- Kit: worktree on `implementer-gh98`, uncommitted tree of this change (`<kit>` below).
- Target: `/tmp/gh98-fixture`, a fresh `git init` with one `AGENTS.md` line and `.octo-feather.toml` holding `tracker = "linear"`.
- Fake Linear: `<kit>/.agents/skills/linear/scripts` first on `PATH` (its `linear` is the offline fake), `OCTO_FEATHER_LINEAR_STORE` a JSON store with ENG-121 (Done), ENG-122 and ENG-123 (Todo, parent ENG-122, blocked by ENG-121). No `LINEAR_API_KEY` set; the fake needs none and has no network.
- Headless, Herdr ids and `OCTO_FEATHER_PARENT` unset, the role's own model with `--thinking off`:
  `<kit>/scripts/pi-role <kit>/agents/supervisor.md --thinking off -p "<prompt>"`.

## Run: the supervisor in a Linear target

Prompt: "You may read your skill files and run read-only commands; change nothing, write no ticket, message nobody. Answer in short numbered lines: (1) list, one per line, every skill in your available_skills list. (2) Using only your tracker skill, run the commands that print the lane key for Linear ticket ENG-123, the line a lane PR body starts with for it, and read ticket ENG-123; give each exact command (script path and args) and its exact output. (3) Which command would move ENG-123 to done after the merge (do not run it)? (4) Your tracker scripts do not list a team's workflow states: per your tracker skill, where do you look up how to do that read, and what command does that file give? Give the file path you read."

Smoke: agents/supervisor.md .agents/skills/linear/SKILL.md .agents/skills/linear-cli/ .skillfile/patches/skills/linear-cli/SKILL.md.patch

```
1. Skills in my available_skills list:
   - commit
   - github-pr
   - linear
   - herdr-comms
   - implement-spec
   - push
   - to-tickets

2. Commands I ran, with `S=<kit>/.agents/skills/linear/scripts`. Each one exited 0.
   - Lane key: `$S/lane-key ENG-123` printed `eng-123`.
   - PR line: `$S/pr-line ENG-123` printed `Tracks ENG-123`.
   - Read ticket: `$S/issue-view ENG-123` printed:
     `{"key":"ENG-123","title":"Linear tracker smoke","body":"Fixture ticket for the smoke.","state":"open","url":"https://linear.app/acme/issue/ENG-123/linear-tracker-smoke","parent":"ENG-122","blocked_by":["ENG-121"]}`
     (The real output is the same JSON spread over several lines.)

3. The command that would move ENG-123 to done is `<kit>/.agents/skills/linear/scripts/issue-done ENG-123`. I did not run it. It is a tracker write, so it needs consent under the github-pr skill's Consent section.

4. Workflow states:
   - The tracker skill says any other read goes through the vendored linear-cli skill's references at `<linear skill folder>/../linear-cli/references/`.
   - The file that covers this is `<kit>/.agents/skills/linear-cli/references/team.md`.
   - Its command is `linear team states [OPTIONS] [TEAM]`, for example `linear team states ENG --json`.
```

The store was unchanged after the run (ENG-123 still Todo, no comment). The supervisor had `linear`, not `github-issues` and not `linear-cli`, and reached `linear-cli` only by path through the `linear` skill.

## Demo: pi-role and lane-key in the fixture

```
$ cd /tmp/gh98-fixture && <kit>/scripts/pi-role --json <kit>/agents/supervisor.md
{"args": ["--approve", "--model", "anthropic/claude-opus-5-5", "--thinking", "high", "--tools", "read,grep,find,ls,bash,edit,write", "--no-mcp", "--no-skills", "--skill", "<kit>/.agents/skills/commit", "--skill", "<kit>/.agents/skills/github-pr", "--skill", "<kit>/.agents/skills/linear", "--skill", "<kit>/.agents/skills/herdr-comms", "--skill", "<kit>/.agents/skills/implement-spec", "--skill", "<kit>/.agents/skills/push", "--skill", "<kit>/.agents/skills/to-tickets", "--append-system-prompt", "<cache>/octo-feather/roles/supervisor-9c93f765915f.md"]}
rc=0
$ <kit>/.agents/skills/linear/scripts/lane-key ENG-123
eng-123
rc=0
```

## Result

- In a Linear target the supervisor reports `github-pr` and `linear`, not `github-issues` and not `linear-cli`; it runs the `linear` scripts for lane key, PR line and view, names `issue-done` for done, and reads `linear-cli` references by path for any other read.

Removed: from the vendored `linear-cli` SKILL.md, upstream's `allowed-tools: Bash(linear:*), Bash(curl:*)` frontmatter line (a tool-permission key of another runtime; Pi only, docs/adr/0001).
