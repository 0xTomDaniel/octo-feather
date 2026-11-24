# A spec PR merges like a lane PR

Superseded by ADR 0033 (2026-11-20), for the spec PR's merge gate staying the owner's.

The spec PR (ADR 0021) merged by the owner's hand, while every lane PR merges on the owner's approval by a supervisor, pinned to the head the merge ask named. Two merge paths for one owner gate. A spec PR now merges the same way as a lane PR: see [gates-merge](../specs/issue-lifecycle.spec.html#gates-merge) and [lc-spec-pr](../specs/issue-lifecycle.spec.html#lc-spec-pr). The merge gate stays the owner's ([gates-list](../specs/issue-lifecycle.spec.html#gates-list)). Decided by Tom (owner), 2026-11-13, issue #785; first applied to PR #827. This supersedes ADR [0021](0021-the-accepted-spec-is-the-handoff.md) only where it has the owner merge the spec PR.

Rejected: the owner merging spec PRs by hand, a second merge path with no pinned head; and the director merging them, which breaks the director's merge-nothing rule (pilot 1, 2026-10-20).
