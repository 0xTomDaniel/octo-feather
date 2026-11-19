"""The world of the `just install-check` items (tests/install-check*.sh, one section each, #508;
their scenarios: tests/gate/kit/install_check.py): a Scratch made into a box, offline, the kit's
justfile run in a target as `just -f KIT/justfile install-check [TARGET]` (#996).

Stand-ins, only for systems the kit does not own: Herdr, the testkit's herdr (FAKES; the recipe
only finds it on PATH); GitHub, the testkit's gh over a tape of real gh's `gh auth status`
(testkit/recordings/install-check.json; each install-check run asks it once, so the log is
cleared before each run); Pi, tests/fixtures/install-check/pi, at the pin unless PI_STUB_VERSION
says another, each call logged (nomodel reads it), which also plays the model proxy for
`just install-check-models` (the testkit's other Pi stand-ins, classify-stub/pi and pi_agent.py,
answer no version and no proxy keyed by Pi's models.json and auth.json); and the host probes the
recipe reads, shell stubs in Box.bin: systemctl (`--user show` answers the file unit), agent-browser
(`doctor` answers doctor.json, else its version), uname (-r answers kver, the rest the real one),
unshare (refused while userns-off exists), ffmpeg, rg. Real: mise, uv, just, git, python3, their
installs the caller's (MISE_DATA_DIR, UV_PYTHON_INSTALL_DIR kept while HOME is a fresh dir; nothing
is installed). The state folder with its lanes/, the commit identity, and the live kit install (a
clone of a bare origin, on main) are made fresh.

PATH (#422 item 10): `hide` drops only the named programs, each PATH dir holding one mirrored minus
them (links to the rest), never dropped, so the tools sharing its dir stay. `clean` is the caller's
PATH without mise, linear or rg, plus `shared`, the owner's Debian layout (linear and the only mise
in one dir), mirrored minus linear; `shims` mise's shims dir minus rg. A run's PATH: PRE, the
stubs, EXTRA, the shims, clean.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from testkit import FIXTURES, HERE, ROOT, Scratch, asked
from testkit.jsonwalk import at, seq

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

PI_STUB = FIXTURES / "install-check" / "pi"
GH_TAPE = HERE / "recordings" / "install-check.json"
# Unset in every install-check run: a cache folder, a Chrome and a Spec Chat clone of the caller's.
UNSET = ("XDG_CACHE_HOME", "AGENT_BROWSER_EXECUTABLE_PATH", "SPEC_CHAT_CLONE")


def pinned(name: str) -> str:
    """The kit's pin file NAME, stripped."""
    return (ROOT / name).read_text().strip()


def field(raw: str, where: str, *keys: str | int) -> str:
    """The string at KEYS in RAW, a JSON text WHERE names (the testkit's walk, jsonwalk.at); else
    fail naming the path."""
    v = at(json.loads(raw), *keys, where=where)
    assert isinstance(v, str), f"{where}: {'.'.join(map(str, keys))} is no string: {v!r}"
    return v


def argv(line: str, where: str) -> list[str]:
    """LINE, a JSON list of strings WHERE names (a stub's logged argv)."""
    items = seq(json.loads(line))
    assert all(isinstance(x, str) for x in items), f"{where}: not all strings: {line}"
    return cast("list[str]", items)


@dataclass(frozen=True)
class Out:
    """One run's exit and its stdout and stderr together, as `$(... 2>&1)` keeps them."""

    rc: int
    text: str

    def has(self, line: str) -> bool:
        """A line equal to LINE (grep -qxF)."""
        return line in self.text.splitlines()

    def full(self, rx: str) -> bool:
        """A line RX matches whole (grep -qx, -qxE)."""
        return any(re.fullmatch(rx, x) for x in self.text.splitlines())

    def find(self, rx: str) -> bool:
        """A line RX matches from its start, or anywhere when RX holds no ^ (grep -qE)."""
        return re.search(rx, self.text, re.MULTILINE) is not None


