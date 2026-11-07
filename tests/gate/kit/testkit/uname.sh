#!/bin/sh
# Stand-in for `uname` (the OS, which the kit does not own), put first on PATH by a scenario itself
# (testkit's docstring) to stand for another OS: prints FAKE_UNAME (default Linux), whatever its
# arguments, as `uname -s` would there. It reproduces no logic.
echo "${FAKE_UNAME:-Linux}"
