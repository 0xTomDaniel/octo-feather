# Skills live in .agents/skills

Every kit skill, vendored through the Skillfile or authored here, lives in `.agents/skills/<name>/`, and the Skillfile's install-path is `.agents/skills`. `.agents/skills` is the de facto cross-client Agent Skills location: Pi discovers it natively, as do other clients, so a skill sits where every tool already looks, and one folder holds every skill whatever its source. Vendored skills are the Skillfile's `github` entries; checks that exempt upstream wording derive that list from the Skillfile. Role files live in root `agents/`. Decided by Tom (owner), 2026-10-18.

## Consequences

- Pi auto-discovers `.agents/skills` from the working directory up to the repo root, but pi-role turns discovery off and passes only a role's listed skills (ADR 0016), so a role started in the kit or in a target repo loads nothing by discovery.
- A target repo's own `.agents/skills` is not auto-loaded into roles; which roles load its declared skills, and how: docs/specs/skills.spec.html#loading-listed (corrected in place, issue #184).
- Patches in `.skillfile/patches/skills/<name>/` are keyed by skill name, so the install path does not affect them.
