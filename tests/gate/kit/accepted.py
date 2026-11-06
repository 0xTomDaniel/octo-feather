"""The scenario of tests/gate/kit/test_accepted.py (its item), this file its command
(testkit.main): scripts/octo-feather-accepted against fixture review-host registries,
review-page hand-offs and a throwaway repo (prepared once per gate run: the spec at c1, edited at
c2; and r0, the spec at c0).

The pilot 1 failure (2026-10-20): the owner pressed Accept spec, the page wrote its hand-off, and
octo-feather-accepted still exited 1 because it waited for a registry `accepted = true` that
nothing writes. Here Accept is the hand-off alone, exactly as the review page writes it.

Spec Chat is read only at its pin (the Skillfile fetch-only entry, `just vendored-fetch`'s warm
cache), never the box's clone (#96). With it the scenario checks:
- the versions: pinned review-serve.py, run as a server, serves tests/fixtures/accepted/*.spec.html
  with ETags V1 and V2 below (the ETag names the served body, the version its events record), so
  a change in its version rule fails here. Through its HTTP surface, never its private helpers
  (#104); its readiness read from its own stdout, no sleep;
- the cases: unregistered, no hand-off, a hand-written registry key, Accept at base, newer
  comments, stale base, re-accept, absolute, ./ and subdirectory SPEC_PATH, the unregistered
  reason, no argument, an agent actor's hand-off, a missing commit in another session or this one;
- the registry: pinned Spec Chat's review-host CLI registers a spec under an isolated
  XDG_STATE_HOME, and octo-feather-accepted finds that row and its Accept (#96, director finding
  47: it once read an env var Spec Chat never reads).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from testkit import FIXTURES, Scratch, kit, main

TAG = "accepted test"
FX = FIXTURES / "accepted"
V1 = "9a91105876313c1c1c25cb0dbdb5244af32ea96fe36e4009b6a7373255c8991d"  # a.spec.html
V2 = "9beb7ff92e817947ef4b7a4241d7cddf36d24f84c00cbe00058240d1610c7a86"  # a-edited.spec.html
SPEC = "docs/specs/a.spec.html"
SPOOL_SIDE = "human"  # Spec Chat's owner side of the spool
CACHE_HOME = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")  # the warm cache's


def build(p: Scratch) -> None:
    for name, files in (("repo", ("a.spec.html", "a-edited.spec.html")), ("r0", ("a.spec.html",))):
        r = p.root / name
        (r / "docs/specs").mkdir(parents=True)
        p.git(r, "init", "-q", "-b", "main")
        for i, f in enumerate(files):
            shutil.copy2(FX / f, r / SPEC)
            p.git(r, "add", "-A")
            p.git(r, "commit", "-qm", "spec" if i == 0 else "edit")


def served(s: Scratch, sc: Path) -> list[str]:
    """The ETags pinned review-serve.py serves for a.spec.html and a-edited.spec.html."""
    x = s.root / "x"
    x.mkdir()
    for f in ("a.spec.html", "a-edited.spec.html"):
        shutil.copy2(FX / f, x)
    env = {**s.env, "XDG_STATE_HOME": str(s.root / "xdg-serve")}
    p = subprocess.Popen(["python3", "-u", str(sc / "review-spec/assets/review-serve.py"), str(x), "--port", "0"],
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        url, seen = "", []
        assert p.stdout is not None
        for ln in p.stdout:  # its own readiness line, read from its pipe
            seen.append(ln)
            if ln.startswith("spec-chat review-serve on http://"):
                url = ln.split(" on ", 1)[1].split()[0]
                break
        assert url, f"{TAG}: pinned review-serve did not start: {''.join(seen)}"
        tags = []
        for f in ("a.spec.html", "a-edited.spec.html"):
            with urllib.request.urlopen(f"{url}/{f}") as r:  # noqa: S310: a local URL it printed
                tags.append((r.headers.get("ETag") or "").strip('"'))
        return tags
    finally:
        p.kill()
        p.wait()


def accepted(s: Scratch) -> None:
    s.prepare("accepted", build)
    t = s.root
    sc = Path(s.run([kit("check-vendored"), "--extract", "spec-chat", str(t / "sc")],
                    env={"XDG_CACHE_HOME": CACHE_HOME}).out)
    got = served(s, sc)
    assert got == [V1, V2], (
        f"{TAG}: Spec Chat's served version rule changed (got {got}); update scripts/octo-feather-accepted "
        "served_version and the pins here")
    r = t / "repo"
    c1 = s.git(r, "rev-parse", "HEAD~1")
    c2 = s.git(r, "rev-parse", "HEAD")
    state = t / "xdg" / "spec-chat"
    for d in ("default", "other"):
        (state / "hosting" / d).mkdir(parents=True)
    s.env |= {"XDG_STATE_HOME": str(t / "xdg")}  # fixture rows; the real registry case is last
    spool = r / f"{SPEC}.review" / SPOOL_SIDE
    reg = state / "hosting" / "default" / "registry.toml"

    def row(base: str, at: str, extra: str = "") -> str:
        return (f'[[resource]]\nid = "spec:a-flow:p::{SPEC}"\nslug = "a-flow"\nroot = "{r}"\nspec = "{SPEC}"\n'
                f'base = "{base}"\nupdated_at = "{at}"\n{extra}\n')

    def handoff(stamp: str, hid: str, version: str, events: str | None = None, *, to: Path | None = None) -> None:
        """One hand-off as the review page writes it: stamp, id, version, and an events list for comments."""
        d = to or spool
        d.mkdir(parents=True, exist_ok=True)
        h: dict[str, object] = {"id": hid, "event": "handoff", "anchorId": "", "actor": SPOOL_SIDE,
                                "createdAt": f"2026-10-20T15:{int(stamp[-2:]) % 60:02d}:00.000Z",
                                "schemaVersion": 1, "version": version}
        if events:
            h["events"] = json.loads(events)
        (d / f"{stamp}-handoff-{hid}.json").write_text(json.dumps(h) + "\n")

    def run(want: int, *args: str, cwd: Path | None = None, repo: Path | None = r) -> str:
        a = [*args, "--repo", str(repo)] if repo else list(args)
        x = s.run([kit("octo-feather-accepted"), *a], want=want, cwd=cwd)
        return x.out if not x.err else f"{x.out}\n{x.err}".strip("\n")

    def like(out: str, *parts: str, start: bool = False) -> None:
        """OUT holds PARTS in order (the first at its start when START), as a shell glob would."""
        at = 0
        for i, part in enumerate(parts):
            j = out.find(part, at)
            assert j >= 0 and not (start and i == 0 and j != 0), f"{TAG}: {out!r} does not match {parts}"
            at = j + len(part)

    run(1, SPEC)  # not registered
    reg.write_text(row(c1, "2026-10-20T15:00:00Z"))
    like(run(1, SPEC), "no hand-off")
    reg.write_text(row(c1, "2026-10-20T15:00:00Z", "accepted = true"))
    run(1, SPEC)  # a hand-written registry key is not an Accept
    reg.write_text(row(c1, "2026-10-20T15:00:00Z"))
    handoff("1792509686764211101", "acc1", V1)
    out = run(0, SPEC)  # pilot 1: register, press Accept, exit 0
    like(out, f"accepted {c1} slug=a-flow at=2026-10-20T15:", start=True)
    assert out.endswith(f" session=default id=spec:a-flow:p::{SPEC} handoff=acc1"), f"{TAG}: bad output: {out}"
    handoff("1792509686764211102", "com1", V1, '[{"id": "c1"}]')
    like(run(1, SPEC), "sends comments")
    handoff("1792509686764211103", "acc2", V1)
    reg.write_text(row(c2, "2026-10-20T15:10:00Z"))
    like(run(1, SPEC), "not on the spec at registered commit")  # base moved to an edited spec
    handoff("1792509686764211104", "acc3", V2)
    like(run(0, SPEC), f"accepted {c2} ", start=True)
    # gh#64: the same Accept is found however SPEC_PATH is given.
    like(run(0, str(r / SPEC)), f"accepted {c2} ", start=True)
    like(run(0, f"./{SPEC}"), f"accepted {c2} ", start=True)
    like(run(0, "specs/a.spec.html", cwd=r / "docs", repo=None), f"accepted {c2} ", start=True)
    like(run(1, "docs/specs/missing.spec.html"), "SPEC_PATH docs/specs/missing.spec.html", "tried docs/specs/missing.spec.html",
         f"registered: {SPEC}")
    out = run(64, repo=None)
    assert "SPEC_PATH" in out.splitlines()[0], f"{TAG}: no argument: {out}"
    (spool / "1792509686764211199-handoff-ag1.json").write_text(json.dumps(
        {"id": "ag1", "event": "handoff", "actor": "agent", "createdAt": "2026-10-20T15:59:00.000Z", "version": V1}) + "\n")
    out = run(0, SPEC)
    like(out, f"accepted {c2} ", start=True)
    assert out.endswith("handoff=acc3"), f"{TAG}: an agent-actor hand-off counted: {out}"
    missing = "0123456789abcdef0123456789abcdef01234567"
    (state / "hosting" / "other" / "registry.toml").write_text(row(missing, "2026-10-20T16:00:00Z"))
    like(run(0, SPEC), f"accepted {c2} ", "session=default", start=True)
    reg.write_text(row(missing, "2026-10-20T16:00:00Z"))
    like(run(1, SPEC), "is not in")
    # The registry pinned Spec Chat's review-host writes (no --state-dir, no Herdr session), under its own
    # XDG_STATE_HOME: octo-feather-accepted finds the row, then its Accept.
    host = str(sc / "review-spec/scripts/review-host.py")
    r0 = t / "r0"
    c0 = s.git(r0, "rev-parse", "HEAD")
    s.env = {k: v for k, v in s.env.items() if k != "HERDR_SESSION"} | {
        "XDG_STATE_HOME": str(t / "xdg-host"), "SPEC_CHAT_APPROVED_INGRESS_PORTS": ""}
    s.run(["python3", host, "register", "--owner", "t", "--slug", "a-flow", "--base", c0, SPEC], cwd=r0)
    try:
        like(run(1, SPEC, repo=r0), "a-flow: no hand-off")
        handoff("1792509686764211301", "real1", V1, to=r0 / f"{SPEC}.review" / SPOOL_SIDE)
        out = run(0, SPEC, repo=r0)
        like(out, f"accepted {c0} slug=a-flow ", " session=default ", start=True)
        assert out.endswith("handoff=real1"), f"{TAG}: Accept on the registered row: {out}"
    finally:
        s.run(["python3", host, "stop"], cwd=r0)


if __name__ == "__main__":
    main(accepted)
