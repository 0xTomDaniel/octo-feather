"""The scenarios of tests/gate/kit/test_herdr_extension.py, this file their command (testkit.main):
herdr-spawn installs Herdr's Pi extension for each launch alone, in a dir named by the launch's
session under the state dir, and herdr-close (a close and a park) removes a closed agent's dir
(#1140; owner ruling 2026-11-19 #1132). End to end through the kit's commands in a copy of the
kit, with the testkit's Herdr and systemd stand-ins and real processes standing in for each pane's
Pi (lane_stale.Factory: what each stands for).

own_extension: two launches run as the gate items ran herdr-spawn (a scratch state dir, a given
cache dir standing in for the box's). close_ends_extension: a close and a park of those agents."""

from __future__ import annotations

from typing import cast

from lane_stale import Factory
from testkit import Scratch, main

# What the Herdr stand-in installs (testkit/herdr.py, INTEGRATION).
INTEGRATION = "// installed by herdr\n// HERDR_INTEGRATION_ID=pi\n"


def own_extension(s: Scratch) -> None:
    """Two launches leave the given cache dir with no Herdr extension file, and get two files,
    each under its own session's dir, each launch's --extension naming its own."""
    cache = s.root / "box-cache"
    s.env |= {"XDG_CACHE_HOME": str(cache), "XDG_STATE_HOME": str(s.root / "state")}
    f = Factory(s)
    try:
        a, b = f.launch("implementer-a"), f.launch("implementer-b")
        files = [p for p in cache.rglob("*") if p.is_file()]
        leaked = [p for p in files if "HERDR_INTEGRATION_ID" in p.read_text(errors="replace")]
        assert not leaked, f"a Herdr extension in the given cache dir: {leaked}"
        ext_a, ext_b = f.herdr_extension(a), f.herdr_extension(b)
        assert ext_a != ext_b, ext_a
        assert ext_a.read_text() == ext_b.read_text() == INTEGRATION
    finally:
        f.close()


def close_ends_extension(s: Scratch) -> None:
    """herdr-close of A's tab removes A's session dir and not B's; parking B removes B's."""
    f = Factory(s)
    try:
        a, b = f.launch("implementer-a"), f.launch("implementer-b")
        dir_a, dir_b = f.herdr_extension(a).parent, f.herdr_extension(b).parent
        close = str(f.kit / ".agents" / "skills" / "herdr-comms" / "assets" / "herdr-close")
        s.run([close, cast("str", f.agents()[a]["tab_id"])])
        assert not dir_a.exists(), f"{dir_a} kept after its tab closed"
        assert f.herdr_extension(b).read_text() == INTEGRATION, f"{dir_b} touched by A's close"
        s.run([close, "--park", b])
        assert not dir_b.exists(), f"{dir_b} kept after its agent parked"
    finally:
        f.close()


if __name__ == "__main__":
    main(own_extension, close_ends_extension)
