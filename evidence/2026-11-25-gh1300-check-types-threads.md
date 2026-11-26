# gh1300: check-types' basedpyright thread count, measured

Rule (owner ruling 2026-11-25 on #1235): the gate target is in CPU seconds; the count is the lowest-CPU one whose wall
beside a full gate is no worse than 8 threads'. Result: no lower count qualifies (4 threads' wall beside a gate is
25% worse, 2 and 1 far worse), so the count stays a worker per 25 files up to every logical CPU: 8 on the kit's 227
files on this 8-CPU box. tests/lint.sh's 3-file sets stay on one thread (3 // 25 = 0, floored at 1).

## Method

- Box: 8 logical CPUs. Kit file set: 227 files (`octo-feather-lint files`), worktree gh1235-1300 at 74a6b546.
- Command, per run: `GH1300_THREADS=<n> /usr/bin/time -f '%U %S %e' uv run --locked --offline --no-sync octo-feather-lint types`,
  with `scripts/octo-feather-lint` locally edited for the measurement only (one line after the threads assignment:
  `threads = int(os.environ.get("GH1300_THREADS", threads))`), reverted before the commit. CPU = user + sys.
  Every run printed `types: ok (basedpyright analyzed 227 files)`.
- load1 read from /proc/loadavg before and after each run; `octo-feather-slot status` heavy "run holding it now"
  read before and after each run.
- Alone: no run holding the heavy slot (status `none` before and after); 6 runs per count in rounds ordered 1,2,4,8,
  12:28-12:33Z (load1 7-15) and 12:43-12:48Z (load1 from 0.95, the lowest seen; later runs raise it themselves).
- Beside a full gate: lane gh1235's `just check` (512 items) on head ca0b3bb7, two gates: pid 1962179 (from
  13:23:22Z), rounds ordered 1,2,4,8; pid 2103810 (from 13:33:38Z), rounds ordered 8,4,2,1 to cancel order bias.
  3 runs per count per gate, each counted only when the same gate held the slot at its start and end (all did).

## Summary (6 runs per cell; CPU and wall in seconds)

| threads | alone CPU mean (min-max) | alone wall mean (min-max) | beside CPU mean (min-max) | beside wall mean (min-max) |
| --- | --- | --- | --- | --- |
| 1 | 39 (35-47) | 25.5 (22.1-30.6) | 70 (65-73) | 65.9 (62.1-69.0) |
| 2 | 60 (51-67) | 20.9 (17.8-23.9) | 86 (71-102) | 46.3 (36.9-54.2) |
| 4 | 107 (95-113) | 21.4 (19.1-22.4) | 110 (95-128) | 37.7 (31.2-43.7) |
| 8 | 134 (126-139) | 21.9 (19.3-23.5) | 117 (104-126) | 30.1 (25.5-36.2) |

