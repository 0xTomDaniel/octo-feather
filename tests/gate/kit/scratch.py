"""The scenarios of tests/gate/kit/test_scratch.py (its items), this file their command
(testkit.main): the testkit's Scratch keeps mise's state its own (#683; owner ruling 2026-11-05
#577: a test leaves no state behind and reads none of the user's). What mise records while a
scenario runs (`mise trust`, a shim's tracked config) lands in the scratch's mise-state dir,
whatever MISE_STATE_DIR the caller has (the user's, a gate run's), and goes with the scratch."""

from __future__ import annotations

import sys

from testkit import Scratch, main


def own_mise_state(s: Scratch) -> None:
    """A mise.toml trusted in the scratch is recorded in the scratch's own mise-state dir."""
    p = s.root / "repo"
    p.mkdir()
    (p / "mise.toml").write_text("[tools]\n")
    s.run(["mise", "trust", str(p / "mise.toml")], cwd=p)
    trusted = s.root / "mise-state" / "trusted-configs"
    got = sorted(str(t.resolve()) for t in trusted.iterdir()) if trusted.is_dir() else []
    assert got == [str(p.resolve())], f"trust not in the scratch's mise-state: {got}"
    sys.stdout.write(f"mise trusted {p} in {trusted}\n")


if __name__ == "__main__":
    main(own_mise_state)
