---
name: github-issues
description: The tracker skill for a target whose tickets live in GitHub Issues; read, file, comment on and close tickets, and name lane keys, only through its scripts.
---

# GitHub Issues tracker

Be extremely concise. No em-dashes or en-dashes. Ever.

The target's tickets live in GitHub Issues (`tracker = "github"` in its
`.octo-feather.toml`, or no tracker set; docs/adr/0004). Every lane ticket
operation goes only through the scripts below, by path:
`<this skill's folder>/scripts/<name>`. Each wraps one `gh` command, prints
only its output, and on failure exits non-zero with the reason. For any other
read, use `gh`'s own help (`gh issue --help`); never write a ticket another way.

A key is the issue number, `82`.

| Script | Does | Prints |
| --- | --- | --- |
| `lane-key ID` | Lane key for an issue as the owner writes it (`82`, `#82`, its URL) | `gh82` |
| `key-from-branch BRANCH` | Parent issue of a lane branch or a worker branch named after it | `82` |
| `issue-view KEY` | Reads one issue | JSON: `key`, `title`, `body`, `state`, `url`, `parent` (key or null), `blocked_by` (keys) |
| `issue-create --title T --body-file F\|- [--parent KEY] [--blocked-by KEY]...` | Files an issue, optionally a sub-issue of a parent and blocked by others | The new key |
| `issue-comment KEY [--body-file F\|-]` | Adds a comment (standard input by default) | The comment's url |
| `issue-done KEY` | Closes the issue; one already closed stays closed | Nothing |
| `pr-line KEY` | The line a lane PR body starts with for its parent issue | `Closes #82` |

Tracker writes are only these: a ticket filed, commented on, and moved to
done. No other state change and no label. Writes need consent (the
`github-pr` skill's Consent section).