class Box:
    """S made into a box install-check runs on (the module docstring)."""

    def __init__(self, s: Scratch) -> None:
        self.s, t = s, s.root
        self.t = t
        self.bin = s.bin
        self.pin, self.ppin, self.mpin = (
            pinned("pi-version"),
            pinned(".python-version"),
            pinned("mise-version"),
        )
        self.real_py3 = shutil.which("python3") or "python3"
        self.real_unshare = shutil.which("unshare") or "unshare"
        self.calls = t / "pi-calls"
        self.calls.write_text("")
        (self.bin / "pi").unlink()
        (self.bin / "pi").symlink_to(PI_STUB)
        homes = {
            "MISE_DATA_DIR": os.environ.get("MISE_DATA_DIR")
            or str(Path.home() / ".local/share/mise"),
            "UV_PYTHON_INSTALL_DIR": asked("uv", "python", "dir"),
        }
        s.env |= homes | {
            "XDG_STATE_HOME": str(t / "state"),
            "PI_STUB_LOG": str(self.calls),
            "PI_STUB_VERSION": self.pin,
        }
        (s.gh.dir / "tape.json").write_text(GH_TAPE.read_text())
        self.stub("rg", "exit 0")
        self.stub("systemctl", f'[ "$1 $2" = "--user show" ] && exec cat "{t}/unit"\nexit 1')
        self.unit("active", "enabled")
        self.agent_browser("0.40.0")
        self.okchrome = self.s.home / ".agent-browser/browsers/chrome-156/chrome-linux64/chrome"
        self.chrome(self.okchrome)
        self.kernel("6.12.0")
        uname = shutil.which("uname") or "uname"
        self.stub("uname", f'[ "$1" = -r ] && exec cat "{t}/kver"\nexec "{uname}" "$@"')
        off = "unshare: write failed /proc/self/uid_map: Operation not permitted"
        self.stub("unshare", f'[ -e "{t}/userns-off" ] && {{ echo "{off}" >&2; exit 1; }}\nexit 0')
        self.stub("ffmpeg", "exit 0")
        (t / "state/octo-feather/lanes").mkdir(parents=True)
        s.identity()  # the commit identity (#665), ok in every case
        self.git("init", "-q", "--bare", str(t / "kit-origin.git"))
        self.git("clone", "-q", str(t / "kit-origin.git"), str(t / "kitinst"))
        self.kitinst = t / "kitinst"
        self.git("-C", str(self.kitinst), "commit", "-q", "--allow-empty", "-m", "one")
        self.git("-C", str(self.kitinst), "push", "-q", "origin", "main")
        # mise's own just, linked: its dir on the recipe's PATH (never one holding a linear), the
        # link resolving to mise's install, so install-check's PATH rule holds.
        (self.bin / "just").symlink_to(asked("mise", "which", "just"))
        real_shims = field(asked("mise", "doctor", "--json"), "mise doctor --json", "dirs", "shims")
        shared = t / "shared"
        shared.mkdir()
        (shared / "mise").symlink_to(shutil.which("mise") or "mise")
        (shared / "linear").write_text('#!/bin/sh\necho "linear 3.1.0"\n')
        (shared / "linear").chmod(0o755)
        self.shims = self.hide(["rg"], [real_shims])[0]
        caller = os.environ["PATH"].split(os.pathsep)
        self.clean = self.hide(["linear", "rg"], [str(shared), *self.hide(["mise"], caller)])
        mise = shutil.which("mise", path=os.pathsep.join(self.clean))
        assert mise, f"no mise on the clean PATH: {self.clean}"
        self.mdir = str(Path(mise).parent)  # shared mirrored minus linear
        self.lin_target, self.gh_target = t / "linear", t / "github"
        for d in (self.lin_target, self.gh_target):
            self.git("init", "-q", str(d))
        (self.lin_target / "sub").mkdir()
        shutil.copy(FIXTURES / "install-check/linear/.octo-feather.toml", self.lin_target)

    def git(self, *args: str) -> None:
        """git ARGS with the scratch identity and main as the first branch."""
        ident = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main"]
        self.s.run(["git", *ident, *args])

    def stub(self, name: str, body: str, where: Path | None = None) -> Path:
        """A host probe NAME in WHERE (default the stubs dir): a shell script running BODY. It
        replaces any NAME there, never writing through it: Scratch.bin's fakes are links into the
        kit (testkit FAKES), so a write would rewrite the kit's own stand-in for every later
        item."""
        p = (where or self.bin) / name
        p.unlink(missing_ok=True)
        p.write_text(f"#!/bin/sh\n{body}\n")
        p.chmod(0o755)
        return p

    def unit(self, active: str, file: str) -> None:
        """The review service's state as `systemctl --user show` answers it."""
        (self.t / "unit").write_text(f"ActiveState={active}\nUnitFileState={file}\n")

    def agent_browser(self, version: str) -> None:
        self.stub(
            "agent-browser",
            f'[ "$1" = doctor ] && exec cat "{self.t}/doctor.json"\necho "agent-browser {version}"',
        )

    def chrome(self, at: Path | None) -> None:
        """`agent-browser doctor --offline --quick --json` naming Chrome AT (pass), else none."""
        ok = {"message": f"Google Chrome for Testing 156.0.8078.4 at {at}", "status": "pass"}
        c = ok if at else {"message": "Chrome not found", "status": "fail"}
        check = {"category": "Chrome", "id": "chrome.installed", **c}
        (self.t / "doctor.json").write_text(json.dumps({"checks": [check]}) + "\n")

    def kernel(self, release: str) -> None:
        (self.t / "kver").write_text(release + "\n")

    def hide(self, names: Iterable[str], dirs: Iterable[str]) -> list[str]:
        """DIRS with only NAMES gone: each dir holding one mirrored minus them (the docstring)."""
        names, out = set(names), list[str]()
        for d in filter(None, dirs):
            if not any(os.path.lexists(Path(d, n)) for n in names):
                out.append(d)
                continue
            m = Path(tempfile.mkdtemp(prefix="mirror.", dir=self.t))
            for f in sorted(Path(d).iterdir()) if Path(d).is_dir() else []:
                if f.name not in names:
                    (m / f.name).symlink_to(f)
            out.append(str(m))
        return out

    def path(self, *, pre: str | None = None, extra: str | None = None) -> str:
        dirs = [pre, str(self.bin), extra, self.shims, *self.clean]
        return os.pathsep.join(d for d in dirs if d)

    def env(self, path: str, **more: str) -> dict[str, str]:
        """An install-check run's environment: the scratch's, the fake gh's log cleared, UNSET
        unset, the state folder, the kit install, the data folder, PATH, then MORE."""
        (self.s.gh.dir / "log").write_text("")
        env = {k: v for k, v in self.s.env.items() if k not in UNSET}
        env |= {
            "OCTO_FEATHER_KIT_INSTALL": str(self.kitinst),
            "XDG_DATA_HOME": str(self.s.home / ".local/share"),
            "PATH": path,
        }
        return env | more

    def run(
        self, want: int | None, cmd: list[str], cwd: Path, env: Mapping[str, str], what: str
    ) -> Out:
        """CMD's exit and output, run in CWD with ENV; fails naming WHAT unless it exits WANT
        (None: any exit)."""
        p = subprocess.run(
            cmd,
            cwd=cwd,
            env=dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        out = Out(p.returncode, p.stdout.rstrip("\n"))
        assert want in (None, out.rc), f"{what}: want exit {want}, got {out.rc}: {out.text}"
        return out

    def check(
        self,
        want: int,
        cwd: Path,
        extra: str | None = None,
        target: Path | None = None,
        *,
        pre: Path | None = None,
        **env: str,
    ) -> Out:
        """`just -f KIT/justfile install-check [TARGET]` in CWD exiting WANT, PRE first and EXTRA
        after the stubs on PATH, ENV over the run's environment."""
        cmd = [
            "just",
            "-f",
            str(ROOT / "justfile"),
            "install-check",
            *([str(target)] if target else []),
        ]
        e = self.env(self.path(pre=str(pre) if pre else None, extra=extra), **env)
        return self.run(want, cmd, cwd, e, f"in {cwd} (PATH extra '{extra or ''}')")

    def nomodel(self) -> None:
        """No install-check run so far called a model (a Pi call in print mode, -p or --print)."""
        calls = [argv(x, "the stub pi's log") for x in self.calls.read_text().splitlines()]
        assert not [c for c in calls if {"-p", "--print"} & set(c)], (
            f"install-check called a model: {calls}"
        )

    def kit_copy(self, dest: Path) -> None:
        """DEST holding the kit's tracked files, as they are in its working tree."""
        files = self.s.run(["git", "-C", str(ROOT), "ls-files", "-z"]).out
        for f in filter(None, files.split("\0")):
            src, to = ROOT / f, dest / f
            if not os.path.lexists(src):
                continue
            to.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, to, follow_symlinks=False)
