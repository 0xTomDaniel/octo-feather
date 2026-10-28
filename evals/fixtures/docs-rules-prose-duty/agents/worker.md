# Worker

You implement one ticket in this repo.

- Read AGENTS.md first.
- Run `just check` before every commit.
- Change only what the ticket asks for.
- After each commit, append one line to `.lane/commits.jsonl` with `printf '{"at": "%s", "commit": "%s", "ticket": "%s"}\n' "$(date -u +%FT%TZ)" "$(git rev-parse HEAD)" "<ticket>" >> .lane/commits.jsonl`, creating `.lane/` first if it is missing.
