# gh1340: the merge digest's due days, its sent record, and the director's digest step

Change: `octo-feather-lane digest` with no DAY prints every due day's digest and its sha256 prefix; `digest --sent SHA12`
records it sent (the director's pane only, the sha checked against the remade digest; check class declaration);
`merge` tells the director once when a digest is due and `start` prints the same line; agents/director.md gets the
step: on that line run `digest`, send the owner its text as printed, then `digest --sent`, and write him no merge by
hand, a tier 2 one included (issue-lifecycle #gates-digest, #acceptance-merge-digest; issue 1340). The commands:
`octo-feather-lane --help`, digest; tests: tests/gate/kit/lane_digest.py.

Smoke: agents/director.md, headless director run (pi-role agents/director.md -p) on this lane's uncommitted tree over 06581b77, started 20261128T072808Z, exit 0: on the due line it runs `digest --repo <realcase>`, sends the owner its text as printed, then `digest --repo <realcase> --sent <sha12>` with the printed sha; it writes no message about the tier 2 merge of PR #52 itself, citing "write him no merge by hand, a tier 2 one included".
Smoke: .agents/skills/verify-octo-feather/ `verify-octo-feather drive merge-tiers` on the same tree: every case PASS, the new digest cases among them (digest-merge-tier1 told nothing, digest-merge-tier2 told the due line once, digest, digest-due, digest-sent-refused, digest-sent, digest-none); evidence record 20261128T072748Z-5a97b3b8.

Removed: the director's hand-written tier 2 merge messages to the owner (the owner's option (a), 2026-11-26, a stopgap until the digest existed): agents/director.md now sends merges that waited for nobody only through the digest.

The run had a scratch state dir (XDG_STATE_HOME=/tmp/gh1340smoke/xdg, its commit identity `smoke`) and no route
to any pane (-p); the brief forbids every write, message, octo-feather-lane and gh command.

## Director run

Brief (verbatim):

```
Smoke check, read-only. Do not edit any file, commit, spawn, close or message any agent or pane; run no octo-feather-lane command and no gh command.
The post-merge routine of lane gh50 just told you, in your pane:

merge digest due for 2026-11-28: octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase, send its text to the owner, then octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase --sent <sha12>

Earlier that day lane gh50's supervisor merged PR #52 of 0xTomDaniel/octo-feather-realcase, a tier 2 merge with one clarifying spec call, without the owner.

From your role file only, answer in at most 6 lines:
1. Each command you run, in order, and what you send the owner between them.
2. Do you also write the owner a message about the tier 2 merge of PR #52 yourself? Why or why not?
```

Answer (verbatim):

```
1. Run `octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase`.
   Send the owner its text exactly as printed, nothing added.
   Then run `octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase --sent <sha12>`, using the sha it printed under the text.
2. No. My role file says a merge that waited for nobody reaches the owner only in the digest. It says "write him no merge by hand, a tier 2 one included", so PR #52 reaches him only through the digest.
   The role file sends spec call timing to spec `#gates-call-loudness`, so it doesn't make the clarifying call a reason to write him either.
```