Beside a gate, 8 threads had the best wall in every round of both orders (per round 4 vs 8: 38.9/31.5, 31.3/28.8,
35.4/25.5, 39.1/29.3, 37.8/29.0, 43.7/36.2). Alone the walls tie from 2 threads up, but the rule judges beside a gate.
Load beside a gate: load1 14-24 for counts 2-8 (1 thread's first run started at 6.3 as the gate ramped).
8-thread CPU figure for the demo: 117 s beside a gate, 134 s alone (max 139).

## Raw runs

`<label> <UTC> threads=<n> user_sys_wall=<user> <sys> <wall> load1=<before>-><after> ok=<types ok> heavy_run_start/end`

```
alone 12:28:15 threads=1 user_sys_wall=33.63 1.50 22.05 load1=10.07->8.75 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:28:36 threads=2 user_sys_wall=54.99 3.49 20.26 load1=8.75->7.57 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:28:59 threads=4 user_sys_wall=100.04 9.05 22.24 load1=7.57->9.52 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:29:22 threads=8 user_sys_wall=124.45 12.76 23.50 load1=9.52->11.45 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:29:48 threads=1 user_sys_wall=37.74 1.67 25.64 load1=11.45->8.53 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:30:13 threads=2 user_sys_wall=63.40 4.01 23.89 load1=8.53->8.27 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:30:35 threads=4 user_sys_wall=103.73 8.56 22.43 load1=8.27->8.90 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:30:59 threads=8 user_sys_wall=123.13 13.06 23.19 load1=8.90->12.26 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:31:30 threads=1 user_sys_wall=44.81 1.99 30.62 load1=12.26->8.63 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:31:52 threads=2 user_sys_wall=59.06 3.73 21.86 load1=8.63->7.22 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:32:14 threads=4 user_sys_wall=96.02 8.50 21.74 load1=7.22->9.18 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone 12:32:38 threads=8 user_sys_wall=124.75 12.77 23.24 load1=9.18->15.04 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:43:45 threads=1 user_sys_wall=33.24 1.53 22.07 load1=0.95->1.09 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:44:03 threads=2 user_sys_wall=48.32 2.89 17.78 load1=1.09->1.43 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:44:25 threads=4 user_sys_wall=103.79 8.84 21.52 load1=1.43->4.28 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:44:47 threads=8 user_sys_wall=125.80 13.56 21.69 load1=4.28->9.34 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:45:12 threads=1 user_sys_wall=37.29 1.85 25.35 load1=9.34->7.06 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:45:35 threads=2 user_sys_wall=61.52 4.06 22.49 load1=7.06->6.80 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:45:57 threads=4 user_sys_wall=102.29 8.98 21.56 load1=6.80->7.92 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:46:17 threads=8 user_sys_wall=114.56 11.83 19.28 load1=7.92->9.39 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:46:44 threads=1 user_sys_wall=39.77 1.83 27.20 load1=9.39->7.29 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:47:04 threads=2 user_sys_wall=50.50 3.15 19.17 load1=7.29->6.86 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:47:23 threads=4 user_sys_wall=87.51 7.46 19.07 load1=6.86->8.80 ok=1 heavy_run_start=[none] heavy_run_end=[none]
alone-quiet 12:47:44 threads=8 user_sys_wall=114.76 11.02 20.33 load1=8.80->12.97 ok=1 heavy_run_start=[none] heavy_run_end=[none]
beside 13:24:37 threads=1 user_sys_wall=60.50 4.26 66.96 load1=6.32->14.16 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:25:24 threads=2 user_sys_wall=81.28 7.10 47.15 load1=14.16->14.99 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:26:04 threads=4 user_sys_wall=105.54 9.46 38.89 load1=14.99->16.85 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:26:36 threads=8 user_sys_wall=113.23 9.99 31.54 load1=16.85->20.07 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:27:42 threads=1 user_sys_wall=64.44 4.39 66.08 load1=20.07->16.78 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:28:32 threads=2 user_sys_wall=77.03 5.39 49.48 load1=16.78->19.30 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:29:04 threads=4 user_sys_wall=87.60 7.27 31.25 load1=19.30->19.07 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:29:33 threads=8 user_sys_wall=103.87 8.24 28.78 load1=19.07->20.30 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:30:36 threads=1 user_sys_wall=67.44 4.22 62.77 load1=20.30->17.44 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:31:13 threads=2 user_sys_wall=66.54 4.70 36.86 load1=17.44->16.74 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:31:49 threads=4 user_sys_wall=97.95 8.29 35.41 load1=16.74->17.71 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside 13:32:15 threads=8 user_sys_wall=97.34 7.09 25.52 load1=17.71->19.24 ok=1 heavy_run_start=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] heavy_run_end=[pid 1962179 of lane gh1235 since 2026-11-25T13:23:22Z, 512 items] counted=yes
beside-rev 13:34:20 threads=8 user_sys_wall=110.58 10.31 29.32 load1=16.38->18.99 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:35:00 threads=4 user_sys_wall=104.80 9.36 39.13 load1=18.99->20.74 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:35:44 threads=2 user_sys_wall=78.14 6.63 43.46 load1=20.74->19.52 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:36:53 threads=1 user_sys_wall=67.05 4.82 68.72 load1=19.52->17.49 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:37:22 threads=8 user_sys_wall=108.03 8.48 29.00 load1=17.49->20.42 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:38:01 threads=4 user_sys_wall=93.12 7.78 37.76 load1=20.42->20.81 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:38:48 threads=2 user_sys_wall=78.82 6.42 46.49 load1=20.81->19.84 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:39:58 threads=1 user_sys_wall=68.43 4.57 69.04 load1=19.84->18.91 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:40:35 threads=8 user_sys_wall=117.13 8.82 36.21 load1=18.91->23.63 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:41:19 threads=4 user_sys_wall=116.81 11.07 43.70 load1=23.63->22.06 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:42:14 threads=2 user_sys_wall=94.28 7.58 54.23 load1=21.58->20.20 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
beside-rev 13:43:16 threads=1 user_sys_wall=66.77 3.92 62.10 load1=20.20->15.47 ok=1 heavy_run_start=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] heavy_run_end=[pid 2103810 of lane gh1235 since 2026-11-25T13:33:38Z, 512 items] counted=yes
```
