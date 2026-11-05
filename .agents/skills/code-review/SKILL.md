---
name: code-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) against this repo's documented coding standards. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
---

Standards review of the diff between `HEAD` and a fixed point the user supplies: does the code conform to this repo's documented coding standards?

Anything you would ask the user, escalate instead with `herdr-say --parent`: what is blocked, what you tried, what you need (docs/adr/0015).

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If the brief names none, escalate for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside two parallel sub-agents.

### 2. Identify the standards sources

Search the repo for every file that documents how code should be written. When `CODING_STANDARDS.md` or `CONTRIBUTING.md` exists, it must be on the list.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 3. Run the review

Work from:

- The full diff command and commit list.
- The list of standards-source files you found in step 2, **plus the smell baseline from step 2**.
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

### 4. Verdict (octo-feather)

Report the findings, each marked **block** or **note**, then the verdict: the one line `Verdict: blocking` if any finding blocks, else `Verdict: clear`.

- **Block**: a breach of a documented hard standard of the repo (cite file and rule), a named simplification that lists the lines it deletes, or a test that does not demonstrate the criterion it is tagged with (**Criterion tests**, below).
- **Never a block**: every baseline smell, preferences, and any finding that cannot name a consequence.

**Report fields.** This step owns the form of every report field it names (`Verdict:`, `Check:` or `Checks: none`, `Owner:` or `Owners: none`, `Prior art:`), for every role that reports one, the implementer's check field included (docs/adr/0008 rung 3 names them). Each is a plain line: its label at column 0, then its value, outside code blocks. A report with one check and no owned rule ends:

```
Verdict: blocking
Check: scripts/check-test-surface: tests drive the CLI, never an internal function (AGENTS.md Rules) | reads: tests/*.py import lines | class: proxy
Owners: none
```

`Checks:` takes only `none`: a report with `Check:` lines has no `Checks:` line. Failure examples, each read as a missing or refused field: `## Verdict: blocking`, a heading (gh122 and gh124 reviewers); a bare `Checks:` line heading the `Check:` lines (gh157 implementers, 3 of 3 runs); a bullet or bold label (`- Verdict: clear`, `**Verdict:** clear`).

Then classify every check, and every other decision docs/adr/0008 "Who builds what" classifies, that the diff adds or changes (Check: GLOSSARY.md), one line each, or the one line `Checks: none`:

`Check: <path>: <rule> (<owner>) | reads: <what it reads> | class: exact|proxy`

`<path>` is one path with no spaces: the check's own file (a product command's: the file holding its decision), or `justfile:<recipe>` for a recipe.

`<rule>` (the owned rule), `<owner>`, `exact` and `proxy` are as docs/adr/0008 rung 2 defines them. A proxy check blocks, class `proxy-check`.

**Prior art.** Infrastructure is a parser, test runner, protocol, file format or scheduler. A writer (implementer) reports one line per piece of infrastructure its diff adds or uses, or the one line `Prior art: none` when it touches none:

`Prior art: <library or tool> <pinned version> | released: <latest release date> | activity: <commits or releases in recent months, issue response> | adoption: <downloads or dependents> | license: <license>[ | reason: <why>]`

`Prior art: none found: <what was searched, where> | reason: <why hand-written>`

The chosen library is popular and well maintained: a recent release, commits or releases in recent months, issues answered, real adoption, a license compatible with the repo's, an exact pinned version. A choice failing any of these carries `reason:`.

The reviewer checks each line against the diff and the package index, and blocks, class `reinvented-library`, naming the library or tool to use: hand-written infrastructure where a maintained library or the real tool does the job and no reason is stated (a `reason:`, a comment, the spec), a hand-written replacement for a broken library, a library the diff adds with no line, a fact that is false, or a failing fact with no `reason:`. This holds in any target, whether or not its AGENTS.md states the rule. Failure example: `toml.ts`, a hand-written TOML parser in templates/typescript, cleared review and the owner caught it at the merge ask (#136; smol-toml exists).

**Criterion tests.** For each criterion the lane claims through a tagged acceptance test (the brief's claimed criteria, and any criterion a tag in the diff names; how a test is tagged: the kit's quality spec `#qc-capture`), read the criterion where its spec states it, find every test tagged with it, and judge whether the cases it selects, its assertions, their expected values and its substitutions (a fixture, fake or stub in place of the real thing, a skipped step, a changed flag or input) demonstrate that criterion's observable as the spec words it. Say so in the report, one line per claimed criterion and test: `<spec>#<anchor>: <test>: demonstrates`, or `does not: <what it never asserts or never runs>`. A test that does not blocks, class `criterion-evidence-mismatch`, naming the test and the assertion or input it lacks: a sound test of another behaviour is no evidence for this one. This holds in any target, whether or not its AGENTS.md states the rule. Source: issue #503, consensus item 1 (a tagged regression test is a criterion's evidence, so review judges whether it shows the criterion).

**Duties.** Block, class `prose-duty`, each line of a role file or skill (its patch included) the diff adds or changes that holds a mechanical duty below the tier docs/adr/0008, Duties, gives it (that ADR in the kit, two levels above the folder holding this skill), naming the command, trigger or skill to use instead. This holds in any target, whether or not its AGENTS.md states the rule. Failure example (#269): teardown order, review-row registration, lane-log writes and main-moved broadcasts stayed role prose, and each failed quietly until the owner caught it.

Then, for every rule the diff writes or changes where it is owned (owners: docs/adr/0008 rung 2; terms: GLOSSARY.md), search the whole repo, unchanged files and the diff's other hunks alike, for text that restates the rule instead of pointing to it (docs/adr/0008 rung 1). One line per owned rule, or the one line `Owners: none`:

`Owner: <path>: <rule> | restated: none|<path>:<line>[, <path>:<line>...]`

List every restatement in the first review. A restatement blocks, class `duplicated-rule`, only in a role file (agents/), a skill or its patch (.agents/skills, .skillfile/patches), a spec (docs/specs), an ADR (docs/adr) or AGENTS.md; in a code comment, docstring or test comment it is a non-blocking note: its `Owner:` line still lists it, the merge ask shows it, and it is fixed when that file is next edited (owner ruling 2026-10-27, issue #200). Failure example: lane gh118 wrote docs/adr/0008 rung 2 and, in the same lane, restated it in AGENTS.md, agents/corrector.md and two skills with their patches; review rounds 6 and 7 each found only a share.

Search once per part of the rule: each label, value and term it fixes, one grep each, across docs, comments, docstrings, help text, test headers and eval descriptions. A restatement paraphrases, so one phrase finds a share. Failure example: lane gh157 wrote the report-field reader scope here; its first review found 4 restatements, the next two found 3 more (scripts/octo-feather-qa:333, tests/qa.sh:429, tests/lane-merge-ask.sh:106) and 1 more (evals/ladder/suite.json:4).

A writer (implementer, corrector) runs this same search on its own diff before its commit, points every hit, and ends its report with the same `Owner:` lines or `Owners: none`. A fix round for a `duplicated-rule` finding searches again: the finding's sites are a share. Failure example: gh121, gh152 and gh157 writers each fixed only the listed sites, and the next review found more.

The verdict reader (`octo-feather-lane verdict`) counts `Verdict:`, `Check:` and `Checks:` lines only at column 0, outside a column-0 ``` or ~~~ fence (closed by a column-0 run of the same character, at least as long) and outside a column-0 `>` blockquote with its lazy continuation lines up to a blank line or a column-0 fence. Lists and indented code are not read as containers.
