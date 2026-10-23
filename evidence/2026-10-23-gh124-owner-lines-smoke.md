# gh124 smoke: code reviewer sends every restatement of an owned rule (`Owner:` lines); writing-for-agents points to the owner

Smoke: agents/code-reviewer.md .skillfile/patches/skills/code-review/SKILL.md.patch .agents/skills/code-review/
Smoke: .skillfile/patches/skills/writing-for-agents/SKILL.md.patch .agents/skills/writing-for-agents/
Removed: nothing from the reviewer's rules; adds the `Owner:` / `Owners: none` lines and their send. Incident: class `duplicated-rule`, lane gh118 (archive gh118.handoffs.jsonl lines 70 and 79, PR #120 review rounds 6 and 7, fixes 61e2b8e and 5ad7429): restatements written in the same lane as the owner text, each round finding only a share.
Removed: writing-for-agents Pruning, the skill's own statement of the one-place rule ("Keep each meaning in a single source of truth: one authoritative place, so changing the behaviour is a one-place edit"), now a pointer to docs/adr/0008 rung 1. Incident: PR #126 review, class `duplicated-rule` (two owners of one rule).

Owed eval: docs/owed-evals/124.md. Result: runs 1 and 3 (before) FAIL, runs 2 and 4 (after) PASS.

## Harness (all runs)

- Kits: before = `git archive 78a097d` (main, the gh124 base) into `<scratch>/kit-before`. After = this worktree (branch corrector-gh124) with this change.
- Fixture: scratch git repo. `main` holds:
  - AGENTS.md, with the rule "Each rule is stated once, where it is owned; every other file points to it";
  - docs/adr/0001;
  - README.md, saying "the error should tell the user which command fixes it";
  - agents/worker.md and src/app.py.

  Branch `lane-gh5` adds `docs/adr/0002-errors-name-the-fix.md` (errors name the fix command, usage errors exit 2). The same commit restates the rule in `AGENTS.md:9` and `agents/worker.md:5` and changes src. README.md is unchanged: a prior restatement the new ADR now owns. One fresh clone per run.
- Sandbox: `env -i`, with only these variables:
  - `PATH=<scratch>/bin:/usr/local/bin:/usr/bin:/bin`, where `<scratch>/bin` holds `pi`, `fd` and a stub `herdr-say`;
  - `HOME=<scratch>/home` (copies of Pi's `models.json` and `auth.json`);
  - `XDG_STATE_HOME=<scratch>/state` and `GH_CONFIG_DIR=<scratch>/ghcfg` (empty);
  - `HERDR_SESSION=gh124-sandbox`, `RUN=<run>`, `PI_CODING_AGENT_SESSION_DIR=<scratch>/sess-<run>`, `TERM`, `LANG`, `PI_SKIP_VERSION_CHECK=1`.

  Checked first: `herdr`, `octo-feather-state` and `gh` not found; no `HERDR_*` or `OCTO_FEATHER_*` variable. No live pane touched.
- Stub `herdr-say` records every call's args (and stdin when piped) to `<scratch>/sent-<run>.log`, prints `sent` and exits 0:

```
#!/bin/bash
f=/tmp/gh124/sent-$RUN.log
{ printf '=== call %s\n' "$(date -u +%T)"; for a in "$@"; do printf -- '--- arg\n%s\n' "$a"; done
  if [ ! -t 0 ]; then printf -- '--- stdin\n'; cat; fi; } >> "$f"
echo "sent"; exit 0
```

- Box: before runs 1 and 2, 6.5 GB available and no other pi-role -p run; runs 3 and 4 likewise. Each pair ran in parallel, rc 0.

## Runs 1 and 2: code reviewer, the Owner: lines reach the supervisor

- Command (cwd the clone): `env -i <sandbox> timeout -k 30 1200 <kit>/scripts/pi-role <kit>/agents/code-reviewer.md -p "Review lane gh5, ticket #5 (no tracker access in this run; the diff is the ticket), diff main...lane-gh5 (this worktree). Your supervisor is your --parent."`. Model `openai/gpt-6.1-sol`, thinking high.
- Grader: the owed eval's three conditions, mechanically. It reads every stub-recorded send and keeps the column-0 lines outside code fences. It needs `Owner:` lines whose path, with any `:<line>` suffix stripped, is `docs/adr/0002-errors-name-the-fix.md`, and whose `restated:` union holds `AGENTS.md`, `agents/worker.md` and `README.md`:

```
import re,sys
t=open(sys.argv[1]).read()
sends=t.split('=== call ')[1:]
if not sends: print('FAIL: no send'); sys.exit(1)
lines=[];fence=False
for s in sends:
    for l in s.split('\n'):
        if re.match(r'\s{0,3}(```|~~~)',l): fence=not fence; continue
        if not fence: lines.append(l)
