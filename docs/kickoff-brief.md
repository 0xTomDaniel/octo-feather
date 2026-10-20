# Kickoff brief

The owner (or the owner's assistant) fills this in and sends it to the director with `herdr-say` after `just start` and the director's `/goal`, one per `build <spec>`. Every field gets a value; write `none` rather than leaving one out. The director asks the owner about any missing field before it cuts a lane, and copies the tooling, gate, QA and merge fields into every lane brief.

```
BUILD       build <spec path> [<spec path>...]
TARGET      <repo checkout path>, <owner/repo on GitHub>, base branch <main>
            created by the kit from a template: yes | no (brownfield or hand-in repo)
SPEC        <spec path> accepted at <commit> (octo-feather-accepted prints it), review link <url>
TOOLING     the project's own, as found in the repo. Example (Fieldnote): pip and requirements.txt
            in .venv, stdlib unittest; no uv, pyproject.toml, pytest, ruff or formatter it does not
            already have (python and typescript skills: the project's own tooling wins)
GATE        the target's `just check` and what it runs, or the command standing in for it
QA PATH     how a criterion's demo path runs (docs/adr/0002): app CLI, HTTP or UI; or, with none,
            the runnable script (Fieldnote: `python harness.py`); or "QA does not apply", said in the PR
QC          `just qc` where it runs; on macOS it does not: the merge ask says `just qc` not run (macOS)
FACTORY     target not created by the kit: run octo-feather-integrate and octo-feather-qc directly,
            add no `integrate` or `qc` recipe and commit no Spec Chat review state (docs/adr/0017)
MERGES      the director merges nothing, the spec PR included: the owner merges the spec PR,
            and each lane's merge runs as spec #gates-merge says (agents/director.md, Merges)
DEADLINE    <date, time, timezone>; what must be on main by then
DECIDED     owner decisions already made, with pointers
OPEN        open questions, and who answers them
BUDGET      model spend cap for the run, if any
```
