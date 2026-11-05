"""One JSON trend line per pytest run, written from the run's junit xml (#201, #224).

Copyable unchanged into any repo whose pytest writes junit xml (--junitxml): it names no
repo path. After the run, it appends one line to check-runs.jsonl in the state dir: the
output of `octo-feather-state` when that command is on PATH, else
${XDG_STATE_HOME:-~/.local/state}/octo-feather. Fields: start (UTC), repo (git top level
of the working dir), head, total_s (the run's elapsed wall seconds: the junit testsuite time,
which pytest's junitxml measures on the controller from session start; never a sum of item
times), exit, tier (`full` only when the invocation narrowed nothing: no paths or node ids, so pytest
ran its configured testpaths, and no -k, -m, --lf, --sw, --deselect, --ignore or --ignore-glob;
else `subset`), steps (name, seconds, result: ok, FAIL, ERROR or skipped), one per junit
testcase (under xdist their seconds overlap, so their sum exceeds total_s). A missing junit file or an unwritable state dir is a
warning on stderr, never a failure: the trend line never changes the run's exit status.

Also copyable unchanged: the qc capture's side of the gate (what it must capture: quality spec #qc-capture). A test
carries pytest's `criterion` marker, `@pytest.mark.criterion("<spec>#<anchor>", ..., source=PATH)`. Inert unless
OCTO_FEATHER_QC_CLAIMS (space-separated <spec>#<anchor>) is set: then, before any test runs, a narrowed invocation
(_tier) is refused and each claim checked against its spec; every collecting process writes the plan into a capture
dir; a claimed tagged case runs through `octo-feather-qc --capture-case` (fixture qc_command); after the run the
controller hands plan, pytest reports and capture notes to `octo-feather-qc --capture-store`. A store that fails
fails the run.
OCTO_FEATHER_QC_TAGS=FILE (octo-feather-qc, with --collect-only): the collecting process writes every tagged
case and its criteria there as JSON, so qc knows exactly which criteria a test carries; such a run adds no trend line.
"""
import datetime, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast
import xml.etree.ElementTree as ET

import pytest

TREND = "check-runs.jsonl"
CLAIMS = "OCTO_FEATHER_QC_CLAIMS"
CAPTURE_DIR = "OCTO_FEATHER_QC_CAPTURE_DIR"   # set by the controller before any worker starts
TAGS = "OCTO_FEATHER_QC_TAGS"
CLAIM = re.compile(r"^([a-z0-9][a-z0-9._-]*)#([A-Za-z0-9][A-Za-z0-9._-]*)$")


def _git(*args):
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True)
    except OSError:
        return None
    return (r.stdout.strip() or None) if r.returncode == 0 else None


