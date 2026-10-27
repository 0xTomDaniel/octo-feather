# #172 final review: module gate refused (lane gh167)

Reviewer repro at 5e22546 (old) vs this fix (new): scratch repo, justfile `mod sub`, sub/mod.just `alias c := check`, `check:`, `inner:`; demo criterion ending the command shown. `; fix:` hint trimmed.

```
$ (old) JUST_UNSTABLE=1 octo-feather-lane ticket - # demo: just sub check
stdin: ok
exit 0
$ (new) JUST_UNSTABLE=1 octo-feather-lane ticket - # demo: just sub check
stdin: class: layer-only-ticket: demo runs no surface the repo declares (`just sub check`: just sub check is a gate or factory recipe, not the app)
exit 1
$ (old) JUST_UNSTABLE=1 octo-feather-lane ticket - # demo: just sub c
stdin: ok
exit 0
$ (new) JUST_UNSTABLE=1 octo-feather-lane ticket - # demo: just sub c
stdin: class: layer-only-ticket: demo runs no surface the repo declares (`just sub c`: just sub c is a gate or factory recipe, not the app)
exit 1
$ (old) JUST_UNSTABLE=1 octo-feather-lane ticket - # demo: just sub inner
stdin: ok
exit 0
$ (new) JUST_UNSTABLE=1 octo-feather-lane ticket - # demo: just sub inner
stdin: ok
exit 0
```
