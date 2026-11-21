# gh1213: fast-tier runs at the lowest priority, and at most fast_runs of them at once

Change: tests/gate/heavy_slot.py sets each process running a fast-tier run's items (quality #recipes-static-first) to nice 19 and ionice(1)'s idle class, every thread, before its first item; a full run keeps its priority (27c129a5). Step 2 (b62a2dbf): at most fast_runs (gate-budget.toml, 2) fast-tier runs at once on the box; one over it waits its turn, naming the runs it waits for, never refused.

Smoke: .agents/skills/verify-octo-feather/features/run-slots.md (its pointer to the rule; `just fast` run live in the implementer pane of lane gh1186, no model run)

## The smoke

`just fast` at 27c129a5's tree (worst case, 321 items): `heavy slot: not needed: fast tier, 3 workers (cap 3), at the lowest priority (nice 19, disk idle)`, 321 passed in 343.8 s. During it `ps` showed its three xdist workers at NI 19 and `ionice -p` on each thread of one `idle`; the controller at NI 0 (it runs no item). The box's block devices all use the `none` I/O scheduler (`/sys/block/*/queue/scheduler`), which ignores I/O priorities: on this box the disk half of the rule has no effect; the processor half does.

## The guard measurement

Method: /tmp/gh1186-guard's run.sh and config.sh (the failed measurement's), scratch /tmp/gh1186-guard2. Full gate `just check` (8 workers, lane gh1186's heavy grant) in a detached worktree g0 at the head; 5 s after its `heavy slot: held` line, N worst-case `just fast` runs at once in g1..gN (an uncommitted comment line appended to the justfile: `just fast-list` selects 321 of 455 at 27c129a5, 322 of 456 at b62a2dbf). Order A gate alone, B + 1 fast, C + 3, D + 5, E alone. Per run: wall and exit (run.sh), load1 at start/end, steal and idle share from /proc/stat's cpu line over the run's window (idle includes iowait), MemAvailable min and swap used max from /proc/meminfo sampled every 5 s, gate item CPU sum from its CPU-seconds block, earlyoom kills from `journalctl -u earlyoom`. 8 vCPU, 15.6 GiB, swap 4 GiB.

### Step 1: lowest priority only (27c129a5), 06:46 to 07:35Z

mean(A, E) = 406.5 s.

| run | gate wall s (vs mean A,E) | gate item CPU s | gate exit | fast walls s (exit) | load1 start/end | steal % | idle % | MemAvailable min MiB | swap max MiB | earlyoom |
|---|---|---|---|---|---|---|---|---|---|---|
| A gate alone | 418.0 | 2587.3 | 0 | | 2.25/11.12 | 28.6 | 15.2 | 10995 | 1269 | none |
| B + 1 fast | 427.5 (+5.2%) | 2357.8 | 0 | 597.6 (0) | 11.12/18.66 | 22.7 | 5.9 | 9170 | 1269 | none |
| C + 3 fast | 432.0 (+6.3%) | 2157.4 | 0 | 745.7, 744.0, 743.0 (all 0) | 5.63/27.85 | 14.9 | 2.4 | 2833 | 1283 | none |
| D + 5 fast | 443.1 (+9.0%) | 2080.8 | 1 | 260.0 (1), 742.0 (0), 737.6 (0), 256.0 (1), 261.9 (1) | 13.66/25.52 | 12.4 | 2.5 | 895 | 4096 (full) | 4 node SIGTERMs, 07:19:07 to 07:20:11 |
| E gate alone | 394.9 | 2508.5 | 0 | | 9.48/12.43 | 26.8 | 13.7 | 11002 | 1581 | none |

D's failures: fast1, fast4, fast5 red on the static check-ts (`ERR_PNPM_RECURSIVE_EXEC_FIRST_FAIL Command was killed with SIGTERM`: eslint), so no test ran; the full gate red on tests/gate/kit/test_check_ts.py::test_findings, its nested check-ts's eslint killed with SIGTERM the same way. The SIGTERM is earlyoom's (earlyoom.service, `-m 5 -s 10 --prefer (^|/)(node|tsc|eslint|knip)$`), at MemAvailable under 5% with swap full; no timeout in test_recipe, check-ts or pnpm sends it. The same held in the failed measurement (05:52:26 to 05:52:35Z). Verdict: miss (D: failures; the gate within 15% at C and D).

### Step 2: lowest priority and fast_runs = 2 (42e72c17), 08:23 to 09:18Z

A first step-2 run at b62a2dbf was stopped at D: its C full gate took 630.5 s because the gate's own tests/fast.sh item ran a nested `just fast` that waited 535 s for a turn behind the lanes' fast runs. Fixed in 42e72c17 (a run under a holder of the heavy slot or a turn takes none, by ancestry); its data: /tmp/gh1186-guard2/step2-bug. Below, the run at 42e72c17; tests/fast.sh in the full gate took 50.0 s at C and 56.8 s at D.

mean(A, E) = 320.3 s.

| run | gate wall s (vs mean A,E) | gate item CPU s | gate exit | load1 start/end | steal % | idle % | MemAvailable min MiB | swap max MiB | earlyoom |
|---|---|---|---|---|---|---|---|---|---|
| A gate alone | 320.4 | 2025.0 | 0 | 3.73/9.77 | 15.8 | 15.5 | 11337 | 1563 | none |
| B + 1 fast | 348.2 (+8.7%) | 1942.3 | 0 | 9.77/15.75 | 12.0 | 6.1 | 10037 | 1563 | none |
| C + 3 fast | 381.8 (+19.2%) | 1971.4 | 0 | 6.17/20.79 | 10.6 | 3.5 | 6804 | 1562 | none |
| D + 5 fast | 374.9 (+17.0%) | 1929.6 | 0 | 4.62/21.03 | 10.0 | 3.2 | 6354 | 1562 | none |
| E gate alone | 320.2 | 2026.4 | 0 | 4.76/12.41 | 15.2 | 15.2 | 11113 | 1561 | none |

Each fast run (worst case, 322 items, all passed): wall = waiting for a turn + running.

| run | wall s | waiting s | running s | exit |
|---|---|---|---|---|
| B fast1 | 491.3 | 0 | 491.3 | 0 |
| C fast1 | 593.3 | 0 | 593.3 | 0 |
| C fast2 | 867.3 | 577 | 290.3 | 0 |
| C fast3 | 594.1 | 0 | 594.1 | 0 |
| D fast1 | 648.5 | 0 | 648.5 | 0 |
| D fast2 | 1262.4 | 971 | 291.4 | 0 |
| D fast3 | 993.8 | 642 | 351.8 | 0 |
| D fast4 | 988.3 | 632 | 356.3 | 0 |
| D fast5 | 659.0 | 0 | 659.0 | 0 |

A waiting run said, e.g.: `fast tier: waiting my turn, 2 fast runs at once (fast_runs, gate-budget.toml), held by: pid 3617145 in /home/exedev/src/octo-feather-gh1186-g5 since 2026-11-21T08:52:21Z; pid 3617359 in ...`, then `fast tier: my turn after 642 s waiting, fast-0.lock taken`.

Against the pass line: no failure anywhere, gate or fast, no earlyoom kill, MemAvailable never under 6.3 GiB (pass). Full gate +19.2% at C and +17.0% at D over mean(A, E): over "about 15%" by 2 to 4 points (miss, narrowly; steal was 15% in A and E, 10% in C and D). Fast runs all finish, but not in a few minutes: running 4.8 to 11.0 min, wall up to 21.0 min with waiting (miss on "a few minutes").
