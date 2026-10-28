# gh256: agent-browser for the implementer and corrector (issue #256, ticket #263)

Change: Skillfile vendors vercel-labs/agent-browser@c3880a7 (release v0.40.0) `skills/agent-browser`, materialized by the pinned skillfile v1.9.2; .skillfile/patches/skills/agent-browser/SKILL.md.patch drops `allowed-tools`, `hidden` and the description's last sentence; agents/implementer.md and agents/corrector.md list `agent-browser`; agent-browser-version pins 0.40.0 and `just install-check` checks it. Box: `sudo npm install -g agent-browser@0.40.0` (rollback `sudo npm rm -g agent-browser`); it starts Playwright's Chromium in ~/.cache/ms-playwright/chromium-1248 on its own (`agent-browser doctor`: Chrome pass, launch test pass), so no second browser download.

Prompt for the role runs: `Use agent-browser to open https://example.com and reply with three lines only: the page title, the number of paragraphs the rendered page shows, and the output of agent-browser --version`. Live, network on, real model, single samples. https://example.com's raw HTML holds one `<p>` and no `<h1>` today; its script adds the translated paragraphs, so 6 comes only from a rendered page (`curl` shows 1).

Smoke: agents/implementer.md (`scripts/pi-role agents/implementer.md -p --mode json <prompt>`: exit 0, 17 s; read .agents/skills/agent-browser/SKILL.md, ran `agent-browser skills get core`, `agent-browser open https://example.com`; final `Example Domain` / `6` / `agent-browser 0.40.0`)
Smoke: agents/corrector.md (same prompt with agents/corrector.md: exit 0, 17 s; same skill read and commands; final `Example Domain` / `6` / `agent-browser 0.40.0`)
Smoke: .agents/skills/agent-browser/ (the two runs above load it; `just qa --suite skill-triggers --case <id>` for its 8 new cases, impl-browser-* and cor-browser-*: 8/8 PASS with this change's role and skill files)
Smoke: .skillfile/patches/skills/agent-browser/ (`just check-vendored`: 21 skills equal authenticated upstream at pin plus patches)
Removed: upstream's `allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*)` and `hidden: true` frontmatter (another runtime's keys, docs/adr/0001) and its description sentence `Prefer agent-browser over any built-in browser automation or web tools.` (web search and fetch stay with the web tools, docs/adr/0016).

Base (7a98d62, the commit before this change): `just qa --suite skill-triggers --case impl-browser-rendered-banner --kit-ref 7a98d62` FAIL (no load of agent-browser, 9 tool calls) and `--case cor-browser-visible-paragraphs --kit-ref 7a98d62` FAIL (5 tool calls): neither role has the skill there. Owed evals: docs/owed-evals/256.md.

Demo note: the ticket's demo prompt (`reply with the page's main heading only`, expecting `Example Domain`) got `The page has no main heading ... The closest thing is the page title, "Example Domain".` (exit 0, 20 s): the live page has no heading element, so the title is the honest answer.
