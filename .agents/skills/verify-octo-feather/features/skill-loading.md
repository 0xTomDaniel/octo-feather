# skill-loading

Criteria:

- [skills#acceptance-launch-refuses-unloaded](../../../../docs/specs/skills.spec.html#acceptance-launch-refuses-unloaded)
- [skills#acceptance-only-listed](../../../../docs/specs/skills.spec.html#acceptance-only-listed)
- [skills#acceptance-skill-frontmatter](../../../../docs/specs/skills.spec.html#acceptance-skill-frontmatter)

Drive criterion: `skills#acceptance-launch-refuses-unloaded`
Drive criterion: `skills#acceptance-only-listed`
Drive criterion: `skills#acceptance-skill-frontmatter`

## Sub-features

- `offered` the implementer's launch in a target declaring `python` and its own valid skill `local`: starts, and Pi's loaded skills are exactly the role file's `skills:` list (`{tracker}` as `github-issues`), `local` not among them.
- `own-copy` the implementer's launch in a target that holds and declares its own copy of `python`, a skill its role lists: starts, offered exactly its listed skills, `python` once, from the target's copy.
- `declared-malformed` a target whose declared skill's description is invalid YAML: refused, naming it and Pi's reason.
- `declared-dangling` a target whose declared skill is a dangling link: refused, naming it and why.
- `listed-malformed` a scratch kit copy whose `tdd`, listed by the implementer, is invalid YAML: refused, naming it and Pi's reason.
- `gate-refused`, `gate-no-name`, `gate-clean` `check-skills` on that copy: the broken `tdd` fails naming the skill and each role listing it; a skill with no name fails naming it; the copy restored passes.

## How to get to it (user POV)

- A supervisor starts a role in a target: `pi-role agents/<role>.md` (headless with `-p`, or a pane through `herdr-spawn --role <role>`); a maintainer runs the gate, `just check` (its `check-skills`). The rule: [skills#loading-refuse](../../../../docs/specs/skills.spec.html#loading-refuse); the launch: `pi-role --help`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- `pi` on PATH (the kit's pin, `pi-version`).

Run: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive skill-loading` (or `run skill-loading`). Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/skill-loading/`.

Each launch case runs, from a scratch git target under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/skill-loading/targets/<case>`, `pi-role <kit>/agents/implementer.md --mode rpc --offline --no-session --no-mcp` with its RPC input on stdin (`offered`, `own-copy`: one `get_commands`; the others: none), `HOME`, `PI_CODING_AGENT_DIR` and `XDG_CACHE_HOME` scratch. The gate cases run the copy's `scripts/check-skills`.

- **Each launch case.** Observe the exit code and, for a refusal, `Pi did not load skill <name> (` and the reason on stderr; for `offered`, the `get_commands` response's skills against `offered.obs.role-skills`; for `own-copy`, the same, and `python`'s one path against `own-copy.obs.target-python`.
- **Each gate case.** Observe the exit code and the stderr lines naming the skill and roles.
- **Side effects.** Every case cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- RPC mode with no prompt: Pi starts, runs its session start and exits at end of input, so no model turn is possible, refused or not, and the scratch agent dir holds no credentials. That a refusal comes before a headless `-p` run's first request is tests/gate/kit/test_skills_loaded.py's (a fake provider, zero requests).
- A pane launch also tells its parent (`herdr-say --parent`); the drive empties `OCTO_FEATHER_PARENT` and the Herdr pane ids, so no live pane is told. The parent message is tests/gate/kit/test_skills_loaded.py's, through the kit's herdr-say over the testkit's Herdr stand-in.
