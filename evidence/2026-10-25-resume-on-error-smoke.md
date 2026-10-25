# resume-on-error smoke, 2026-10-25 (issue #152, docs/adr/0023)

Box, Pi 1.3.0 (`pi-version`), lane gh152. Every run below is one real Pi at a time against a fake OpenAI-compatible provider on 127.0.0.1 (503 for its first N requests, then an answer), Pi's retries off, a fake `herdr-say` recorder first on PATH.

## Abort probe: why the wait left agent_before_settle

Probe extension sleeping 5 s inside `agent_before_settle` on an error, Pi in RPC mode, `{"type":"abort"}` sent 1.5 s in:

```
PROBE settle outcome=error signal=false aborted=undefined
PROBE slept 5003 aborted=undefined
PROBE settled {"type":"agent_settled","aborted":true}
```

Polled every 100 ms during the sleep, `ctx.signal` stayed undefined, `ctx.isIdle()` false, `ctx.hasPendingMessages()` false. Pi gives that handler no abort signal, so the resume timer now starts from `agent_settled`, with Pi idle.

## tests/resume-on-error.sh (in `just check`)

At the lane head, inside `just check` (green):

```
case recovers: ok (2 provider errors, 2 resumes, finished, parent not messaged)
case down: ok (4 requests, 3 resumes, then stopped; one parent line: --parent implementer (pane fake:p9, repo) stopped on a provider error after 3 resume round(s): 503: {"message":"fake upstream overloaded","type":"overloaded_error"})
case normal: ok (1 request, no resume, parent not messaged)
case idle: ok (mid-backoff isStreaming false, abort answered in 0.00s)
case takeover: ok (takeover answered 0.51s after the error, no resume after the 3 s backoff, parent not messaged)
case headless: ok (pi-role -p exit 1 in 0s, 1 request, no resume, nothing sent)
resume-on-error: ok (pi 1.3.0, empty HOME and environment, no provider credential)
```

CI stand-in: Pi installed as CI does (`npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.3.0` into a temp prefix), run with `unshare -rn` (no network but loopback), `env -i HOME=<empty dir> PATH=<npm prefix>/bin:/usr/bin:/bin`: the same seven lines, exit 0.

The same test at main `bfb5bc8` (with `pi-version` copied in): `recovers: timed out waiting for a settle after the provider's answer`, exit 1. At the first build `243829b` (wait inside `agent_before_settle`): `recovers: 3 requests, 0 resumes; want 3 and 2`, exit 1.

Fail closed: `PATH=/usr/bin:/bin` (no pi): `pi not on PATH; install Pi 1.3.0: npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.3.0`, exit 1. A pi reporting 1.2.0: `pi reports 1.2.0, the kit pins 1.3.0 (pi-version); npm install ...@1.3.0`, exit 1.

## Interactive pane (tmux, TUI mode)

`scripts/pi-role agents/supervisor.md --model fake/fake --no-session 'do the task'`, provider always failing, `OCTO_FEATHER_RESUME_DELAYS=1,2,3`, empty environment and HOME:

```
t=2.5s requests=2 (mid-backoff of round 2)
t=9.5s requests=4
said: --parent supervisor (pane fake:p7, repo) stopped on a provider error after 3 resume round(s): 503: {"message":"fake upstream overloaded","type":"overloaded_error"}
```

The pane showed each `[octo-feather-resume]` message, "Resume round 1 of 3" to "3 of 3", each followed by the 503 error, then the idle editor.

## Headless short path

`pi-role ... -p` against a provider that keeps failing: exit 1 within the second, 1 provider request, no kit resume, nothing sent (Pi's own retries off in the test; with defaults Pi's 3 bounded retries run first, docs/adr/0023 Headless).
