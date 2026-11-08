# Lane 681 migration map

Old tests at ef42b60; all replacement scenarios run commands through kit public CLIs. Parity cases select the whole replacement file, so scenario consolidation needs no selector changes.

| Old script | Replacement scenario(s) | Preserved cases |
| --- | --- | --- |
| herdr-spawn.sh | herdr_messaging: spawn_plain | Plain spawn, approve flags (interactive and headless), Linear env and issue creation, no key leak, PATH fallback and precedence, cwd tracker selection/refusal, mise shims and no-mise fallback |
| herdr-spawn.sh | herdr_messaging: spawn_dialog | Pi trust dialog, detecting-read failure, stuck non-Pi dialog and final-read failure; stderr, no keys, tab cleanup |
| herdr-spawn.sh | herdr_messaging: resume_live | Parked supervisor in live workspace, plain delivery after resume, fresh-start refusal; then missing workspace, new lane workspace and seed-tab cleanup |
| herdr-say.sh | herdr_messaging: say_parked | Worker sibling and other-lane refusals; lane-log worker resume, malformed-log diagnostics, unnamed supervisor parent-route resume; sessions and notices |
| herdr-close.sh | herdr_close: close_ids | Tab and pane targets, pane mapping, missing and unknown targets, only owned tagged child termination |
| handoff-park.sh | herdr_close: park | Park report channel, session identity and close behavior |
| handoff.sh | handoff: encode_roundtrip | JSON encoding/decoding, field types and special-character roundtrip |
| lane-post-merge-tell.sh | herdr_messaging: tell_supervisors | Live/parked/other-repo filtering, latest parked record, canonical prod fields, rerun suppression, no-rule merge, kit-wide notification, failed-send retry, gone/moved lanes, pending/archive teardown, non-missing Herdr failure |
| qc-uv-cache.sh | qc_uv_cache: colored | Cache-overlay offline sync/import/write, host manifest unchanged, upper cleanup, lower binding and writable-path isolation; also retains existing lane 660 colored-cache coverage |

Existing lane 660 messaging scenarios remain separate: spawn_ready_late, say_lookup_fails, say_stalled, post_merge_busy. Existing qc_uv_cache not_a_dir remains separate. Consolidated cases add no duplicate stand-in or product mechanism.

Seven parity levers passed before consolidation, with 13 seeded defects total. Consolidated clean scenarios passed CI-emulated single-item runs. Seeded levers and serial CPU comparison require the supervisor's next heavy slot; earlier timing is not evidence for the consolidated harness.
