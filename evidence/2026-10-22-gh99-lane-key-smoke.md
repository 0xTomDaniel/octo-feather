# Lane key per tracker smoke, issue #99 (lane gh82), 2026-10-22

ADR 0008; owed evals in docs/owed-evals/99.md. Spec roles#lane-key, #acceptance-supervise-layout-linear.

## herdr-comms Layout, read by a real headless supervisor

Smoke: .agents/skills/herdr-comms/SKILL.md

Real pi, `scripts/pi-role agents/supervisor.md -p` (worktree kit), run in a throwaway git target with
`tracker = "linear"` (so the supervisor got github-pr and linear). Same prompt both runs:

> Smoke probe, no task. Run no command and message no one. From your herdr-comms skill Layout section only: in
> this target (its tracker is Linear), what Herdr workspace holds the lane for Linear ticket ENG-123, which tab is
> the supervisor, and the exact octo-feather-start command line that starts it for worktree /w? Answer in three
> lines: workspace=..., tab=..., command=...

Before (Layout as at d814b08, `gh<n>` only), 23:49:08 to 23:49:20 UTC, final message verbatim:

```
I read only the skill file; I ran no commands and messaged no one. The Layout section only covers GitHub-style issue numbers, so it can't fully answer this for a Linear ticket:

workspace=not defined for Linear. Layout only gives `gh<n>` (a GitHub issue number) and says nothing about how ENG-123 maps to a workspace name. Calling it `gh123` would be a guess.
tab=supervisor
command=not defined for Linear. Layout only gives `octo-feather-start --issue <n> --cwd <worktree>`, which would be `octo-feather-start --issue <n> --cwd /w`, but it doesn't say what `<n>` is for ENG-123.

The linear skill says it names lane keys, so it probably has the mapping, but I didn't open it because you limited me to the Layout section.
```

After (this change), 23:48:52 to 23:49:03 UTC, final message verbatim:

```
workspace=eng-123
tab=supervisor
command=octo-feather-start --issue ENG-123 --cwd /w
```

Result: pass. One sample per side, no director or live lane run.

## Demo: octo-feather-start under the test herdr

Fake herdr `tests/fixtures/herdr-say/herdr` first on PATH (stateful: workspace create makes w8 with seed tab
w8:t1, tab create makes w8:t9). `$TARGET` is a throwaway git repo: `lin` has `tracker = "linear"`, `ghr` has no
config (github). stderr dropped (pi-role's external-skill skip notes and octo-feather-exclude's line).

```
$ scripts/octo-feather-start --issue ENG-123 --cwd $TARGET   # lin
workspace=w8 name=eng-123 role=supervisor tab=w8:t9 pane=w8:p9 cwd=/tmp/d99/lin contract=pi-role provider_session_id=a96181fd-092d-48c5-b7dc-400811a19340
exit=0
$ scripts/octo-feather-start --issue 12 --cwd $TARGET   # ghr
workspace=w8 name=gh12 role=supervisor tab=w8:t9 pane=w8:p9 cwd=/tmp/d99/ghr contract=pi-role provider_session_id=3816af4b-c014-47a5-b4a1-1505e81c340a
exit=0
```

Fake herdr calls (cut to 60 chars):

```
workspace create --label eng-123 --cwd /tmp/d99/lin --no-foc
tab create --workspace w8 --label supervisor --cwd /tmp/d99/
agent start eng-123 --kind pi --pane w8:p9 -- --approve --mo
tab close w8:t1
workspace create --label gh12 --cwd /tmp/d99/ghr --no-focus
tab create --workspace w8 --label supervisor --cwd /tmp/d99/
agent start gh12 --kind pi --pane w8:p9 -- --approve --model
tab close w8:t1
```

One workspace each, one tab `supervisor`, seed tab closed. Pinned by tests/start.sh; integrate by
tests/integrate.sh (ENG-123 lands on eng-123, never eng-1230 or eng-123-x); call-log lane by tests/spec-status.sh.
