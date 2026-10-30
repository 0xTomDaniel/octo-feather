# gh406: just qc gives insufficient evidence as a blocking result; verify-octo-feather drives it (qc-insufficient)

Change: `just qc` gives a criterion whose declared demo did not run to its end (exit 77, 126, 127 or above 128) the result insufficient evidence naming what is missing, planned, never FAIL, exit 2; `octo-feather-lane merge-ask` fails naming it (ebe897a). The verify-octo-feather skill gains the `qc-insufficient` feature: features/qc-insufficient.md (Drive criterion line `quality#acceptance-qc-insufficient`), its features/README.md index line and the SKILL.md description naming just qc's merge-ask (behavioural, 08f1797); SKILL.md Contract and Drive list pointers (Behaviour-neutral, 11f2d19).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (description names `just qc on a scratch target and its merge-ask`; run below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line for qc-insufficient; run below)
Smoke: .agents/skills/verify-octo-feather/features/qc-insufficient.md (the recipe the run below follows)
Removed: nothing.

## Recorded live run at head 08f1797

Clean tree at 08f1797 (implementer-gh406; gh127 tip 02859b9 already in it), run and evidence folders in scratch (`VERIFY_OCTO_FEATHER_RUN_DIR`, `VERIFY_OCTO_FEATHER_EVIDENCE_DIR` under mktemp), drive records to the kit's real store. Command, as SKILL.md and features/qc-insufficient.md give it:

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run qc-insufficient
```

Exit 0. `verify-octo-feather: ready: ... rev=08f1797`. summary.txt:

```
qc-insufficient @ rev 08f1797, 2026-10-29T19:49:48Z
PASS qc: XDG_STATE_HOME=<run>/scratch/qc-insufficient/state env -C <run>/scratch/qc-insufficient/repo just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a
PASS merge-ask: XDG_STATE_HOME=<run>/scratch/qc-insufficient/state OCTO_FEATHER_GHSNAP=<run>/scratch/qc-insufficient/ghsnap PATH=<kit>/.agents/skills/github-pr/scripts:$PATH env -C <run>/scratch/qc-insufficient/repo octo-feather-lane merge-ask 7 --status docs/specs/demo.status.json
PASS qc-insufficient
```

`qc` stdout, exit 2 (scratch target head 3296a8165e73):

```
INSUFFICIENT EVIDENCE acceptance-a: $ gh api user >/dev/null || { echo "needs GitHub: gh api user, refused in the qc sandbox" >&2; exit 77; }; echo demo checks pass
  missing: demo did not run to its end (exit 77, a step it needs could not run here): needs GitHub: gh api user, refused in the qc sandbox
  evidence incomplete; decision demo checks; record 20261029T194950Z-d3dc3086
qc: insufficient evidence, never a failure to triage: acceptance-a (planned; merge-ask fails naming them until a rerun of just qc gives each pass or fail)
qc: 0/1 passed at 3296a8165e73; offline gh refusals 0; head now 3296a8165e73; report <run>/scratch/qc-insufficient/state/octo-feather/qc/3296a816...-20261029T194948Z-d3a3fa.json
```

`qc.obs.after`: `3296a8165e73703bc5f0c9d897f04a6cec76ec6d planned clean` (head unchanged, no status commit, acceptance-a planned, worktree clean).

`merge-ask` stderr, exit 1, stdout empty (its merge ask lists the criterion as `fail` with a triage line):

```
octo-feather-lane merge-ask: PR #7 merge ask incomplete (4 items), head 3296a8165e73:
  - criterion demo#acceptance-a: insufficient evidence at the judged head 3296a8165e73 (demo did not run to its end (exit 77, a step it needs could not run here): needs GitHub: gh api user, refused in the qc sandbox; qc report 3296a8165e73703bc5f0c9d897f04a6cec76ec6d-20261029T194948Z-d3a3fa.json): never triaged; make what is missing available, then rerun just qc on it until it gives pass or fail
  - Judged: missing; add the check's proof line `Judged: 3296a8165e73 is the PR head`
  - Review verdict: missing; run `octo-feather-lane verdict 7 3296a8165e73 <report>` and add `Review verdict: <the URL it prints>`
  - Built: no `qc: built` commit on PR #7; run just qc on the lane head (docs/adr/0022)
```

The drive's own record, read back with `octo-feather-evidence read --criterion quality#acceptance-qc-insufficient --commit 08f1797` in the kit:

- `20261029T194950Z-12427e7a`: quality#acceptance-qc-insufficient, revision 08f1797880ab, clean, text from spec, contract qc.toml format 1, 14 outputs.

Agent run (a role reading the skill and choosing this drive): no `just qa` case; owed, with the reason, in docs/owed-evals/406.md.