own=[l for l in lines if l.startswith('Owner:')]
ADR='docs/adr/0002-errors-name-the-fix.md'
mine=[l for l in own if re.sub(r':\d+$','',l[6:].split(': ',1)[0].strip())==ADR]
if not mine: print(f'FAIL: no Owner: line for {ADR} ({len(own)} Owner lines)'); sys.exit(1)
got=set()
for l in mine:
    r=l.split('| restated:',1)[1] if '| restated:' in l else 'none'
    got|={re.sub(r':\d+$','',x.strip()) for x in r.split(',') if x.strip()!='none'}
need={'AGENTS.md','agents/worker.md','README.md'}
print(('PASS' if need<=got else 'FAIL: missing '+','.join(sorted(need-got))), len(mine),'Owner lines, restated',sorted(got)); sys.exit(0 if need<=got else 1)
```

### Run 1: before (kit 78a097d): FAIL

One `herdr-say --parent` send. Grader: `FAIL: no Owner: line for docs/adr/0002-errors-name-the-fix.md (0 Owner lines)`. Send (trimmed):

```
Lane gh5, ticket #5. Verdict: blocking
Checks: none

Block [class: duplicated-rule]: AGENTS.md:9 and agents/worker.md:5 restate the error-message and exit-status rule owned by docs/adr/0002-errors-name-the-fix.md:3. ...
```

The unchanged `README.md:5` is missed: the gh118 shape, where each round found only a share.

### Run 2: after (this change): PASS

One `herdr-say --parent` send. Grader: `PASS 2 Owner lines, restated ['AGENTS.md', 'README.md', 'agents/worker.md']`. Send (trimmed):

```
Block [class: duplicated-rule]: AGENTS.md:9 and agents/worker.md:5 restate ADR 0002 instead of linking; README.md:5 also restates its fix-command rule. ...
Checks: none
Owner: docs/adr/0002-errors-name-the-fix.md:3: every error names its repair command | restated: AGENTS.md:9, agents/worker.md:5, README.md:5
Owner: docs/adr/0002-errors-name-the-fix.md:3: usage errors exit 2 | restated: AGENTS.md:9, agents/worker.md:5
...
Checked: ... whole-repo rule restatement search. ...
```

Not graded: the verdict label, which this change does not own. Run 1 wrote `Verdict: blocking`; run 2 wrote `Verdict: blocked.` mid-line, and the supervisor writes the helper's `Verdict:` line. `scripts/octo-feather-lane verdict` matches only `^Check:` and `^Checks:`, so `Owner:` lines pass into the comment's findings body untouched.

## Runs 3 and 4: writing-for-agents names the rule's owner

- Command (cwd a fresh clone): `env -i <sandbox> timeout -k 30 900 <kit>/scripts/pi-role <kit>/agents/corrector.md -p "<brief>"`. The corrector is the role that loads `writing-for-agents`. Model `anthropic/claude-opus-5-5`, thinking medium.
- Brief: `Probe run, not a correction lane: edit nothing, run no git command, message no one. Read the writing-for-agents skill (path from your skill list) and find its Pruning rule on duplication. Final message: exactly one fenced json block {"owner_of_one_place_rule": "<the path and section that rule names as its owner, or \"this skill\" if the skill states the rule itself without naming another owner>", "quote": "<the skill line, verbatim, first 120 chars>"}.`
- Graded on the declared field `owner_of_one_place_rule`: pass when it is `docs/adr/0008 rung 1`.
- Run 3, before (kit 78a097d): FAIL. `{"owner_of_one_place_rule": "this skill", "quote": "- Keep each meaning in a **single source of truth**: one authoritative place, so changing the behaviour is a one-place e"}`. The skill was a second owner of the rule.
- Run 4, after: PASS. `{"owner_of_one_place_rule": "docs/adr/0008 rung 1", "quote": "- **Single source of truth**: docs/adr/0008 rung 1. **Duplication** (the same meaning in more than one place) costs main"}`.

## Owner: sweep of this lane's own diff

The owned rule this lane writes is docs/adr/0008 rung 1: a rule is stated once, other files point to it. I ran `git grep -n -i -E 'stated once|owned once|one owner|single source|one authoritative|source of truth|never restate|do not restate|instead of restating|points? (to it|there)'` over the repo, excluding docs/owed-evals, evidence and docs/specs. What it found:

- writing-for-agents:78: was a second owner; now a pointer (this commit).
- The code-review Verdict step: carried the gloss "one owner per rule"; now the bare pointer `(docs/adr/0008 rung 1)`.
- Not restatements. Each points to one named owner for one specific rule:
  - agents/director.md:39 and :140, agents/supervisor.md:28, :62, :63 and :81, github-pr:76 and implement-spec step 7 ("read it there, never restate it");
  - docs/adr/0007:7 (the merge rule "is stated once, in spec `#gates-merge`");
  - justfile:103 (the lane branch, owned by docs/adr/0011).
- Not about rules: the correct skill step 1 ("one source of truth" for lists and state, the general rung 1 wording), interrogate's "Each dimension is stated once", and writing-for-agents:79 (the environment as a source of truth).

```
Owner: docs/adr/0008-prose-last.md: a rule is stated once where it is owned, other files point to it | restated: none
```
