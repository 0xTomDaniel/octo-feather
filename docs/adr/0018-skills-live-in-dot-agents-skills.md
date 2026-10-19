# Skills live in .agents/skills

Every kit skill, vendored through the Skillfile or authored here, lives in `.agents/skills/<name>/`, and the Skillfile's install-path is `.agents/skills`. `.agents/skills` is the de facto cross-client Agent Skills location: Pi discovers it natively, as do other clients, so a skill sits where every tool already looks and the kit stops carrying two folders (`skills/` local, `agents/skills/` vendored) with their own lookup rules. Vendored skills are the Skillfile's `github` entries; checks that exempt upstream wording derive that list from the Skillfile. Role files stay in root `agents/`. Decided by Tom (owner), 2026-10-18 20:18 MDT.

## Consequences

- Pi auto-discovers `.agents/skills` from the working directory up to the repo root. pi-role always passes `--no-skills` and one `--skill` per listed skill, so a role loads only its own skills, and a role started in a target repo loads none of the kit's skills by discovery (`check-roles` asserts the flags).
- A target repo's own `.agents/skills` is not auto-loaded into roles either; the implementer loads declared `Repo skills:` by name, as before.
- Patches in `.skillfile/patches/skills/<name>/` are keyed by skill name and still apply.
