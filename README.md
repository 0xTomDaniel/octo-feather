# octo-feather

Lightweight agentic dev kit: Pi agents in Herdr, one director, spec first, airtight validation gate. See AGENTS.md, docs/adr/, docs/specs/index.spec.html.

## Bootstrap a box

What a box needs and why (host, toolchain, models, review service): docs/specs/remote.spec.html. As your own user, bash, no secret on any command line:

```sh
git clone https://github.com/0xTomDaniel/octo-feather.git ~/src/octo-feather   # the live kit install: it stays on main
cd ~/src/octo-feather
curl -fsSL https://mise.run | MISE_VERSION="v$(cat mise-version)" sh   # mise at its pin, checksum verified, into ~/.local/bin
echo 'export PATH="$HOME/.local/bin:$PATH"; eval "$(~/.local/bin/mise activate bash --shims)"' >> ~/.bashrc
. ~/.bashrc                    # mise's shims first on PATH, here and in every pane
mise install --locked          # node, pnpm, uv, just, shellcheck, scc at mise.lock
uv python install --no-bin     # the gate's Python at .python-version (--no-bin: nothing in ~/.local/bin)
just vendored-fetch            # offline caches the gate reads: vendored skills at their Skillfile pins,
uv sync --locked               # the gate's Python packages
just install-check             # run each fix it prints, then rerun, until it exits 0
just install-check-models      # one short call per role model through Pi (the model key is Pi's config)
GATE_WORKERS=1 just check      # one full gate run, green
just start                     # director in Herdr workspace `director`
```

## Daily

```sh
just check                # the gate
just test -k NAME         # a few of its items (pytest arguments: --lf reruns the last failures)
just start [DIR]          # director in Herdr workspace `director`
just supervise TICKET [WORKTREE]  # supervisor for TICKET (12, ENG-123) in the workspace named by its lane key (gh12, eng-123), tab `supervisor`
```

Derived in part from octo-lite (Sebastian Varela, Apache-2.0); see NOTICE.
