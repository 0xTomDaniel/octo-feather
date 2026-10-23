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

Report the findings, each marked **block** or **note**, then one verdict: blocked if any finding blocks, else clear.

- **Block**: a breach of a documented hard standard of the repo (cite file and rule), or a named simplification that lists the lines it deletes.
- **Never a block**: every baseline smell, preferences, and any finding that cannot name a consequence.

Then classify every check the diff adds or changes (Check: GLOSSARY.md), one line each at column 0 outside code blocks, or the one line `Checks: none`:

`Check: <path>: <rule> (<owner>) | reads: <what it reads> | class: exact|proxy`

`<path>` is one path with no spaces: the check's own file, or `justfile:<recipe>` for a recipe.

- **exact**: it tests the rule itself. `<rule>` is the rule as stated where it is owned and `<owner>` names that place (a spec criterion id, an ADR, a recorded owner ruling), never the check's own docstring or error; when owners conflict, the latest owner ruling wins. A case escaping an exact check is a defect to fix, still exact.
- **proxy**: it tests a stand-in that correlates with the rule, however factual what it reads (code tokens for coupling, words for reachability, a regex over prose for intent). A proxy check blocks, class `proxy-check` (docs/adr/0008): `scripts/check-test-surface` read six real module-loading tokens to enforce "tests reach no internals", and tests coupled to internals in other ways kept passing it.
