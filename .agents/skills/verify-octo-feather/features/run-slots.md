# run-slots

Criteria:

- [quality#acceptance-verify-map-current](../../../../docs/specs/quality.spec.html#acceptance-verify-map-current) (no spec criterion owns the slots yet: the rule is owner ruling #660 2026-11-06, issue #668; the queue, owner ruling 2026-11-14 #906, issues #976 and #977)

Drive criterion: `quality#acceptance-verify-map-current`

## Sub-features

- `grant-not-director` an implementer's `octo-feather-slot grant` refused (exit 77).
- `refused` a lane implementer's `just test` over 31 items without its lane's grant: refused before any item runs (exit 75), naming the count, heavy_items, the holder and the grant to ask for.
- `grant` the director's `octo-feather-slot grant gh7 --kind heavy`.
- `status` `octo-feather-slot status` naming gh7 the heavy holder, and the eval kind.
- `queue-not-director` an implementer's `octo-feather-slot queue` refused (exit 77).
- `queue` the director's `octo-feather-slot queue gh8 --kind heavy` onto gh7's full slot: gh8 queued, position 1.
- `queue-status` `octo-feather-slot status` listing gh8 in the heavy queue, gh7 still the holder.
- `not-before-run` `octo-feather-slot settle --kind heavy` before any run under gh7's grant: nothing passes.
- `granted` the same `just test`, now holding the slot, passing.
- `released` `octo-feather-slot status` after it: no run holds either kind.
- `handed` a grace after that run ended (no run since): status names gh8 the heavy holder, the queue empty, and gh8's supervisor and the director were told.
- `refused-queue` gh7's `just test` again: refused, told to ask for `queue` (the kind is full).
- `queue-free` the director's `octo-feather-slot queue gh7 --kind eval` onto the free eval kind: granted at once, gh7's supervisor told.
- `queue-behind` gh7 queued for heavy behind gh8.
- `revoke` the director's `octo-feather-slot revoke gh8 --kind heavy`: gh8's grant gone, gh7 to get the slot after the grace.
- `revoke-status` status at once: no heavy holder, gh7 queued, the free slot waiting out the grace.
- `freed-handed` after the grace: gh7 the heavy holder, gh7's supervisor and the director told.
- `requeue` gh8 queued behind gh7.
- `revoke-again` the director revokes gh7.
- `grant-by-hand` inside the grace, the director grants gh6 by hand.
- `grant-wins` past the grace: gh6 holds, gh8 still queued, nobody told.
- `passed-over` gh6 starts no run within the bound: gh8 the holder; gh8's supervisor, gh6's supervisor and the director told.

## How to get to it (user POV)

- A worker or supervisor in a lane runs a gate over more than heavy_items items (`just fast`, `just check`, `just integrate --full`, `just fast-map`) or `just qa`; without its lane's grant the run stops with the refusal, which names the command to ask the director for.
- The director runs `octo-feather-slot grant <lane> --kind heavy|eval`, `octo-feather-slot queue <lane> --kind heavy|eval` and `octo-feather-slot status`; a queued lane's supervisor is told through `herdr-say` when the slot passes to it. The rule, the queue, the files and the lane lookup: `octo-feather-slot --help`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- The kit's gate runs offline (`just test` needs its uv venv and pnpm store, as `just check` does).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive run-slots`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/run-slots/`.

The drive makes scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/run-slots/state`, HERDR_SESSION default) holding three lane records, gh7 (supervisor `w9:p1`), gh8 (supervisor `w8:p1`) and gh6 (supervisor `w6:p1`), a director.toml (pane `w1:p1`), and a scratch suite of 31 trivial pytest items. `herdr-say` is this checkout's own (linked first on PATH in `scratch/run-slots/bin`); Herdr is a stand-in `herdr` there that appends each call's arguments as one line to `scratch/run-slots/said` (the justfile puts the kit's own herdr-say first on its recipes' PATH, so the stand-in sits at `herdr`, which that herdr-say finds on the caller's PATH); the queue's grace is 2 s through `OCTO_FEATHER_SLOT_GRACE`, its bound 30 s through `OCTO_FEATHER_SLOT_BOUND` until `requeue`, 6 s from it on. The implementer's env: OCTO_FEATHER_ROLE=implementer, HERDR_PANE_ID=w9:p3, OCTO_FEATHER_PARENT=w9:p1, HERDR_WORKSPACE_ID=w9; the director's: OCTO_FEATHER_ROLE=director, HERDR_PANE_ID=w1:p1. No live Herdr, lane or box slot file is touched.

- **Not the director** (`grant-not-director`). As the implementer, run `octo-feather-slot grant gh7 --kind heavy`. Observe exit 77 and `grant is the director's` on stderr.
- **Refused** (`refused`). As the implementer, run `just --justfile <kit>/justfile test <scratch suite>`. Observe exit 75, no item passed, and on stderr `octo-feather-slot: refused, nothing ran: this heavy run selects 31 items, over heavy_items 30 (gate-budget.toml), and lane gh7 holds no heavy grant; current holder: none; ask the director: octo-feather-slot grant gh7 --kind heavy`.
- **Grant** (`grant`). As the director, run `octo-feather-slot grant gh7 --kind heavy`. Observe exit 0 and `granted: heavy slot to lane gh7 (granted <time> by w1:p1, expires <time>)`.
- **Status** (`status`). Run `octo-feather-slot status`. Observe `  holder: gh7 (granted ...` under heavy, and the eval kind's lines.
- **Queue, not the director** (`queue-not-director`). As the implementer, run `octo-feather-slot queue gh8 --kind heavy`. Observe exit 77 and `queue is the director's` on stderr.
- **Queue** (`queue`). As the director, run `octo-feather-slot queue gh8 --kind heavy`. Observe exit 0 and `queued: lane gh8 for the heavy slot, position 1`.
- **Queue status** (`queue-status`). Run `octo-feather-slot status`. Observe `  holder: gh7 (granted ...` and `  queue: 1. gh8 (queued <time> by w1:p1)` under heavy.
- **Not before a run** (`not-before-run`). As the director, run `octo-feather-slot settle --kind heavy`. Observe `settle heavy: nothing passes (queue: gh8)`: no run has started under gh7's grant.
- **Granted** (`granted`). As the implementer, the same `just test`. Observe exit 0, `heavy slot: held: the heavy slot for lane gh7, run pid <pid> ...` and `31 passed`.
- **Released** (`released`). `octo-feather-slot status` again: `run holding it now: none` for both kinds.
- **Handed over** (`handed`). Once the grace has passed (the drive polls status up to 30 s), `octo-feather-slot status`. Observe `  holder: gh8 (granted <time> by queue, expires <time>)` and `  queue: none` under heavy; the `said` observation holds exactly two prompts, each `agent prompt <pane> <message> --wait --until working --until idle --timeout 60000`: to `w8:p1` `octo-feather-slot: the heavy slot is granted to lane gh8 until <expires> (lane gh7's run ended, no run within the 2 s grace); run your heavy run now.`, then to `w1:p1` `octo-feather-slot: heavy slot passed from lane gh7 to lane gh8; queue left: none.`
- **Refused, queue** (`refused-queue`). As the implementer, the same `just test`. Observe exit 75, no item passed, and on stderr `lane gh7 holds no heavy grant; current holder: gh8 (granted ...` and `ask the director: octo-feather-slot queue gh7 --kind heavy`.
- **Queue onto a free kind** (`queue-free`). As the director, `octo-feather-slot queue gh7 --kind eval`. Observe exit 0, `granted: eval slot to lane gh7 (granted ...`, `told w9:p1`, and the last `said` line the prompt to `w9:p1` of `octo-feather-slot: the eval slot is granted to lane gh7 until <expires> (queued onto a free slot); run your eval run now.`
- **Queue behind** (`queue-behind`). As the director, `octo-feather-slot queue gh7 --kind heavy`. Observe exit 0 and `queued: lane gh7 for the heavy slot, position 1`.
- **Revoke** (`revoke`). As the director, `octo-feather-slot revoke gh8 --kind heavy`. Observe exit 0 and exactly `revoked: heavy slot of lane gh8` then `the heavy slot passes to lane gh7 after the 2 s grace`.
- **Revoke status** (`revoke-status`). At once, `octo-feather-slot status`. Observe under heavy `  holder: none`, `  queue: 1. gh7 (queued ...` and `  free since <time>: to the queue's head after the 2 s grace`.
- **Freed, handed** (`freed-handed`). Once gh7 holds heavy (the drive polls status up to 30 s), `octo-feather-slot status`. Observe `  holder: gh7 (granted <time> by queue, ...` under heavy; the last two `said` lines the prompts to `w9:p1` of `octo-feather-slot: the heavy slot is granted to lane gh7 until <expires> (the slot free for the 2 s grace); run your heavy run now.` and to `w1:p1` of `octo-feather-slot: heavy slot free for the 2 s grace, granted to lane gh7; queue left: none.`
- **Requeue** (`requeue`). As the director, `octo-feather-slot queue gh8 --kind heavy`. Observe `queued: lane gh8 for the heavy slot, position 1`.
- **Revoke, again** (`revoke-again`). As the director, `octo-feather-slot revoke gh7 --kind heavy`. Observe exit 0, `revoked: heavy slot of lane gh7` first.
- **Grant by hand** (`grant-by-hand`). At once, as the director, `octo-feather-slot grant gh6 --kind heavy`. Observe `granted: heavy slot to lane gh6 (granted ...`.
- **The grant wins** (`grant-wins`). Past the grace (3 s), `octo-feather-slot status`. Observe under heavy `  holder: gh6 (granted ...` and `  queue: 1. gh8 (queued ...`, and no `said` line since `grant-by-hand`.
- **Passed over** (`passed-over`). Once gh8 holds heavy (gh6 started no run; polled up to 30 s), `octo-feather-slot status`. Observe `  holder: gh8 (granted ...`; the last three `said` lines the prompts to `w8:p1` of `octo-feather-slot: the heavy slot is granted to lane gh8 until <expires> (lane gh6 started no heavy run within the 6 s bound); run your heavy run now.`, to `w6:p1` of `octo-feather-slot: lane gh6's heavy grant passed to lane gh8: no heavy run started under it within the 6 s bound; to run, ask the director: octo-feather-slot queue gh6 --kind heavy.` and to `w1:p1` of `octo-feather-slot: heavy slot passed over lane gh6 (no run within the 6 s bound) to lane gh8; queue left: none.`
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- Never drive this feature against the box's real `XDG_STATE_HOME`: every worktree's copy of octo-feather-slot shares the one slots dir, and every command of this one settles it first. What each file holds and which copies read it: `octo-feather-slot --help`, Files.
- Nothing passes at once: when a slot passes (hand-over, pass-over, free slot) and what starts each check, `octo-feather-slot --help`, the queue. The drive polls status, which settles first, rather than sleeping a fixed time.
- Outside a Herdr agent (no HERDR_PANE_ID or OCTO_FEATHER_ROLE) nothing is refused: the drive sets the implementer's env to be refused. What else is not refused: `octo-feather-slot --help`.
- `status` lists both kinds: a lane holding eval shows `holder: <lane>` there too, so read the heavy kind's lines only.