def _state_dir():
    if shutil.which("octo-feather-state"):
        r = subprocess.run(["octo-feather-state"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "octo-feather")


def _result(case):
    for tag, result in (("failure", "FAIL"), ("error", "ERROR"), ("skipped", "skipped")):
        if case.find(tag) is not None:
            return result
    return "ok"


def _tier(config: pytest.Config) -> str:
    o = config.option
    narrowed = (config.args_source == pytest.Config.ArgsSource.ARGS, o.keyword, o.markexpr, getattr(o, "lf", False),
                getattr(o, "stepwise", False), o.deselect, o.ignore, o.ignore_glob)
    return "subset" if any(narrowed) else "full"


def _entry(xml_path, status, tier: str):
    suite = ET.parse(xml_path).getroot()
    suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
    start = datetime.datetime.fromisoformat(suite.get("timestamp")).astimezone(datetime.timezone.utc)
    return {"start": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "repo": _git("rev-parse", "--show-toplevel") or os.getcwd(),
            "head": _git("rev-parse", "HEAD"), "total_s": round(float(suite.get("time")), 3), "exit": int(status),
            "tier": tier, "steps": [{"name": c.get("name"), "seconds": round(float(c.get("time") or 0), 3), "result": _result(c)}
                      for c in suite.iter("testcase")]}


def _claims() -> list[str]:
    return os.environ.get(CLAIMS, "").split()


def _names_criterion(root: Path, claim: str) -> bool:
    m = CLAIM.match(claim)
    spec = root / "docs" / "specs" / f"{m.group(1)}.spec.html" if m else None
    return bool(m and spec and spec.is_file() and f'data-anchor="{m.group(2)}"' in spec.read_text(encoding="utf-8"))


_COLLECT_ONLY: list[bool] = []   # non-empty in a --collect-only run: no tests ran, so no trend line


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("collectonly"):
        _COLLECT_ONLY.append(True)
    config.addinivalue_line("markers", "criterion(*ids, source=None): the acceptance criteria (<spec>#<anchor>) this "
                            "test proves; source: the test's file when the item runs another one (quality #qc-capture)")
    if not _claims() or hasattr(config, "workerinput"):
        return
    # Arranged before execution: every claim names a criterion of its spec, else nothing runs.
    root = Path(_git("rev-parse", "--show-toplevel") or Path.cwd())
    if _tier(config) != "full":   # a narrowed run would record only part of a criterion's cases: refused, nothing runs
        msg = (f"{CLAIMS} needs the full gate: this invocation narrows it (paths or node ids, -k, -m, --lf, --sw, "
               "--deselect, --ignore); run the full gate with the claims, or unset them; nothing ran")
        raise pytest.UsageError(msg)
    bad = [c for c in _claims() if not _names_criterion(root, c)]
    if bad:
        msg = (f"{CLAIMS}: {' '.join(bad)} names no criterion: want <spec>#<anchor> with that anchor in "
               "docs/specs/<spec>.spec.html; nothing ran")
        raise pytest.UsageError(msg)
    d = tempfile.mkdtemp(prefix="qc-capture-")
    os.environ[CAPTURE_DIR] = d   # xdist workers, started after this, inherit it
    config.pluginmanager.register(_Capture(Path(d)), "qc-capture")


def _tags(item: pytest.Item) -> list[str]:
    return [str(c) for m in item.iter_markers("criterion") for c in m.args]


def _source(item: pytest.Item) -> str:
    for m in item.iter_markers("criterion"):
        if m.kwargs.get("source"):
            return str(m.kwargs["source"])
    return item.location[0]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if tags := os.environ.get(TAGS):
        Path(tags).write_text(json.dumps({i.nodeid: _tags(i) for i in items if _tags(i)}))
    d = os.environ.get(CAPTURE_DIR)
    if not d or not _claims():
        return
    plan = {i.nodeid: {"criteria": [c for c in _tags(i) if c in _claims()], "source": _source(i)} for i in items}
    workerinput: dict[str, str] = getattr(config, "workerinput", {})
    out = Path(d) / f"plan-{workerinput.get('workerid', 'main')}.json"
    out.write_text(json.dumps({k: v for k, v in plan.items() if v["criteria"]}))


def _note(d: Path, nodeid: str) -> Path:
    return d / f"case-{hashlib.sha256(nodeid.encode()).hexdigest()[:16]}.json"


@pytest.fixture
def qc_command(request: pytest.FixtureRequest) -> Callable[[list[str]], list[str]]:
    """A function giving the command this item runs: through `octo-feather-qc --capture-case` when the item is
    tagged with a claimed criterion and the run captures, else the command itself."""
    item = cast("pytest.Item", request.node)  # pyright: ignore[reportUnknownMemberType]  # pytest leaves node unannotated
    d = os.environ.get(CAPTURE_DIR)
    if not d or not set(_tags(item)) & set(_claims()):
        return lambda cmd: cmd
    note = str(_note(Path(d), item.nodeid))
    return lambda cmd: ["octo-feather-qc", "--capture-case", note, "--", *cmd]


def _read(path: Path) -> object:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


class _Capture:
    """The controller's side of a capturing run: the head and tree before any test runs, each case's report as pytest
    (or xdist, from its workers) hands it over, and the store after the run."""

    def __init__(self, d: Path) -> None:
        self.dir = d
        self.reports: dict[str, dict[str, Any]] = {}
        self.head, self.clean = _git("rev-parse", "HEAD"), not _git("status", "--porcelain")

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        r = self.reports.setdefault(report.nodeid, {"phases": {}, "output": "", "seconds": 0.0})
        why = report.longreprtext if report.outcome != "passed" else ""
        r["phases"][report.when] = {"outcome": report.outcome, "why": why[-2000:]}
        r["seconds"] = round(r["seconds"] + report.duration, 3)
        if report.when == "call" or report.outcome != "passed":
            r["output"] = "".join(f"--- {name} ---\n{body}" for name, body in report.sections)

    @pytest.hookimpl(tryfirst=True)   # before the trend line
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        try:
            plan: dict[str, object] = {}
            for f in sorted(self.dir.glob("plan-*.json")):
                plan.update(json.loads(f.read_text()))
            notes = {n: _read(_note(self.dir, n)) for n in plan}
            session_file = self.dir / "session.json"
            session_file.write_text(json.dumps({
                "claims": _claims(), "plan": plan, "reports": self.reports,
                "notes": {n: v for n, v in notes.items() if v is not None}, "head_at_start": self.head,
                "clean_at_start": self.clean, "argv": sys.argv[1:], "tier": _tier(session.config),
                "exit": int(exitstatus)}))
            p = subprocess.run(["octo-feather-qc", "--capture-store", str(session_file)],  # noqa: S607
                               capture_output=True, text=True, check=False)
            sys.stdout.write("\n" + p.stdout)   # after the progress line
            sys.stderr.write(p.stderr)
            if p.returncode:
                sys.stderr.write(f"qc capture: octo-feather-qc --capture-store exited {p.returncode}: the claimed "
                                 "criteria have no record from this run; the gate fails\n")
                session.exitstatus = 1
        finally:
            shutil.rmtree(self.dir, ignore_errors=True)



@pytest.hookimpl(trylast=True)   # after the junitxml plugin has written its file
def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    config = session.config
    if hasattr(config, "workerinput") or _COLLECT_ONLY:   # a worker, or no run: no line
        return
    xml_path = config.option.xmlpath
    try:
        if not xml_path:
            raise OSError("no --junitxml for this run")
        line = json.dumps(_entry(xml_path, exitstatus, _tier(session.config)), separators=(",", ":"))
        d = _state_dir()
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, TREND), "a") as f:
            f.write(line + "\n")
    except (OSError, ET.ParseError, ValueError, TypeError, AttributeError) as e:
        print(f"trend: warning: line not written to {TREND} ({e}); the verdict stands", file=sys.stderr)
