# octo-feather

Lightweight agentic dev kit: Pi agents in Herdr, one director, spec first, airtight validation gate. See AGENTS.md, docs/adr/, docs/specs/index.spec.html.

```sh
just install-check        # herdr, pi, gh, jq, git, just on PATH; gh signed in
just vendored-fetch       # once per Skillfile pin: the cache check-vendored reads offline
uv sync --locked          # once per uv.lock: pytest and pytest-xdist into the uv cache the gate reads offline
just check                # the gate
just test -k NAME         # a few of its items (pytest arguments: --lf reruns the last failures)
just start [DIR]          # director in Herdr workspace `director`
just supervise TICKET [WORKTREE]  # supervisor for TICKET (12, ENG-123) in the workspace named by its lane key (gh12, eng-123), tab `supervisor`
```

Derived in part from octo-lite (Sebastian Varela, Apache-2.0); see NOTICE.
