## Parent

#40

## What to build

Every lane's tickets are checked as tracer bullets by a kit command, so a layer-only ticket cannot be filed silently. `octo-feather-lane tickets <parent issue>` reads every sub-issue of the parent through `gh` (works under the qc judge's offline gh) and `octo-feather-lane ticket <body file or ->` checks one draft before publishing. A ticket passes when its acceptance criteria name at least one `<spec slug>#<anchor>` that exists in `docs/specs/<slug>.spec.html`, and its last acceptance item is `demo:` with a backticked command other than the gate alone (`just check`); or when it carries the stated wide-refactor exception line `Expand-contract: expand|migrate|contract` (to-tickets' expand-and-contract sequence), which waives the demo. Each failure names the ticket and the fix. The vendored `to-tickets` skill (through a `.skillfile/patches` change) puts criterion ids and the demo line in its issue template and runs the check on each draft before publishing (ADR 0008 smoke + owed eval).

## Acceptance criteria

- [ ] issue-lifecycle#story-tracer-tickets: `tests/lane-tickets.sh` (run by `just check`, fake gh) proves a parent whose tickets all name criteria and end on a demo passes; #10's body (layer-only, `demo: just check green`) fails naming `layer-only-ticket` and the fix; a ticket naming no criterion or an unknown anchor fails; an `Expand-contract:` ticket passes without a demo
- [ ] issue-lifecycle#story-tracer-tickets: to-tickets patch: issue template carries criterion ids and the demo line, and the publish step runs `octo-feather-lane ticket` first; `evidence/` smoke and `docs/future.md` owed eval in the same diff
- [ ] demo: `octo-feather-lane tickets 40` exits 0 on this lane's own sub-issues, and `octo-feather-lane tickets 8` (#10's parent) exits 1 naming #10

## Blocked by

- #46


## Skills

Skills: none
