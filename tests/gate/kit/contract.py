"""The scenarios of tests/gate/kit/test_contract.py (its items), this file their command
(testkit.main): octo-feather-contract (quality spec #qc-contract), run as a command.

`variants`: on copies of each template's qc.toml. A valid contract prints ok; a missing format
version, an unsupported one, a missing, unknown or mistyped key, bad TOML and no qc.toml each fail
naming the field or the fix; two arguments are refused with the usage. `ts_drive`: the
TypeScript template's verify-app drives what its qc.toml declares: with the repo's packages not
installed, launch fails naming smol-toml and `just setup`, before any setup; then a changed value
and setup are followed with no helper edit; a declared service it cannot start is refused before
setup."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, main, pnpm_store

if TYPE_CHECKING:
    from pathlib import Path

TAG = "contract test"
CMD = str(ROOT / "scripts" / "octo-feather-contract")
PY = (ROOT / "templates" / "python" / "qc.toml").read_text()
DEMO = '[demo."app#acceptance-other"]'


def sub(pat: str, repl: str) -> str:
    """PY with each line's match of PAT replaced (sed s///)."""
    return re.sub(f"(?m){pat}", lambda _: repl, PY, count=0)


def drop(pat: str, text: str = PY) -> str:
    """TEXT without its lines matching PAT (sed /PAT/d)."""
    return "".join(ln for ln in text.splitlines(keepends=True) if not re.search(pat, ln))


def add(*lines: str, text: str = PY) -> str:
    """TEXT with LINES appended (sed $a)."""
    return text + "".join(f"{ln}\n" for ln in lines)


def cut_from(pat: str, text: str, *repl: str) -> str:
    """TEXT up to its first line matching PAT, then REPL (sed /PAT/,$d or $c)."""
    lines = text.splitlines(keepends=True)
    n = next(i for i, ln in enumerate(lines) if re.search(pat, ln))
    return "".join(lines[:n]) + "".join(f"{ln}\n" for ln in repl)


def without_entry() -> str:
    """PY without [entry] through its command line (sed /^\\[entry\\]/,/^command/d)."""
    lines = PY.splitlines(keepends=True)
    a = lines.index("[entry]\n")
    b = next(i for i in range(a + 1, len(lines)) if lines[i].startswith("command"))
    return "".join(lines[:a] + lines[b + 1 :])


