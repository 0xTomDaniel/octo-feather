# gh118 smoke: the ladder (docs/adr/0008) for the corrector

Smoke: agents/corrector.md .skillfile/patches/skills/correct/SKILL.md.patch .agents/skills/correct/
Removed: the `correct` patch's line "can a script decide this without reading meaning? If not, it's an instruction ... not a check" and corrector.md's restatement of it, both replaced by a pointer to the four-rung ladder in docs/adr/0008 and its exact-versus-proxy test (owner direction 2026-10-23; incident: check-test-surface read only facts and still proxied a coupling rule, so "meaning" let it through).

Run, 2026-10-23, branch corrector-gh118 with this change in the worktree: `pi-role agents/corrector.md -p <brief>` headless, isolated (`env -i`, PATH = pi, just, uv only, no herdr, `HERDR_SESSION=gh118-smoke-sandbox`, temp HOME and Pi agent dir, `--session-dir` in the run dir), on a copy of evals/fixtures/python-app on branch corrector-gh9. Brief: finding class `vague-error-message` twice (gh5, gh7), plus an inviting fix "a just check script failing any error message lacking run, use or try"; final message one json block `{"rung", "rule", "reads"}` (the owed rung-choice case, docs/owed-evals/118.md).

Reads, in order: correct SKILL.md, principle-encode-lessons-in-structure SKILL.md, docs/adr/0008-prose-last.md, commit SKILL.md. Commit 09024c1 in the scratch repo, its `just check` green.

Final message (trimmed): `{"rung": "structure", "rule": "User-facing errors must be app.core.AppError(problem, next_step=...) ... I rejected the proposed check for the words run/use/try: it is a proxy under ADR 0008 because it tests words, not whether the message says what to do next ...", "reads": "basedpyright reads the AppError signature ... Whether the next step is actually useful is left to code review"}`. The word check was refused as a proxy by name; the rung chosen was above it, with the meaning left to review.

An earlier run on the fact|meaning wording (same brief, before the owner's exact|proxy direction) also chose `structure` (UserError with a required next_step) and refused the word list as "a word list deciding what a message means".
