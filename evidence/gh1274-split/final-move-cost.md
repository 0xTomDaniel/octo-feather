# What the final move (#1336) stales (#1335 follow-up)

Made by evidence/gh1274-split/final_move_cost.py origin/main (67fc426d41cd) gh1274 (babd151063c2) 1ed7fea6 (1ed7fea6c91f); its docstring owns each part's rule.

## (1) Eval pins

4 demos run `octo-feather-qa --verdict` (8 cases). Each run read-only, in a detached worktree of the ref, its own scripts/octo-feather-qa.

| criterion | exit at origin/main | exit at gh1274 | exit at 1ed7fea6 |
|---|---|---|---|
| issue-lifecycle#acceptance-tier-three-waits | 77 | 77 | 77 |
| comms#acceptance-real-blocker | 77 | 77 | 77 |
| issue-lifecycle#acceptance-ticket-skills | 77 | 77 | 77 |
| roles#acceptance-general-worker-no-implementation | 77 | 77 | 77 |

### issue-lifecycle#acceptance-tier-three-waits

At origin/main (exit 77):
    INSUFFICIENT director-tier-relay/tier-three-waits-for-owner: stored PASS, run 20261126T064835Z-939595, kit c5886d638631, runs 3/3 passed; stale at HEAD 67fc426d41cd: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261126T064835Z-939595/director-tier-relay/tier-three-waits-for-owner: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; scripts/pi-role changed
At gh1274 (exit 77):
    INSUFFICIENT director-tier-relay/tier-three-waits-for-owner: stored PASS, run 20261126T064835Z-939595, kit c5886d638631, runs 3/3 passed; stale at HEAD babd151063c2: .agents/skills/herdr-comms/SKILL.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261126T064835Z-939595/director-tier-relay/tier-three-waits-for-owner: .agents/skills/herdr-comms/SKILL.md changed; scripts/pi-role changed
  stale files it names that the lane changed: none
At 1ed7fea6 (exit 77):
    INSUFFICIENT director-tier-relay/tier-three-waits-for-owner: stored PASS, run 20261126T064835Z-939595, kit c5886d638631, runs 3/3 passed; stale at HEAD 1ed7fea6c91f: .agents/skills/herdr-comms/SKILL.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261126T064835Z-939595/director-tier-relay/tier-three-waits-for-owner: .agents/skills/herdr-comms/SKILL.md changed; scripts/pi-role changed
  stale files it names that the lane changed: none

### comms#acceptance-real-blocker

At origin/main (exit 77):
    INSUFFICIENT supervisor-autonomy/owner-access-blocker-and-ready-work: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 67fc426d41cd: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-autonomy/owner-access-blocker-message: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, review; stale at HEAD 67fc426d41cd: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-autonomy/owner-access-blocker-and-ready-work: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-autonomy/owner-access-blocker-message: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
At gh1274 (exit 77):
    INSUFFICIENT supervisor-autonomy/owner-access-blocker-and-ready-work: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD babd151063c2: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-autonomy/owner-access-blocker-message: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, review; stale at HEAD babd151063c2: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-autonomy/owner-access-blocker-and-ready-work: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-autonomy/owner-access-blocker-message: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
  stale files it names that the lane changed: none
At 1ed7fea6 (exit 77):
    INSUFFICIENT supervisor-autonomy/owner-access-blocker-and-ready-work: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 1ed7fea6c91f: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-autonomy/owner-access-blocker-message: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, review; stale at HEAD 1ed7fea6c91f: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-autonomy/owner-access-blocker-and-ready-work: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-autonomy/owner-access-blocker-message: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
  stale files it names that the lane changed: none

### issue-lifecycle#acceptance-ticket-skills

At origin/main (exit 77):
    INSUFFICIENT supervisor-ticket-skills/missed-skill-sent-back: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 67fc426d41cd: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-ticket-skills/loaded-skill-integrated: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 67fc426d41cd: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-ticket-skills/missed-skill-sent-back: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-ticket-skills/loaded-skill-integrated: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
At gh1274 (exit 77):
    INSUFFICIENT supervisor-ticket-skills/missed-skill-sent-back: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD babd151063c2: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-ticket-skills/loaded-skill-integrated: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD babd151063c2: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-ticket-skills/missed-skill-sent-back: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-ticket-skills/loaded-skill-integrated: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
  stale files it names that the lane changed: none
At 1ed7fea6 (exit 77):
    INSUFFICIENT supervisor-ticket-skills/missed-skill-sent-back: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 1ed7fea6c91f: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-ticket-skills/loaded-skill-integrated: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 1ed7fea6c91f: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-ticket-skills/missed-skill-sent-back: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-ticket-skills/loaded-skill-integrated: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
  stale files it names that the lane changed: none

### roles#acceptance-general-worker-no-implementation

