# gh1340: the merge digest's due days, its sent record, and the director's digest step

Change: `octo-feather-lane digest` with no DAY prints every due day's digest and its sha256 prefix; `digest --sent SHA12`
records it sent (the director's pane only, the sha checked against the remade digest; check class declaration);
`merge` tells the director once when a digest is due and `start` prints the same line; agents/director.md gets the
step: on that line run `digest`, send the owner its text as printed, then `digest --sent`, and write him no merge by
hand, a tier 2 one included (issue-lifecycle #gates-digest, #acceptance-merge-digest; issue 1340). The commands:
`octo-feather-lane --help`, digest; tests: tests/gate/kit/lane_digest.py.

Smoke: agents/director.md, live director run in a scratch world (review round 2, Block 2), started 20261128T091619Z at 4ad488f8 plus this rework's uncommitted edits, exit 0: the director really ran `octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase`, gave the owner its text exactly as printed (its final reply equals tests/fixtures/merge-digest/2026-11-28-due.txt plus `sha256 f2c56883ddda`, diffed), then ran `octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase --sent f2c56883ddda` from the director's pane, which recorded the sent line below (Live run).
Smoke (earlier, explanation only): agents/director.md, headless director run started 20261128T072808Z: asked what it would do, it named the same steps and no hand-written message about PR #52 (Explanation run, below).
Smoke: .agents/skills/verify-octo-feather/ `verify-octo-feather drive merge-tiers` at 4ad488f8 plus this rework (review round 2: digest, digest-due and digest-sent checked against the worked example tests/fixtures/merge-digest/2026-11-28-day.txt and its literal sha256): every case PASS, the digest cases among them (digest-merge-tier1 told nothing, digest-merge-tier2 told the due line once, digest, digest-due, digest-sent-refused, digest-sent, digest-none); evidence record 20261128T091949Z-f7cd2b23.

Removed: the director's hand-written tier 2 merge messages to the owner (the owner's option (a), 2026-11-26, a stopgap until the digest existed): agents/director.md now sends merges that waited for nobody only through the digest.

## Live run

World (/tmp/gh1340live, scratch, removed after): XDG_STATE_HOME its own state dir, director.toml `pane = "zd9:p1"`, the post-merge record and lane record of lane gh49 as `octo-feather-lane merge 51` wrote them in tests/gate/kit/lane_digest.py's world (the real recording lane-merge-digest-51, merged 2026-11-28 03:29Z), the testkit's gh (tests/gate/kit/testkit/gh.py) first on PATH replaying only lane-digest-1339's two reads (three copies), the testkit's Herdr, the testkit clock at 2026-11-29T08:00:00Z, this worktree's scripts first on PATH. Launch: as a pane launch is (pi-role --json agents/director.md, then `pi <its args> --mode json -p <brief>` with HERDR_PANE_ID=zd9:p1), because a headless `pi-role -p` drops HERDR_PANE_ID by design (pi-role --help, Headless; issue #77): the first try that way ran `digest` and reported `--sent` refused, `only the director records a digest sent`, nothing recorded, no gh call (the guard).

Brief (verbatim):

```
Smoke run in a scratch world: this run's state dir, GitHub (a recorded stand-in) and Herdr are scratch, never live. Do not edit any file, commit, spawn, close or message any agent or pane (no herdr-say). octo-feather-lane and gh run here against the scratch world. The owner reads only your final reply of this run: put there, exactly, whatever you send the owner, and nothing else.

The post-merge routine of lane gh50 just told you, in your pane:

merge digest due for 2026-11-28: octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase, send its text to the owner, then octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase --sent <sha12>

Act on it as your role says.
```

Its commands (from the event stream, in order; reads of help and state aside):

```
octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase
octo-feather-lane digest --repo 0xTomDaniel/octo-feather-realcase --sent f2c56883ddda
```

Owner-facing text (its final reply): the worked example tests/fixtures/merge-digest/2026-11-28-due.txt, then a blank line and `sha256 f2c56883ddda`, byte for byte (diff empty). gh's log (the digest, then the --sent remake):

```
repo view 0xTomDaniel/octo-feather-realcase --json defaultBranchRef
pr list --state merged --base main --search merged:2026-11-27..2026-11-29 --limit 1000 --json number,title,url,mergedAt,mergeCommit,headRefOid -R 0xTomDaniel/octo-feather-realcase
repo view 0xTomDaniel/octo-feather-realcase --json defaultBranchRef
pr list --state merged --base main --search merged:2026-11-27..2026-11-29 --limit 1000 --json number,title,url,mergedAt,mergeCommit,headRefOid -R 0xTomDaniel/octo-feather-realcase
```

The director log after it:

```
{"at": "2026-11-29T08:00:01Z", "kind": "digest", "repo": "0xTomDaniel/octo-feather-realcase", "days": ["2026-11-28"], "prs": [51, 52, 53], "sha256": "f2c56883dddae63e4bdff4eb940073f26a101be748adc0c734405e4cacc7ffbf", "sent": true}
```

## Explanation run

The explanation run had a scratch state dir (XDG_STATE_HOME=/tmp/gh1340smoke/xdg, its commit identity `smoke`) and
no route to any pane (-p); its brief forbids every write, message, octo-feather-lane and gh command.

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
