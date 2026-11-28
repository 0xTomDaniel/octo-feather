# Launch cost of scripts/octo-feather-lane, before and after the split (#1334, director's addition)

Commands (from the kit root; launch.py's docstring says how each number is taken):

    python3 evidence/gh1274-split/covers/launch.py launches <main tree> . --n 20
    python3 evidence/gh1274-split/covers/launch.py tests <main tree> . --runs 3 \
      tests/gate/kit/test_lane_review_resolution.py tests/gate/kit/test_lane_reflect.py \
      tests/gate/kit/test_lane_merge_order.py "tests/gate/test_gate.py::test_script[tests/check-templates.sh]" \
      tests/gate/kit/test_lane_tickets.py

Main tree: a scratch clone at f7f16367 (/tmp/gh1274/main-tree, uv synced). Split tree: this branch at 7a8e7897, whose
scripts/ are gh1274's tip e4fe7b28 (evidence commits only on top). Harness smoke first: merge-ask abc, 3 launches
per tree. The table is the full run that followed.

Summary:
- A real command path costs about half the CPU after the split: median 113 to 137 ms against 221 to 259 ms
  before (floor `python3 -c pass`: 23 ms). Wall drops from 328 to 380 ms to 164 to 220 ms.
- `--help` and the no-argument help cost more after the split: 301 and 290 ms CPU against 228 and 243 ms. The help
  is joined from every module, so every module loads.
- The four lane tests that launch it most launch it 12 to 198 times each, about as often on both trees. The counts
  move by one or two between runs on either tree.
  - Their CPU drops by 10 to 20% per file: test_lane_tickets 43.5 to 36.6 s, test_lane_reflect 22.2 to 18.4 s,
    test_lane_review_resolution 10.6 to 8.7 s, test_lane_merge_order 7.4 to 6.5 s (means of 3).
  - The whole five-item `just test` run goes from 106 to 110 s CPU down to 93 to 96 s.
- check-templates does not launch the lane script (0 launches under strace on both trees); its CPU is the same.
- Box load was high throughout (1-minute load average 29 to 38 on 8 cores). Runs are interleaved, so it falls on
  both trees alike, but p90s are noisy.

## Per launch (20 each, interleaved)

Trees: main f7f163676186 (/tmp/gh1274/main-tree), split 7a8e7897929b (/home/exedev/src/octo-feather-gh1274-1334). 20 launches per command and tree, interleaved (tree order alternating by round). Interpreter: Python 3.12.3 (/usr/bin/env).
Box load average (1 min) over the run: start 31.4, median 30.3, max 31.8, end 29.2.

| command | tree | exit | CPU median ms | CPU p90 ms | wall median ms | wall p90 ms |
|---|---|---|---|---|---|---|
| --help | main | 64 | 228 | 309 | 350 | 583 |
| --help | split | 64 | 301 | 422 | 459 | 613 |
| no argument | main | 64 | 243 | 372 | 353 | 712 |
| no argument | split | 64 | 290 | 366 | 423 | 694 |
| tickets 1 (no spec dir: refused after parsing) | main | 2 | 259 | 332 | 367 | 693 |
| tickets 1 (no spec dir: refused after parsing) | split | 2 | 127 | 226 | 186 | 407 |
| seam 1 (usage refusal) | main | 2 | 221 | 492 | 340 | 805 |
| seam 1 (usage refusal) | split | 2 | 123 | 231 | 184 | 334 |
| report (offline: scratch state, gh refusing) | main | 0 | 233 | 315 | 328 | 450 |
| report (offline: scratch state, gh refusing) | split | 0 | 137 | 233 | 220 | 385 |
| merge-ask abc (refusal) | main | 1 | 232 | 373 | 380 | 616 |
| merge-ask abc (refusal) | split | 1 | 113 | 227 | 164 | 346 |
| python3 -c pass (floor) | - | 0 | 23 | 44 | 36 | 86 |

## The five tests (launches counted under strace -f -v, attributed by GATE_ITEM; CPU = sum of items' cpu_s from the junit report, 3 runs per tree, interleaved)

main: launches of octo-feather-lane under strace (just test exit 0): {'tests/gate/kit/test_lane_reflect.py': 70, 'tests/gate/kit/test_lane_merge_order.py': 12, 'tests/gate/kit/test_lane_review_resolution.py': 35, 'tests/gate/kit/test_lane_tickets.py': 196}
split: launches of octo-feather-lane under strace (just test exit 0): {'tests/gate/kit/test_lane_reflect.py': 71, 'tests/gate/kit/test_lane_merge_order.py': 12, 'tests/gate/kit/test_lane_review_resolution.py': 35, 'tests/gate/kit/test_lane_tickets.py': 198}
Box load average (1 min) before the timed runs: 33.8

| test file | main CPU s (runs) | split CPU s (runs) |
|---|---|---|
| tests/check-templates.sh | 7.7 8.2 7.7 | 7.4 7.7 7.9 |
| tests/gate/kit/test_lane_merge_order.py | 6.9 7.4 7.8 | 6.4 6.5 6.6 |
| tests/gate/kit/test_lane_reflect.py | 21.7 22.8 22.1 | 18.6 17.8 18.9 |
| tests/gate/kit/test_lane_review_resolution.py | 10.4 10.3 11.0 | 8.6 8.7 8.8 |
| tests/gate/kit/test_lane_tickets.py | 41.7 43.9 44.9 | 36.8 35.2 37.9 |

Box load average (1 min) after the timed runs: 37.6

main: whole `just test` run CPU s 106.0 109.7 110.3; wall s 44 48 49 (wall includes waiting for a fast-run turn)

split: whole `just test` run CPU s 93.9 92.8 95.6; wall s 39 37 33 (wall includes waiting for a fast-run turn)