V2 = sub("^format = 2", "format = 1")
BAD: dict[str, tuple[str, str]] = {
    "no-format": (
        drop("^format = "),
        "qc.toml: missing format (the contract's format version; supported: 1, 2)",
    ),
    "format-3": (
        sub("^format = 2", "format = 3"),
        "qc.toml: format 3 is not a supported format version (supported: 1, 2)",
    ),
    "format-str": (sub("^format = 2", 'format = "2"'), "qc.toml: format must be an integer"),
    "no-entry": (without_entry(), "qc.toml: missing entry"),
    "no-command": (drop("^command = "), "qc.toml: entry: missing command"),
    "no-services": (drop(r"^\[services\]"), "qc.toml: missing services"),
    "extra": (sub("^setup = ", 'colour = "red"\nsetup = '), "qc.toml: unknown key colour"),
    "value-int": (sub('^name = "Ada"', "name = 7"), "qc.toml: values.name must be a string"),
    "service-no-command": (
        sub(r"^\[services\]", '[services.web]\nready = "/"'),
        "qc.toml: services.web: missing command",
    ),
    "fixture-extra": (
        sub(r"^\[fixture\]", '[fixture.seed]\nreset = "true"\nseed = 1'),
        "qc.toml: fixture.seed: unknown key seed",
    ),
    "empty-setup": (sub("^setup = .*", 'setup = ""'), "qc.toml: setup must not be empty"),
    "bad-toml": (sub("^format = 2", "format = "), "qc.toml: not TOML:"),
    # [browser]: the verify skill drives a headless browser at a Playwright release pin
    # (remote spec, host tools).
    "browser-latest": (
        add("[browser]", 'playwright = "latest"'),
        r"qc.toml: browser.playwright must match ^[0-9]+\.[0-9]+\.[0-9]+$",
    ),
    "browser-no-pin": (add("[browser]"), "qc.toml: browser: missing playwright"),
    # [demo."<spec>#<anchor>"]: per-criterion metadata, its demo command only for a criterion no
    # tagged test covers; which tests enforce it is the tag on each test, never a list here.
    "demo-tests": (
        add(DEMO, 'command = "x"', 'covers = ["src"]', 'tests = ["t"]'),
        "qc.toml: demo.app#acceptance-other: unknown key tests",
    ),
    "demo-no-covers": (
        add(DEMO, 'command = "x"', "covers = []"),
        "qc.toml: demo.app#acceptance-other.covers: [] should be non-empty",
    ),
    "demo-extra": (
        add(DEMO, 'command = "x"', 'covers = ["src"]', 'checks = "y"'),
        "qc.toml: demo.app#acceptance-other: unknown key checks",
    ),
    "demo-bad-id": (
        add("[demo.acceptance-other]", 'command = "x"', 'covers = ["src"]'),
        "qc.toml: demo must match ^[a-z0-9][a-z0-9._-]*#[A-Za-z0-9][A-Za-z0-9._-]*$",
    ),
    # fixtures: names of this contract's [fixture] entries; artifacts: files the run must leave.
    "demo-fixture-unknown": (
        add(DEMO, 'covers = ["src"]', 'fixtures = ["seed"]'),
        (
            "qc.toml: demo.app#acceptance-other.fixtures: seed is no declared fixture; declare "
            "it under [fixture.seed]"
        ),
    ),
    "demo-artifact-empty": (
        add(DEMO, 'covers = ["src"]', 'artifacts = [""]'),
        "qc.toml: demo.app#acceptance-other.artifacts.0 must not be empty",
    ),
    # tags: the command writing the tagged cases (OCTO_FEATHER_QC_TAGS), a non-empty string.
    "tags-empty": (sub("^setup = ", 'tags = ""\nsetup = '), "qc.toml: tags must not be empty"),
    # Format 1 still reads as before: its demo needs a command and the tests list.
    "v1-demo": (
        cut_from(r"^\[demo\.", V2, DEMO, 'covers = ["src"]'),
        "qc.toml: demo.app#acceptance-other: missing command",
    ),
}
GOOD: dict[str, tuple[str, str]] = {
    "browser": (add("[browser]", 'playwright = "1.64.1"'), ""),
    "demo": (
        add(DEMO, 'command = "app hello Ada --json"', "browser = false", 'covers = ["src"]'),
        "ok (format 2)",
    ),
    # format 2: an entry without a command (metadata only).
    "demo-no-command": (add(DEMO, 'covers = ["src"]'), ""),
    "demo-expect": (
        add(
            DEMO,
            'covers = ["src"]',
            'fixtures = ["seed"]',
            'artifacts = ["out/a.txt", "out/shots/"]',
            text=sub(r"^\[fixture\]", '[fixture.seed]\nreset = "true"'),
        ),
        "",
    ),
    "v1": (cut_from(r"^\[demo\.", V2), "ok (format 1)"),
}


