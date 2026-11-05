# Errors name the fix

A user who hits an error should not have to search for the way out. Every error message names the command that fixes it (for a missing notes file: run `app init`). A usage error (an unknown command or a missing argument) exits with status 2; every other error exits with status 1.

Status: accepted.
