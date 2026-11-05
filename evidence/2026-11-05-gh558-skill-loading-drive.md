# gh558 review r1: skill-loading verify feature, driven live (#558)

Smoke: .agents/skills/verify-octo-feather/ (`.agents/skills/verify-octo-feather/scripts/verify-octo-feather run skill-loading` at ff1b6a4, clean tree: 7/7 cases PASS; evidence records 20261105T021112Z-327d196f skills#acceptance-launch-refuses-unloaded, 20261105T021112Z-33076e3b skills#acceptance-only-listed, 20261105T021112Z-7e1e381d skills#acceptance-skill-frontmatter)
Removed: none; the incident: review round 1 on PR #570 found the launch refusal unmapped in verify-octo-feather (verification-map-drift) and a declared Repo skill that does not resolve skipped with a warning (unloaded-skill-bypass).

## Change

- `.agents/skills/verify-octo-feather/features/skill-loading.md`, `features/README.md`, `SKILL.md` (feature list), `scripts/verify-octo-feather` (drive_skill_loading): launch cases `offered`, `declared-malformed`, `declared-dangling`, `listed-malformed` (Pi in RPC mode, no prompt, so no model turn; parent route emptied) and gate cases `gate-refused`, `gate-no-name`, `gate-clean` on a scratch kit copy.
- `qc.toml`: the three criteria's demos run this drive.

## Demo

From a scratch target whose AGENTS.md declares `python, ghost`, ghost a dangling link, under env -i with a private home: `pi-role agents/implementer.md --mode rpc --offline --no-session --no-mcp` exits 1:

```
octo-feather: Pi did not load skill ghost (<target>/.agents/skills/ghost/SKILL.md): skill path does not exist
octo-feather: the role does not start (spec skills#loading-refuse)
```