def run(s: Scratch, *args: str, cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(
        [CMD, *args],
        cwd=cwd or s.root,
        env=s.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return p.returncode, p.stdout.rstrip("\n")


def variants(s: Scratch) -> None:
    t = s.root.resolve()
    for lang in ("python", "typescript"):
        (t / lang).mkdir()
        shutil.copy(ROOT / "templates" / lang / "qc.toml", t / lang)
        rc, out = run(s, str(t / lang))
        want = f"octo-feather-contract: {t}/{lang}/qc.toml: ok (format 2)"
        assert (rc, out) == (0, want), f"{TAG}: {lang} template contract not ok (exit {rc}): {out}"
        rc, out = run(s, str(t / lang / "qc.toml"))
        assert rc == 0, f"{TAG}: {lang}: a path to the file itself not ok: {out}"
    rc, out = run(s, cwd=t / "python")
    assert rc == 0, f"{TAG}: no argument does not read ./qc.toml: {out}"
    for name, (text, said) in {**GOOD, **BAD}.items():
        (t / name).mkdir()
        (t / name / "qc.toml").write_text(text)
        rc, out = run(s, str(t / name))
        if name in GOOD:
            assert rc == 0, f"{TAG}: {name}: not ok (exit {rc}): {out}"
            assert out.endswith(said), f"{TAG}: {name}: want '{said}': {out}"
        else:
            assert rc == 1, f"{TAG}: {name}: want exit 1 naming '{said}', got exit {rc}: {out}"
            assert said in out, f"{TAG}: {name}: want exit 1 naming '{said}': {out}"
    (t / "none").mkdir()
    rc, out = run(s, str(t / "none"))
    assert rc == 1, f"{TAG}: none: want exit 1, got {rc}: {out}"
    assert f"no qc.toml at {t}/none/qc.toml" in out, f"{TAG}: none: {out}"
    rc, out = run(s, str(t / "python"), str(t / "python"))
    assert rc == 2, f"{TAG}: two arguments not refused (exit {rc}): {out}"
    assert "usage: octo-feather-contract [REPO-OR-QC.TOML]" in out, f"{TAG}: no usage: {out}"


def ts_drive(s: Scratch) -> None:
    """The TypeScript template's verify-app invokes only what qc.toml declares: its setup (here a
    marker) and its entry, driven with the contract's value. It reads qc.toml with the TOML
    package smol-toml: with the repo's packages not installed, launch fails naming it and `just
    setup`, before any setup; then the packages are copied from the run's one offline install of
    the template from the pnpm store (tests/lib/prepared.py), as `just setup` installs them."""
    t = s.root.resolve()
    repo = t / "ts-app"
    src = ROOT / "templates" / "typescript"
    names = subprocess.run(
        ["git", "ls-files", "-z"],  # noqa: S607
        cwd=src,
        capture_output=True,
        check=True,
    ).stdout.decode()
    for rel in filter(None, names.split("\0")):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, repo / rel, follow_symlinks=False)
    s.git(t, "init", "-q", str(repo))
    s.git(repo, "commit", "-qm", "init", "--allow-empty")
    qc = repo / "qc.toml"
    qc.write_text(
        re.sub(
            r"(?m)^setup = .*",
            lambda _: 'setup = "echo declared > \\"$QC_REPO/setup-ran\\""',
            qc.read_text(),
        )
    )
    va = str(repo / ".agents" / "skills" / "verify-app" / "scripts" / "verify-app")

    def helper(step: str, **env: str) -> tuple[int, str]:
        p = subprocess.run(
            [va, step],
            cwd=t,
            env={**s.env, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return p.returncode, p.stdout

    first = {
        "VERIFY_APP_RUN_DIR": str(t / "va0/run"),
        "VERIFY_APP_EVIDENCE_DIR": str(t / "va0/evidence"),
    }
    rc, out = helper("launch", **first)
    assert rc == 1, f"{TAG}: launch with no packages: want exit 1, got {rc}: {out}"
    assert "cannot load the TOML reader smol-toml" in out, f"{TAG}: smol-toml not named: {out}"
    assert "just setup" in out, f"{TAG}: just setup not named: {out}"
    assert not (repo / "setup-ran").exists(), f"{TAG}: setup ran before the refusal"
    s.env["npm_config_store_dir"] = pnpm_store()  # the caller's, never the scratch HOME's
    # The install with the caller's HOME: pnpm's own metadata cache, never fetched again (#509).
    prep = [sys.executable, str(ROOT / "tests" / "lib" / "prepared.py"), "typescript", str(t)]
    p = s.run(prep, env={"HOME": os.environ["HOME"]})
    subprocess.run(["cp", "-a", f"{p.out}/node_modules", str(repo)], check=True)  # noqa: S607
    text = re.sub(r'(?m)^name = "Ada"', 'name = "Grace"', qc.read_text())
    qc.write_text(re.sub(r"(?m)^greeting = .*", 'greeting = "Hello, Grace"', text))
    rc, out = run(s, str(repo))
    assert rc == 0, f"{TAG}: edited ts contract not ok: {out}"
    # Its drive appends an evidence record: to a throwaway store, never the box's.
    ev = t / "va" / "evidence"
    s.env |= {
        "VERIFY_APP_RUN_DIR": str(t / "va" / "run"),
        "VERIFY_APP_EVIDENCE_DIR": str(ev),
        "XDG_STATE_HOME": str(t / "state"),
        "PATH": f"{ROOT / 'scripts'}:{s.env['PATH']}",
    }
    rc, out = helper("run")
    assert rc == 0, f"{TAG}: verify-app run on the edited contract failed (exit {rc}): {out}"
    assert (repo / "setup-ran").read_text() == "declared\n", (
        f"{TAG}: the declared setup did not run"
    )
    got = (ev / "hello" / "json.stdout").read_text().rstrip("\n")
    assert got == '{"name":"Grace","text":"Hello, Grace"}', (
        f"{TAG}: drive did not follow values: {got}"
    )
    # A contract declaring a service this CLI helper cannot start: launch refuses, naming it,
    # before setup.
    (repo / "setup-ran").unlink()
    qc.write_text(drop(r"^\[services\]$", qc.read_text() + '[services.web]\ncommand = "true"\n'))
    rc, out = helper("launch")
    assert rc != 0, f"{TAG}: a declared service was not refused: {out}"
    assert "qc.toml declares services (web)" in out, f"{TAG}: the service not named: {out}"
    assert not (repo / "setup-ran").exists(), f"{TAG}: setup ran before the service refusal"


if __name__ == "__main__":
    main(variants, ts_drive)
