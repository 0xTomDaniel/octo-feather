"""The scenario of tests/gate/kit/test_evidence_store.py (its items, one per template), this
file its command (testkit.main): the evidence store (quality spec #evidence-store, docs/adr/0025), through
its public surfaces: each template's verify-app helper and the kit's octo-feather-evidence
command. In a repo copied from the template LANG, a verify-app drive at a commit adds one record
naming that commit, the drive's criterion with the hash of its text in the repo's starter spec,
the contract and fixture versions, and holding the drive's outputs; editing that text changes the
next record's hash, a drive whose criterion has no text in the repo's specs fails naming it;
earlier records stay byte-identical and the repo's git status does not change
(#acceptance-evidence-record). With records at two commits, reading the criterion at one commit
shows only its records (#acceptance-evidence-read). One store per target: the other template's
repo has another store. An unknown commit is refused, naming it. The store lives under a
throwaway XDG_STATE_HOME.

Offline: typescript's packages copied from the run's one offline install of the template from the
pnpm store (tests/lib/prepared.py) (its helper reads qc.toml with smol-toml), its setup then a
no-op; python's setup a bare venv (the helper's python; no pip: nothing is installed in it), the
entry the source on PYTHONPATH."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from testkit import ROOT, Scratch, main, pnpm_store

TAG = "evidence test"
CRIT = "app#acceptance-hello-json"
# The starter spec's criterion text as written (worked literals, not read from the spec), before
# and after an edit.
TEXT1 = (
    "Given a user with the app installed, When they run app hello with a name and --json, Then the "
    "command exits 0 and prints one JSON document holding the name and its greeting."
)
TEXT2 = TEXT1.replace("holding the name", "holding the given name")
SPEC = "docs/specs/app.spec.html"
SETUP = {
    "typescript": 'setup = "true"',
    "python": """setup = 'python3 -m venv --without-pip "$QC_REPO/.venv"'""",
}
EV = str(ROOT / "scripts" / "octo-feather-evidence")
COMMAND = """command = 'PYTHONPATH="$QC_REPO/src" "$QC_REPO/.venv/bin/python" -m app.cli'"""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def copy(s: Scratch, lang: str) -> Path:
    """The template LANG's tracked files at S/LANG-app, as the test sets its contract up; not yet
    a repo."""
    repo = s.root / f"{lang}-app"
    src = ROOT / "templates" / lang
    names = subprocess.run(
        ["git", "ls-files", "-z"],  # noqa: S607
        cwd=src,
        capture_output=True,
        check=True,
    ).stdout.decode()
    for rel in filter(None, names.split("\0")):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, repo / rel, follow_symlinks=False)
    qc = repo / "qc.toml"
    text = re.sub(r"(?m)^setup = .*", lambda _: SETUP[lang], qc.read_text())
    if lang == "python":
        text = re.sub(r"(?m)^command = .*", lambda _: COMMAND, text)
    qc.write_text(text)
    return repo


def store_files(store: Path) -> dict[str, str]:
    return {str(p.relative_to(store)): sha(p.read_bytes()) for p in store.rglob("*") if p.is_file()}


class Target:
    """The template LANG's repo in S, a git repo of one commit, and its verify-app helper."""

    def __init__(self, s: Scratch, lang: str) -> None:
        self.s, self.lang = s, lang
        self.repo = copy(s, lang)
        if lang == "typescript":
            p = s.run(
                [sys.executable, str(ROOT / "tests" / "lib" / "prepared.py"), lang, str(s.root)]
            )
            subprocess.run(["cp", "-a", f"{p.out}/node_modules", str(self.repo)], check=True)  # noqa: S607
        commit(s, self.repo)
        self.va = str(self.repo / ".agents" / "skills" / "verify-app" / "scripts" / "verify-app")

    def launch_drive(self) -> tuple[int, str]:
        """launch, then drive hello (as `launch && drive`), then cleanup: the exit and output."""
        out, rc = "", 0
        for step in (["launch"], ["drive", "hello"]):
            p = subprocess.run(
                [self.va, *step],
                cwd=self.s.root,
                env=self.s.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            out += p.stdout
            rc = p.returncode
            if rc:
                break
        subprocess.run(
            [self.va, "cleanup"], cwd=self.s.root, env=self.s.env, capture_output=True, check=False
        )
        return rc, out

    def drive(self) -> str:
        """A drive that passes: its record id."""
        rc, out = self.launch_drive()
        m = re.search(r"(?m)^verify-app: evidence record (\S+) ", out)
        assert rc == 0, f"{TAG}: {self.lang}: drive failed (exit {rc}): {out}"
        assert m, f"{TAG}: {self.lang}: drive printed no record id: {out}"
        return m.group(1)

    def status(self) -> str:
        return self.s.git(self.repo, "status", "--porcelain=v1")

    def read(self, *args: str) -> str:
        return self.s.run([EV, "read", "--repo", str(self.repo), *args]).out


def commit(s: Scratch, repo: Path) -> None:
    s.git(repo, "init", "-q")
    s.git(repo, "add", "-A")
    s.git(repo, "commit", "-qm", "init")


def evidence(s: Scratch, lang: str) -> None:
    t = s.root.resolve()
    s.env |= {
        "XDG_STATE_HOME": str(t / "state"),
        "PATH": f"{ROOT / 'scripts'}{os.pathsep}{s.env['PATH']}",
        "VERIFY_APP_RUN_DIR": str(t / "va" / "run"),
        "VERIFY_APP_EVIDENCE_DIR": str(t / "va" / "evidence"),
        "npm_config_store_dir": pnpm_store(),  # the caller's, never the scratch HOME's
    }
    g = Target(s, lang)
    status0 = g.status()
    c1 = s.git(g.repo, "rev-parse", "HEAD")
    id1 = g.drive()
    store = Path(s.run([EV, "where", "--repo", str(g.repo)]).out)
    assert str(store).startswith(f"{t}/state/octo-feather/evidence/"), f"{TAG}: {lang}: {store}"
    snap1 = store_files(store)
    # The criterion's text edited in the starter spec and committed, a second drive: one more
    # record, the first byte-identical.
    spec = g.repo / SPEC
    spec.write_text(spec.read_text().replace("holding the name", "holding the given name"))
    s.git(g.repo, "commit", "-qam", "change")
    c2 = s.git(g.repo, "rev-parse", "HEAD")
    status1 = g.status()
    id2 = g.drive()
    assert id1 != id2, f"{TAG}: {lang}: two drives gave one record id {id1}"
    assert g.status() == status1 == status0, f"{TAG}: {lang}: a drive changed git status"
    now = store_files(store)
    assert {k: now.get(k) for k in snap1} == snap1, f"{TAG}: {lang}: an earlier record changed"
    n = len(list(store.rglob("record.json")))
    assert n == 2, f"{TAG}: {lang}: want 2 records after 2 drives, got {n}"
    first_read(g, c1, id1)
    text = g.read("--criterion", CRIT, "--commit", c2[:10])
    for want in (f"record {id2}", f"revision {c2}", "Hello, Ada"):
        assert want in text, f"{TAG}: {lang}: text read at the second commit lacks {want}: {text}"
    assert f"record {id1}" not in text, f"{TAG}: {lang}: text read at c2 shows {id1}: {text}"
    assert g.read("--criterion", "other#x", "--commit", c1, "--json") == "[]", f"{TAG}: other#x"
    # The edited text: the second commit's record hashes it, not the first text.
    c = json.loads(g.read("--criterion", CRIT, "--commit", c2, "--json"))[0]["record"]["criterion"]
    assert c["text_from"] == "spec", c
    assert c["text_sha256"] == sha(TEXT2.encode()) != sha(TEXT1.encode()), c
    # No text for the criterion in the repo's specs: the drive fails naming it, keeps no record.
    spec.rename(t / "app.spec.html")
    rc, vout = g.launch_drive()
    (t / "app.spec.html").rename(spec)
    assert rc != 0, f"{TAG}: {lang}: a drive with no criterion text passed: {vout}"
    assert CRIT in vout, f"{TAG}: {lang}: a drive with no criterion text did not name it: {vout}"
    assert not re.search(r"(?m)^verify-app: evidence record \S* \(criterion", vout), vout
    n = len(list(store.rglob("record.json")))
    assert n == 2, f"{TAG}: {lang}: a drive with no criterion text kept a record ({n} records)"
    # One store per target: the other template's repo has another.
    o = copy(s, "typescript" if lang == "python" else "python")
    commit(s, o)
    there = s.run([EV, "where", "--repo", str(o)]).out
    assert there != str(store), f"{TAG}: two targets share one store {there}"
    # An unknown commit: refused, naming it.
    bad = s.run([EV, "read", "--repo", str(g.repo), "--commit", "nope"], want=1)
    assert "nope" in bad.out + bad.err, f"{TAG}: an unknown commit not named: {bad}"


def first_read(g: Target, c1: str, id1: str) -> None:
    """Read at the first commit: only its record, with its keys and outputs."""
    out = g.read("--criterion", CRIT, "--commit", c1, "--json")
    recs = json.loads(out)
    assert [x["record"]["id"] for x in recs] == [id1], f"{TAG}: {g.lang}: read at c1: {out}"
    r = recs[0]["record"]
    assert r["format"] == 1, r
    assert r["revision"] == c1, r
    assert r["dirty"] is False, r
    assert r["criterion"]["id"] == CRIT, r
    assert r["criterion"]["text_from"] == "spec", r
    assert r["criterion"]["text_sha256"] == sha(TEXT1.encode()), r
    assert r["contract"] == {"format": 2, "sha256": sha((g.repo / "qc.toml").read_bytes())}, r
    assert r["fixture"] is None, r["fixture"]
    outs = r["outputs"]
    assert "json.stdout" in outs, outs
    assert "summary.txt" in outs, outs
    got = Path(recs[0]["dir"], "outputs", "json.stdout").read_bytes()
    assert json.loads(got) == {"name": "Ada", "text": "Hello, Ada"}, got
    assert outs["json.stdout"]["sha256"] == sha(got), outs
    # No key names a path on this box (#evidence-portable).
    assert "/" + "tmp" not in json.dumps(r), r
    assert str(g.repo) not in json.dumps(r), r


if __name__ == "__main__":
    main(evidence)
