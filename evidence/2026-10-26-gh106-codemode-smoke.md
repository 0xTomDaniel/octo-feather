# gh106 smoke: every role launches with codemode (#175)

Smoke: scripts/pi-role agents/director.md agents/supervisor.md agents/implementer.md agents/corrector.md agents/code-reviewer.md agents/qc-judge.md
Removed: nothing; no role file changed. pi-role now adds codemode to every role's --tools (spec roles#launch-codemode, accepted c2cf665).

Box, Pi 1.3.0 (`pi-version`), lane gh106 ticket #175, 2026-10-26. Base: `git archive 8451938` in /tmp/gh106-smoke/kit-base. Head: `git archive d131ddd` (this ticket's code commit) in /tmp/gh106-smoke/kit-head. 16 live runs, one at a time, none in parallel. Each role's own model; no override (director, supervisor, implementer, corrector `anthropic/claude-opus-5-5`; code-reviewer, qc-judge `openai/gpt-6.1-sol`).

## Isolation

The gh118 shape (evidence/2026-10-23-gh118-corrector-routing-smoke.md), per the supervisor's order replacing the herdr-spawn pane runs: no live Herdr, no lane state, no lane worktree.

- `env -i HOME=/tmp/gh106-smoke/home PATH=/tmp/gh106-smoke/bin:/usr/bin:/bin PI_CODING_AGENT_DIR=/tmp/gh106-smoke/agent HERDR_SESSION=gh106-smoke-sandbox TERM=dumb`; bin holds only a `pi` symlink. Proof line, every run: `herdr=none`, env keys `HERDR_SESSION HOME PATH PI_CODING_AGENT_DIR TERM`: no OCTO_FEATHER_PARENT, no HERDR_PANE_ID, no octo-feather-state on PATH.
- Temp Pi agent dir: copies of auth.json, models.json, models-store.json only (no settings.json, no extensions, no packages); `--session-dir` per run under /tmp/gh106-smoke/runs/<run>/sessions.
- cwd /tmp/gh106-smoke/repo, a throwaway git repo (one README commit).
- Pane path: the exact args `pi-role --json agents/<role>.md` prints (what herdr-spawn hands `herdr agent start`), run as `pi <args> --session-dir ... -p <probe>`. Headless path: `pi-role agents/<role>.md --session-dir ... -p <probe>`.

Probe, all 14 role runs:

```
Smoke probe only, do nothing else. Run the codemode tool with the script: return ALL_TOOLS.map(t => t.name).sort().join(","); then reply with exactly two lines: "codemode: <its output>" (or "codemode: none" if you have no codemode tool) and "declared: <your declared tool names, sorted, comma-separated>".
```

Facts below come from the session files (tool calls and tool results), not the self-report. `declared:` is the model's own report, raw: the providers rename Pi tools on the wire (`functions.<name>` for openai, `mcp__require_asset__<x>_<name>` for anthropic; `image_gen.imagegen` and `multi_tool_use.parallel` are openai's own, not Pi tools).

## Results

| Path | Role | `--tools` (pane args) | Base 8451938 | Head d131ddd: codemode tool result |
|---|---|---|---|---|
| headless | qc-judge | | no tool calls, `codemode: none` | `bash,find,grep,ls,read` |
| headless | code-reviewer | | no tool calls, `codemode: none` | `bash,find,grep,ls,read` |
| pane | director | base `read,grep,find,ls,bash`, head `read,grep,find,ls,bash,codemode` | no tool calls, `codemode: none` | `bash,find,grep,ls,read` |
| pane | supervisor | head adds `codemode` | no tool calls, `codemode: none` | `bash,edit,find,grep,ls,read,write` |
| pane | implementer | head adds `codemode` | no tool calls, `codemode: none` | `bash,edit,find,grep,ls,read,write` |
| pane | corrector | head adds `codemode` | no tool calls, `codemode: none` | `bash,edit,find,grep,ls,read,write` |
| pane | code-reviewer | head adds `codemode` | no tool calls, `codemode: none` | `bash,find,grep,ls,read` |

Every head run: exactly one tool call, `codemode({"code": "return ALL_TOOLS.map(t => t.name).sort().join(\",\");"})`, result `Script completed ... Output: <list>`; exit 0. Every base run: no tool call, exit 0.

Raw self-reports, director (anthropic):

```
base: codemode: none
      declared: mcp__require_asset__alone_grep,mcp__require_asset__cradle_ls,mcp__require_asset__dismiss_read,mcp__require_asset__inspire_bash,mcp__require_asset__must_find
head: codemode: bash,find,grep,ls,read
      declared: mcp__require_asset__alone_grep,mcp__require_asset__cradle_ls,mcp__require_asset__deposit_codemode,mcp__require_asset__dismiss_read,mcp__require_asset__inspire_bash,mcp__require_asset__must_find
```

qc-judge headless (openai):

```
base: codemode: none
      declared: functions.bash,functions.find,functions.grep,functions.ls,functions.read,image_gen.imagegen,multi_tool_use.parallel
head: codemode: bash,find,grep,ls,read
      declared: functions.bash,functions.codemode,functions.find,functions.grep,functions.ls,functions.read,image_gen.imagegen,multi_tool_use.parallel
```

roles#acceptance-director-tools: the director's tools are read, grep, find, ls, bash and codemode, and its codemode script lists no edit or write. Same for the code reviewer (pane and headless) and the QC judge. Supervisor, implementer and corrector scripts reach exactly their listed seven.

## Demo (ticket #175), same isolation

`scripts/pi-role agents/qc-judge.md -p 'Run the codemode tool with the script: return ALL_TOOLS.map(t => t.name).sort().join(","); reply with its output only'` (plus `--session-dir`):

```
head: bash,find,grep,ls,read          (one codemode call)
base: The codemode tool is unavailable in this session.   (no tool call)
```

After the runs, only the pi-role docstring and the check-roles message were reworded (owned-rule search: pointers, not restatements); `launch()` is unchanged since d131ddd.

Not shown: a real Herdr pane (replaced by the args herdr-spawn hands it, by order); a codemode script calling a tool (supervisor probe 2026-10-25: nested calls emit their own tool events). Scratch /tmp/gh106-smoke deleted after the runs.