At origin/main (exit 77):
    INSUFFICIENT supervisor-general-worker/diagnosis-diff-goes-to-implementer: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 67fc426d41cd: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-general-worker/implementer-result-integrated-not-candidate: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 67fc426d41cd: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-general-worker/reviewed-implementer-result-integrated: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 67fc426d41cd: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-general-worker/diagnosis-diff-goes-to-implementer: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-general-worker/implementer-result-integrated-not-candidate: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-general-worker/reviewed-implementer-result-integrated: .agents/skills/github-issues/scripts/issue-view changed; .agents/skills/github-pr/SKILL.md changed; .agents/skills/github-pr/scripts/gh changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
At gh1274 (exit 77):
    INSUFFICIENT supervisor-general-worker/diagnosis-diff-goes-to-implementer: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD babd151063c2: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-general-worker/implementer-result-integrated-not-candidate: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD babd151063c2: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-general-worker/reviewed-implementer-result-integrated: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD babd151063c2: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-general-worker/diagnosis-diff-goes-to-implementer: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-general-worker/implementer-result-integrated-not-candidate: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-general-worker/reviewed-implementer-result-integrated: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
  stale files it names that the lane changed: none
At 1ed7fea6 (exit 77):
    INSUFFICIENT supervisor-general-worker/diagnosis-diff-goes-to-implementer: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 1ed7fea6c91f: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-general-worker/implementer-result-integrated-not-candidate: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 1ed7fea6c91f: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    INSUFFICIENT supervisor-general-worker/reviewed-implementer-result-integrated: stored PASS, run 20261122T162704Z-4a14c2, kit 0363d3e9457d, runs 3/3 passed; stale at HEAD 1ed7fea6c91f: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
    octo-feather-qa: insufficient evidence: 20261122T162704Z-4a14c2/supervisor-general-worker/diagnosis-diff-goes-to-implementer: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-general-worker/implementer-result-integrated-not-candidate: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed | 20261122T162704Z-4a14c2/supervisor-general-worker/reviewed-implementer-result-integrated: .agents/skills/github-pr/SKILL.md changed; .agents/skills/herdr-comms/SKILL.md changed; .agents/skills/herdr-comms/assets/herdr-say changed; .agents/skills/herdr-comms/assets/herdr_scope.py changed; agents/supervisor.md changed; scripts/pi-role changed
  stale files it names that the lane changed: none

## (2) Built criteria the move itself stales

Built at origin/main with covers in its qc.toml: 91 (of 230 built).

### origin/main...gh1274: 89 files changed; 41 of 91 built criteria stale

| spec | stale | built with covers |
|---|---|---|
| comms | 7 | 21 |
| issue-lifecycle | 24 | 30 |
| quality | 9 | 26 |
| roles | 1 | 5 |
| skills | 0 | 3 |
| templates | 0 | 6 |

| changed file | stale criteria it reaches | of them through it alone |
|---|---|---|
| scripts/octo-feather-lane | 33 | 18 |
| justfile | 9 | 8 |
| scripts/merge_ask.py | 9 | 0 |
| scripts/start_lane.py | 6 | 0 |
| scripts/post_merge.py | 3 | 0 |

- comms#acceptance-correction-intake: scripts/octo-feather-lane
- comms#acceptance-reflect-files-correction: scripts/octo-feather-lane
- comms#acceptance-reflect-files-route-owner: scripts/octo-feather-lane
- comms#acceptance-reflect-recurrence-comments: scripts/octo-feather-lane
- comms#acceptance-report-gate-budget: scripts/octo-feather-lane
- comms#acceptance-report-owner-caught-headline: scripts/octo-feather-lane
- comms#acceptance-report-skill-reach: scripts/octo-feather-lane
- issue-lifecycle#acceptance-ci-alongside: scripts/octo-feather-lane
- issue-lifecycle#acceptance-ci-status-only: scripts/octo-feather-lane
- issue-lifecycle#acceptance-correction-replay-missing: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-correction-replay-shown: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-declaration-check-shown: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-integrate-checkpoint: justfile
- issue-lifecycle#acceptance-integrate-fast: justfile
- issue-lifecycle#acceptance-lane-start: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-current-kit: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-exists: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-files: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-rerun: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-sub-issue: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-merge-ask-full-proof: scripts/octo-feather-lane
- issue-lifecycle#acceptance-merge-ask-gate-budget: scripts/octo-feather-lane
- issue-lifecycle#acceptance-merge-ask-siblings: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-one-head-hunks: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-pilot-full: justfile
- issue-lifecycle#acceptance-pilot-pr: scripts/octo-feather-lane
- issue-lifecycle#acceptance-reflection-missed-lane: scripts/octo-feather-lane
- issue-lifecycle#acceptance-review-resolution: scripts/octo-feather-lane
- issue-lifecycle#acceptance-ticket-skills: scripts/octo-feather-lane
- issue-lifecycle#acceptance-verdict-covers-lane: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-writer-route-lane: scripts/octo-feather-lane
- quality#acceptance-fast-affected: justfile
- quality#acceptance-fast-diff-base: justfile
- quality#acceptance-fast-map-behind: justfile
- quality#acceptance-fast-map-slot-free: justfile
- quality#acceptance-map-after-merge: justfile, scripts/merge_ask.py, scripts/octo-feather-lane, scripts/post_merge.py
- quality#acceptance-map-build-failed: scripts/merge_ask.py, scripts/octo-feather-lane, scripts/post_merge.py
- quality#acceptance-map-full-daily: scripts/merge_ask.py, scripts/octo-feather-lane, scripts/post_merge.py
- quality#acceptance-qc-fallback: scripts/octo-feather-lane
- quality#acceptance-qc-insufficient: scripts/octo-feather-lane
- roles#acceptance-shaper-launch: justfile

