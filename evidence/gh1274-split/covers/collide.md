# Collisions before and after the split (#1334, director's addition)

Commands: README.md. A PR of the 60 collides when another PR whose open interval overlaps its own (createdAt to
mergedAt, else closedAt, else the fetch time) changed a file it changed too. Before: files as recorded. After: the
hub's hunks placed on the split modules, as (c') and (c'') in counts.md.

Caveats:
- PR #79 is left out: it has been open since 2026-10-22, and its diff from today's merge base (51 files) is not what
  it touched while the 60 were open. With it the numbers are: all files 53 collided, 310 pairs before and 300 after;
  scripts/ only 29 collided, 115 pairs before and 89 after.
- The open PRs' files are their diff from their merge base with origin/main as of the fetch.
- Bookkeeping files (qc.toml, the status, calls and spec files, .basedpyright/baseline.json) collide in most PRs, so
  the share of PRs that collide does not move. The scripts/ rows and the per-file tables show what the split changes:
  scripts/octo-feather-lane drops from 100 collision pairs to 25 (dispatcher), and its hunks spread over the modules.

PRs measured: the 60 merged in prs.json; others: every PR whose interval overlaps theirs (71 with files, fetched 2026-11-28T09:46:20Z); left out: [79].

| files | view | PRs of the 60 that collided | median colliding PRs per PR | collision pairs (PR, other PR) |
|---|---|---|---|---|
| all | before | 52 | 4 | 275 |
| all | c' | 52 | 3 | 265 |
| all | c'' | 52 | 3 | 265 |
| scripts/ | before | 28 | 0 | 113 |
| scripts/ | c' | 28 | 0 | 87 |
| scripts/ | c'' | 28 | 0 | 87 |

Top colliding files, before: | file | collision pairs through it | PRs of the 60 colliding through it |
|---|---|---|
| scripts/octo-feather-lane | 100 | 21 |
| qc.toml | 80 | 18 |
| docs/specs/issue-lifecycle.status.json | 61 | 18 |
| .basedpyright/baseline.json | 45 | 11 |
| docs/specs/issue-lifecycle.spec.html | 40 | 13 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 32 | 14 |
| justfile | 31 | 11 |
| docs/specs/issue-lifecycle.calls.jsonl | 26 | 9 |
| tests/gate/kit/testkit/herdr.py | 22 | 8 |
| pyproject.toml | 19 | 9 |
| tests/gate/kit/herdr_messaging.py | 19 | 10 |
| docs/specs/comms.calls.jsonl | 18 | 9 |
| docs/specs/comms.spec.html | 18 | 9 |
| docs/specs/comms.status.json | 17 | 9 |
| .agents/skills/verify-octo-feather/features/README.md | 15 | 7 |
| agents/director.md | 14 | 6 |
| tests/gate/kit/lane_archive_teardown.py | 14 | 5 |
| tests/gate/kit/lane_merge.py | 14 | 5 |
| tests/gate/kit/testkit/__init__.py | 13 | 7 |
| .agents/skills/herdr-comms/SKILL.md | 12 | 8 |

Top colliding files, c': | file | collision pairs through it | PRs of the 60 colliding through it |
|---|---|---|
| qc.toml | 80 | 18 |
| docs/specs/issue-lifecycle.status.json | 61 | 18 |
| .basedpyright/baseline.json | 45 | 11 |
| docs/specs/issue-lifecycle.spec.html | 40 | 13 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 32 | 14 |
| justfile | 31 | 11 |
| scripts/lane_ticketing.py | 29 | 13 |
| docs/specs/issue-lifecycle.calls.jsonl | 26 | 9 |
| scripts/post_merge.py | 26 | 9 |
| scripts/octo-feather-lane | 25 | 10 |
| scripts/lane_reporting.py | 22 | 9 |
| tests/gate/kit/testkit/herdr.py | 22 | 8 |
| scripts/merge_ask.py | 20 | 9 |
| pyproject.toml | 19 | 9 |
| scripts/lane_review.py | 19 | 8 |
| tests/gate/kit/herdr_messaging.py | 19 | 10 |
| docs/specs/comms.calls.jsonl | 18 | 9 |
| docs/specs/comms.spec.html | 18 | 9 |
| docs/specs/comms.status.json | 17 | 9 |
| scripts/lane_reflection.py | 16 | 7 |

Top colliding files, c'': | file | collision pairs through it | PRs of the 60 colliding through it |
|---|---|---|
| qc.toml | 80 | 18 |
| docs/specs/issue-lifecycle.status.json | 61 | 18 |
| .basedpyright/baseline.json | 45 | 11 |
| docs/specs/issue-lifecycle.spec.html | 40 | 13 |
| .agents/skills/verify-octo-feather/scripts/verify-octo-feather | 32 | 14 |
| justfile | 31 | 11 |
| scripts/lane_ticketing.py | 29 | 13 |
| docs/specs/issue-lifecycle.calls.jsonl | 26 | 9 |
| scripts/post_merge.py | 26 | 9 |
| scripts/octo-feather-lane | 25 | 10 |
| scripts/lane_reflection.py | 22 | 8 |
| scripts/lane_reporting.py | 22 | 9 |
| tests/gate/kit/testkit/herdr.py | 22 | 8 |
| scripts/merge_ask.py | 20 | 9 |
| pyproject.toml | 19 | 9 |
| scripts/lane_review.py | 19 | 8 |
| tests/gate/kit/herdr_messaging.py | 19 | 10 |
| docs/specs/comms.calls.jsonl | 18 | 9 |
| docs/specs/comms.spec.html | 18 | 9 |
| docs/specs/comms.status.json | 17 | 9 |

## Before and after #1335

All files: c'' 265 pairs before #1335, 265 after; scripts/: 87 before, 85 after; through scripts/merge_ask.py 20
before, 16 after. The table, its command and its full output: counts.md (Before and after #1335),
collide-after-1335.md.
