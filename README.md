# octo-feather

Lightweight agentic dev kit: Pi agents in Herdr, one director, spec first, airtight validation gate. See AGENTS.md, docs/adr/, docs/plan.md.

```sh
just install-check        # herdr, pi, gh, jq, git, just on PATH; gh signed in
just check                # the gate
just start [DIR]          # director in Herdr workspace `director`
just supervise N [WORKTREE]  # supervisor for GitHub issue N in workspace `gh<N>`, tab `supervisor`
```

Derived in part from octo-lite (Sebastian Varela, Apache-2.0); see NOTICE.