### origin/main...1ed7fea6: 117 files changed; 41 of 91 built criteria stale

| spec | stale | built with covers |
|---|---|---|
| comms | 7 | 21 |
| issue-lifecycle | 24 | 30 |
| quality | 9 | 26 |
| roles | 1 | 5 |
| skills | 0 | 3 |
| templates | 0 | 6 |

| changed file | stale criteria it reaches | of them through it alone |
|---|---|---|
| scripts/octo-feather-lane | 33 | 18 |
| justfile | 9 | 8 |
| scripts/merge_ask.py | 9 | 0 |
| scripts/start_lane.py | 6 | 0 |
| scripts/post_merge.py | 3 | 0 |

- comms#acceptance-correction-intake: scripts/octo-feather-lane
- comms#acceptance-reflect-files-correction: scripts/octo-feather-lane
- comms#acceptance-reflect-files-route-owner: scripts/octo-feather-lane
- comms#acceptance-reflect-recurrence-comments: scripts/octo-feather-lane
- comms#acceptance-report-gate-budget: scripts/octo-feather-lane
- comms#acceptance-report-owner-caught-headline: scripts/octo-feather-lane
- comms#acceptance-report-skill-reach: scripts/octo-feather-lane
- issue-lifecycle#acceptance-ci-alongside: scripts/octo-feather-lane
- issue-lifecycle#acceptance-ci-status-only: scripts/octo-feather-lane
- issue-lifecycle#acceptance-correction-replay-missing: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-correction-replay-shown: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-declaration-check-shown: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-integrate-checkpoint: justfile
- issue-lifecycle#acceptance-integrate-fast: justfile
- issue-lifecycle#acceptance-lane-start: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-current-kit: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-exists: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-files: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-rerun: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-lane-start-sub-issue: scripts/octo-feather-lane, scripts/start_lane.py
- issue-lifecycle#acceptance-merge-ask-full-proof: scripts/octo-feather-lane
- issue-lifecycle#acceptance-merge-ask-gate-budget: scripts/octo-feather-lane
- issue-lifecycle#acceptance-merge-ask-siblings: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-one-head-hunks: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-pilot-full: justfile
- issue-lifecycle#acceptance-pilot-pr: scripts/octo-feather-lane
- issue-lifecycle#acceptance-reflection-missed-lane: scripts/octo-feather-lane
- issue-lifecycle#acceptance-review-resolution: scripts/octo-feather-lane
- issue-lifecycle#acceptance-ticket-skills: scripts/octo-feather-lane
- issue-lifecycle#acceptance-verdict-covers-lane: scripts/merge_ask.py, scripts/octo-feather-lane
- issue-lifecycle#acceptance-writer-route-lane: scripts/octo-feather-lane
- quality#acceptance-fast-affected: justfile
- quality#acceptance-fast-diff-base: justfile
- quality#acceptance-fast-map-behind: justfile
- quality#acceptance-fast-map-slot-free: justfile
- quality#acceptance-map-after-merge: justfile, scripts/merge_ask.py, scripts/octo-feather-lane, scripts/post_merge.py
- quality#acceptance-map-build-failed: scripts/merge_ask.py, scripts/octo-feather-lane, scripts/post_merge.py
- quality#acceptance-map-full-daily: scripts/merge_ask.py, scripts/octo-feather-lane, scripts/post_merge.py
- quality#acceptance-qc-fallback: scripts/octo-feather-lane
- quality#acceptance-qc-insufficient: scripts/octo-feather-lane
- roles#acceptance-shaper-launch: justfile

## (3) Parity cases

### origin/main...gh1274

Retargeted (6): lane-archive, lane-ci-start, lane-done, lane-intake, lane-report, lane-spend

Retired (7): lane-judge, lane-judge-real-call-evidence, lane-judge-real-ticket-slice, lane-judge-rerun, lane-judge-threshold-below, lane-judge-threshold-meets, lane-tickets

### origin/main...1ed7fea6

Retargeted (12): lane-archive, lane-ci-start, lane-done, lane-intake, lane-merge-ask, lane-merge-ask-checks, lane-merge-ask-gate-time, lane-merge-ask-judged-proof, lane-merge-ask-main-merges, lane-merge-ask-no-criterion-proof, lane-report, lane-spend

Retired (7): lane-judge, lane-judge-real-call-evidence, lane-judge-real-ticket-slice, lane-judge-rerun, lane-judge-threshold-below, lane-judge-threshold-meets, lane-tickets

