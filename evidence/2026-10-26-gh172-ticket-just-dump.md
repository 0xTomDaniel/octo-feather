# gh172: ticket check reads recipes via just --dump (s20)

Red before the fix (tests/lane-tickets.sh against scripts/octo-feather-lane at 1f59c0a, gh136's regression):

```
lane-tickets test: 'ticket -' want exit 0, got 1: stdin: class: layer-only-ticket: demo runs no surface the repo declares (`just install-check`: no justfile recipe install-check in /tmp/tmp.cfJlNXKUW2/jrepo); fix: make the demo a backticked command through the
```

Demo after the fix, octo-feather-lane ticket - in a scratch git target (just 1.21.0):

```
$ cat justfile
import "more.just"
alias ic := install-check

check:
    true

[private]
hidden:
    true

[no-cd]
install-check flag="x":
    echo install-check {{flag}}
$ cat more.just
demo:
    echo demo
$ just --dump --dump-format json | jq -c "{recipes: (.recipes|keys), aliases: (.aliases|keys)}"
{"recipes":["check","demo","hidden","install-check"],"aliases":["ic"]}
$ octo-feather-lane ticket - <draft with demo `just install-check`
stdin: ok
exit 0
$ octo-feather-lane ticket - <draft with demo `just demo`
stdin: ok
exit 0
$ octo-feather-lane ticket - <draft with demo `just hidden`
stdin: ok
exit 0
$ octo-feather-lane ticket - <draft with demo `just ic`
stdin: ok
exit 0
$ octo-feather-lane ticket - <draft with demo `just nosuch`
stdin: class: layer-only-ticket: demo runs no surface the repo declares (`just nosuch`: no justfile recipe nosuch in <scratch>); fix: make the demo a backticked command through the repo's ow
exit 1
$ PATH=<git python3 env only, no just> octo-feather-lane ticket - <draft with demo `just demo`
octo-feather-lane ticket: cannot read the justfile's recipes (<scratch>/justfile): just is not on PATH (install it: just install-check): fix it, then rerun
exit 2
$ printf "broken (:\n" >>justfile; octo-feather-lane ticket - <draft with demo `just demo`
octo-feather-lane ticket: cannot read the justfile's recipes (<scratch>/justfile): just --dump: error: Expected '*', ':', '$', identifier, or '+', but found '(': fix it, then rerun
exit 2
```

Fails closed, no fallback: no just on PATH or a justfile just cannot read is exit 2 naming why. Module recipes: `just MOD RECIPE` passes, `just MOD::RECIPE` refused, as just 1.21 runs them (with JUST_UNSTABLE=1; covered in tests/lane-tickets.sh).
