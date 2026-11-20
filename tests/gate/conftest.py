"""One JSON trend line per pytest run, written from the run's junit xml (#201, #224).

Copyable unchanged into any repo whose pytest writes junit xml (--junitxml): it names no
repo path. After the run, it appends one line to check-runs.jsonl in the state dir: the
output of `octo-feather-state` when that command is on PATH, else
${XDG_STATE_HOME:-~/.local/state}/octo-feather. Fields: start (UTC), repo (git top level
of the working dir), head, total_s (the run's elapsed wall seconds: the junit testsuite time,
which pytest's junitxml measures on the controller from session start; never a sum of item
times), exit, tier (`full` only when the invocation narrowed nothing: no paths or node ids, so pytest
ran its configured testpaths, and no -k, -m, --lf, --sw, --deselect, --ignore or --ignore-glob, and
the gate's static steps ran: when the root's justfile declares GATE_RECIPES (each a test item), the
run's GATE_RECIPES is that value, so a bare pytest, which skips them, is no full run; and the run was not stopped
early: -x, --maxfail, or a red static check ending it (session.shouldfail or shouldstop set); else `subset`),
steps (name, node: its pytest node id, seconds, result: ok, FAIL, ERROR or skipped, cpu_s: below), one per junit
testcase (under xdist their seconds overlap, so their sum exceeds total_s), load1_start and load1_end (the box's
1-minute load average when the session starts and when it ends, null where the OS has none: a slow run told apart from
a heavy one). A missing junit file or an unwritable state dir is a
warning on stderr, never a failure: the trend line never changes the run's exit status.

Also copyable unchanged: longest items first (#618; gate-time discipline: quality spec #test-kinds). The run reads
this repo's trend lines (repo the same git top level) once, on the controller, before any item runs: each item's
wall seconds on the last line that has its node id (a step's node; on a line before node ids, its name, the junit
testcase name, pytest's item name). Items with a
record are reordered among their own places, longest first (ties keep collection order); an item with none keeps
its place; no history at all leaves collection order. xdist workers get the controller's read (pytest_configure_node),
so every worker collects the same order. Under xdist's --dist load (the default with -n) the run deals the order out
one item per worker per round, two rounds, then one item to each worker as it finishes one (xdist runs an item once
it holds the next, so each worker holds two): the longest items start first, on different workers. Why not prior
art: xdist 3.8.0 hands items out in collection order; its load mode sends each worker a run of consecutive items
first (two, or a quarter of its share), so a sort alone would queue the longest items on one worker; worksteal
first splits the whole order into one consecutive block per worker and steals only from a queue's tail, so neither
alone ends the tail. pytest-slow-first 1.0.3 (2024) and pytest-slowest-first 0.2.0 sort from their own duration
file and leave the dealing to xdist; pytest-timing 0.4.0 (--timing-schedule) plans from its own JSON and puts
unknown items at the mean. Each is a second duration store beside the trend file, none matches on repo, and none
keeps an unknown item's place: so a sort here and a scheduler on xdist's own pytest_xdist_make_scheduler hook.

Also copyable unchanged: each item's CPU seconds (what the run must show: quality spec #acceptance-test-cpu-shown), cpu_s:
user and system CPU of the process running the item (an xdist worker, or pytest itself) and of every process it started
and waited for (RUSAGE_CHILDREN: a grandchild counts once each process between waited for it; a process left running,
or whose parent exited without waiting, does not), from its setup to its teardown, carried to the controller and the
junit xml as the item's cpu_s property. Shared set-up is billed to its own line, never to the item that builds it first
(#687): while an item runs, GATE_SHARED_CPU names a file; a process that builds state the run's items share appends
one JSON line there, {"line": NAME, "cpu_s": its CPU building it}; the item's cpu_s leaves that out, and the item's
cpu_shared property ({NAME: seconds}, JSON; the trend step's cpu_shared) carries it. After the run the controller
shows each item's CPU and wall seconds, each shared line, and names each item over test_cpu_seconds in the root's
gate-budget.toml (its form: octo-feather-lane --help, report) but one carrying pytest's `e2e` marker (quality spec
#acceptance-test-cpu-budget). Such an item the change adds or changes (since the merge base with the default
branch), as `octo-feather-gate changed` (when on PATH) names one, is measured again once, alone: after the run, in a
pytest of its own (-n 0 under xdist) from the same root and environment, GATE_CPU_AGAIN set there so it judges
nothing. Over again (or no CPU measured), it fails the run, named with both CPU times and the budget; under, the run
passes and names it over once, with both. One unchanged is reported only, as is a shared line; no item over the
budget, no second run. Stdlib getrusage, not a plugin: pytest-monitor (last release
2023) measures the pytest process only, into its own sqlite, without xdist; pytest-timing (new in 2026) records CPU into its own report, with no
per-test budget.

Also copyable unchanged: the qc capture's side of the gate (what it must capture: quality spec #qc-capture). A test
carries pytest's `criterion` marker, `@pytest.mark.criterion("<spec>#<anchor>", ..., source=PATH)`. Inert unless
OCTO_FEATHER_QC_CLAIMS (space-separated <spec>#<anchor>) is set: then, before any test runs, a narrowed invocation
(_tier) is refused and each claim checked against its spec; every collecting process writes the plan into a capture
dir; a claimed tagged case runs through `octo-feather-qc --capture-case` (fixture qc_command); after the run the
controller hands plan, pytest reports and capture notes to `octo-feather-qc --capture-store`. A store that fails
fails the run.
OCTO_FEATHER_QC_TAGS=FILE (octo-feather-qc, with --collect-only): the collecting process writes every tagged
case and its criteria there as JSON, so qc knows exactly which criteria a test carries; such a run adds no trend line.
OCTO_FEATHER_GATE_ITEMS=FILE (octo-feather-gate select, with --collect-only): the collecting process writes every
collected item there as JSON, {node id: {"e2e": whether it carries pytest's e2e marker}}, so one collection names the
items and their tier.
"""
import datetime, functools, hashlib, json, os, re, shutil, subprocess, sys, tempfile
try:
    import resource
except ImportError:   # not POSIX: no CPU measure
    resource = None
try:
    import tomllib
except ImportError:   # before Python 3.11: no per-test CPU budget read
    tomllib = None
from collections.abc import Callable, Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast
import xml.etree.ElementTree as ET

import pytest

if TYPE_CHECKING:
    from xdist.remote import Producer  # pyright: ignore[reportMissingTypeStubs]

TREND = "check-runs.jsonl"
CLAIMS = "OCTO_FEATHER_QC_CLAIMS"
CAPTURE_DIR = "OCTO_FEATHER_QC_CAPTURE_DIR"   # set by the controller before any worker starts
TAGS = "OCTO_FEATHER_QC_TAGS"
ITEMS = "OCTO_FEATHER_GATE_ITEMS"
CPU = "cpu_s"
NODE = "node"   # a step's pytest node id, unique where its junit name is not
BUDGET, BUDGET_KEY = "gate-budget.toml", "test_cpu_seconds"
AGAIN = "GATE_CPU_AGAIN"   # set in the run that measures a changed over-budget item again alone
SHARED, SHARED_PROP = "GATE_SHARED_CPU", "cpu_shared"   # shared set-up's own CPU lines (this file's docstring)
CLAIM = re.compile(r"^([a-z0-9][a-z0-9._-]*)#([A-Za-z0-9][A-Za-z0-9._-]*)$")
LAST = "octo_feather_last_seconds"   # the controller's read, in each xdist worker's workerinput
_LAST = pytest.StashKey[dict[str, float]]()
_LOAD_START = pytest.StashKey["float | None"]()


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


@functools.cache
def _static_short(root: Path) -> bool:
    """True when this run lacks some of the gate's static steps: ROOT's justfile declares GATE_RECIPES (from just's own
    --dump) and this run's environment does not hold exactly that literal value; a justfile just cannot read, or a
    value that is no string literal, is unknown, so short."""
    try:
        p = subprocess.run(["just", "--dump", "--dump-format", "json"], cwd=root, capture_output=True, text=True)
    except OSError:
        return any((root / n).is_file() for n in ("justfile", "Justfile", ".justfile"))
    if p.returncode:
        return "No justfile found" not in p.stderr
    declared = json.loads(p.stdout).get("assignments", {}).get("GATE_RECIPES")
    return declared is not None and declared.get("value") != os.environ.get("GATE_RECIPES")


def _tier(config: pytest.Config) -> str:
    o = config.option
    narrowed = (config.args_source == pytest.Config.ArgsSource.ARGS, o.keyword, o.markexpr, getattr(o, "lf", False),
                getattr(o, "stepwise", False), o.deselect, o.ignore, o.ignore_glob)
    return "subset" if any(narrowed) or _static_short(config.rootpath) else "full"


def _entry(xml_path, status, tier: str):
    suite = ET.parse(xml_path).getroot()
    suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
    start = datetime.datetime.fromisoformat(suite.get("timestamp")).astimezone(datetime.timezone.utc)
    return {"start": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "repo": _git("rev-parse", "--show-toplevel") or os.getcwd(),
            "head": _git("rev-parse", "HEAD"), "total_s": round(float(suite.get("time")), 3), "exit": int(status),
            "tier": tier, "steps": [{"name": c.get("name"), **_node(c), "seconds": round(float(c.get("time") or 0), 3), "result": _result(c), **_cpu_s(c), **_cpu_shared(c)}
                      for c in suite.iter("testcase")]}


def _load1() -> float | None:
    try:
        return round(os.getloadavg()[0], 2)
    except (OSError, AttributeError):   # no load average on this OS
        return None


def _last_seconds() -> dict[str, float]:
    """Each item's wall seconds on the last trend line of this repo that names it ({} without history)."""
    repo = _git("rev-parse", "--show-toplevel") or os.getcwd()
    mark = '"repo":' + json.dumps(repo)   # as _entry writes it: lines of other repos skip the parse
    last: dict[str, float] = {}
    try:
        with open(os.path.join(_state_dir(), TREND)) as f:
            for line in f:
                if mark not in line:
                    continue
                try:   # a line not of the runner's form: skipped from its first bad field
                    d: Any = json.loads(line)
                    if d["repo"] == repo:
                        for s in d["steps"]:
                            last[str(s.get(NODE) or s["name"])] = float(s["seconds"])
                except (ValueError, KeyError, TypeError):
                    continue
    except OSError:
        return {}
    return last


def _longest_first(items: list[pytest.Item], last: dict[str, float]) -> None:
    def seconds(i: pytest.Item) -> float | None:   # by node id, else by name (a line before node ids)
        return last.get(i.nodeid, last.get(i.name))

    places = [n for n, i in enumerate(items) if seconds(i) is not None]
    for n, i in zip(places, sorted((items[n] for n in places), key=lambda i: -(seconds(i) or 0)), strict=True):
        items[n] = i


class _Node(Protocol):   # what pytest_configure_node reads of xdist's WorkerController
    workerinput: dict[str, object]
    config: pytest.Config


@pytest.hookimpl(optionalhook=True)   # xdist's: each worker sorts from the controller's read
def pytest_configure_node(node: _Node) -> None:
    node.workerinput[LAST] = node.config.stash.get(_LAST, None) or {}


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_make_scheduler(config: pytest.Config, log: "Producer | None") -> object:
    """--dist load, dealt out one item per worker per round (this file's docstring); any other mode: xdist's own."""
    if config.getoption("dist") != "load":
        return None
    from xdist.scheduler import LoadScheduling  # noqa: PLC0415  # pyright: ignore[reportMissingTypeStubs]  # xdist only here: the file runs without it

    class Dealt(LoadScheduling):
        def __init__(self, config: pytest.Config, log: "Producer | None") -> None:
            super().__init__(config, log)
            self.maxschedchunk = self.maxschedchunk or 1   # after the deal, one item at a time

        def schedule(self) -> None:
            if self.collection is not None or not self._check_nodes_have_same_collection():
                return super().schedule()
            self.collection = next(iter(self.node2collection.values()))
            self.pending[:] = range(len(self.collection))
            for _ in range(2):
                for node in self.nodes:
                    self._send_tests(node, 1)
            if not self.pending:
                for node in self.nodes:
                    node.shutdown()
            return None

    return Dealt(config, log)


def pytest_sessionstart(session: pytest.Session) -> None:
    session.config.stash[_LOAD_START] = _load1()


def _node(case: ET.Element) -> dict[str, str]:
    p = case.find(f"properties/property[@name='{NODE}']")
    return {} if p is None else {NODE: str(p.get("value"))}


def _cpu_s(case: ET.Element) -> dict[str, float]:
    p = case.find(f"properties/property[@name='{CPU}']")
    return {} if p is None else {CPU: float(p.get("value") or 0)}


def _cpu_shared(case: ET.Element) -> dict[str, object]:
    p = case.find(f"properties/property[@name='{SHARED_PROP}']")
    return {} if p is None else {SHARED_PROP: json.loads(p.get("value") or "{}")}


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
    config.addinivalue_line("markers", "e2e: an end-to-end test (its CPU: this file's docstring)")
    if not hasattr(config, "workerinput") and not _COLLECT_ONLY:
        config.pluginmanager.register(_CpuShown(config.rootpath), "cpu-shown")
    if not hasattr(config, "workerinput"):
        config.stash[_LAST] = _last_seconds()
    if not _claims() or hasattr(config, "workerinput"):
        return
    # Arranged before execution: every claim names a criterion of its spec, else nothing runs.
    root = Path(_git("rev-parse", "--show-toplevel") or Path.cwd())
    if _tier(config) != "full":   # a narrowed run would record only part of a criterion's cases: refused, nothing runs
        msg = (f"{CLAIMS} needs the full gate: this invocation narrows it (paths or node ids, -k, -m, --lf, --sw, "
               "--deselect, --ignore, or not the justfile's GATE_RECIPES); run the full gate with the claims, or unset "
               "them; nothing ran")
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
    given: dict[str, Any] = getattr(config, "workerinput", {})   # an xdist worker's: the controller's read
    _longest_first(items, given.get(LAST) or config.stash.get(_LAST, None) or {})
    if tags := os.environ.get(TAGS):
        Path(tags).write_text(json.dumps({i.nodeid: _tags(i) for i in items if _tags(i)}))
    if listed := os.environ.get(ITEMS):
        Path(listed).write_text(json.dumps({i.nodeid: {"e2e": i.get_closest_marker("e2e") is not None} for i in items}))
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



def _cpu() -> float:
    if resource is None:
        return 0.0
    s, c = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return s.ru_utime + s.ru_stime + c.ru_utime + c.ru_stime


_CPU_START = pytest.StashKey[float]()
_SHARED_FILE = pytest.StashKey[str]()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item: pytest.Item) -> Generator[None, object, object]:
    item.stash[_CPU_START] = _cpu()   # in the process running the item: an xdist worker runs one item at a time
    fd, path = tempfile.mkstemp(prefix="shared-cpu-")
    os.close(fd)
    item.stash[_SHARED_FILE], was = path, os.environ.get(SHARED)
    os.environ[SHARED] = path
    try:
        return (yield)
    finally:
        Path(path).unlink()
        if was is None:
            del os.environ[SHARED]
        else:
            os.environ[SHARED] = was


def _shared(path: str) -> dict[str, float]:
    """The shared lines an item's processes billed (this file's docstring); a line not of that form is skipped."""
    out: dict[str, float] = {}
    try:
        rows = Path(path).read_text().splitlines()
    except OSError:
        return out
    for line, cpu in filter(None, map(_shared_row, rows)):
        out[line] = out.get(line, 0.0) + cpu
    return out


def _shared_row(row: str) -> tuple[str, float] | None:
    try:
        d: Any = json.loads(row)
        return str(d["line"]), float(d["cpu_s"])
    except (ValueError, KeyError, TypeError):
        return None


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Generator[None, object, object]:
    if call.when == "teardown":   # before its report copies them
        item.user_properties.append((NODE, item.nodeid))
        if resource is not None and _CPU_START in item.stash:
            shared = _shared(item.stash[_SHARED_FILE]) if _SHARED_FILE in item.stash else {}
            own = _cpu() - item.stash[_CPU_START] - sum(shared.values())
            item.user_properties.append((CPU, round(max(own, 0.0), 3)))
            if shared:
                item.user_properties.append((SHARED_PROP, json.dumps({k: round(v, 3) for k, v in shared.items()})))
    return (yield)


def _secs(x: float) -> str:
    return f"{round(x, 3):g}s"


class _CpuShown:
    """The controller's side of the CPU measure (this file's docstring)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.items: dict[str, dict[str, Any]] = {}
        self.shared: list[tuple[str, float, str]] = []   # (line, CPU seconds, the item that built it)
        self.again_cpu: dict[str, float | None] = {}   # each changed item over the budget: its CPU run again alone
        self.failing: list[str] = []   # changed items over the budget twice: the run fails
        self.changed_why = ""

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        r = self.items.setdefault(report.nodeid, {"wall": 0.0, "cpu": None, "e2e": bool(report.keywords.get("e2e"))})
        r["wall"] += report.duration
        for k, v in report.user_properties:
            if k == CPU and report.when == "teardown" and isinstance(v, (int, float)):
                r["cpu"] = float(v)
            if k == SHARED_PROP and report.when == "teardown" and isinstance(v, str):
                self.shared += [(line, float(s), report.nodeid) for line, s in json.loads(v).items()]

    def over(self) -> list[tuple[str, dict[str, Any]]]:
        b = self.budget()[0]
        return [] if b is None else [(n, r) for n, r in self.items.items()
                                     if r["cpu"] is not None and not r["e2e"] and r["cpu"] > b]

    def changed(self) -> set[str] | None:
        """The changed test items as `octo-feather-gate changed` names them (pytest arguments), or None and why."""
        if not shutil.which("octo-feather-gate"):
            self.changed_why = "octo-feather-gate is not on PATH"
            return None
        p = subprocess.run(["octo-feather-gate", "changed"], cwd=self.root, capture_output=True, text=True)
        self.changed_why = " ".join(p.stderr.split())
        if p.returncode:
            self.changed_why = f"octo-feather-gate changed exited {p.returncode}: {self.changed_why}"
            return None
        return set(p.stdout.split())

    def again(self, config: pytest.Config, node: str) -> float | None:
        """NODE run again alone, serially, in a pytest of its own from the same root and environment: its CPU
        seconds from that run's junit xml, or None when it gave none."""
        with tempfile.TemporaryDirectory() as t:
            xml = Path(t) / "junit.xml"
            cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}", node]
            if config.pluginmanager.hasplugin("xdist"):
                cmd[3:3] = ["-n", "0"]
            env = {k: v for k, v in os.environ.items() if not k.startswith("OCTO_FEATHER_QC_")} | {AGAIN: "1"}
            subprocess.run(cmd, cwd=self.root, env=env, capture_output=True, check=False)
            try:
                cases = list(ET.parse(xml).getroot().iter("testcase"))
            except (OSError, ET.ParseError):
                return None
        return next((_cpu_s(c).get(CPU) for c in cases if _node(c).get(NODE) == node), None)

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        over, b = self.over(), self.budget()[0]
        if not over or b is None or os.environ.get(AGAIN):   # a run measuring one item again judges nothing
            return
        args = self.changed() or set[str]()
        for n, _ in over:
            if n in args or n.split("::")[0] in args:
                self.again_cpu[n] = cpu = self.again(session.config, n)
                if cpu is None or cpu > b:
                    self.failing.append(n)
        if self.failing and session.exitstatus == 0:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED

    def budget(self) -> tuple[float | None, str]:
        """test_cpu_seconds from the root's gate-budget.toml, or None and why."""
        if tomllib is None:
            return None, f"{BUDGET}: unread, no tomllib before Python 3.11"
        try:
            v = tomllib.loads((self.root / BUDGET).read_text()).get(BUDGET_KEY)
        except FileNotFoundError:
            return None, f"{BUDGET}: none"
        except (OSError, ValueError) as e:
            return None, f"{BUDGET}: {e}"
        if v is None:
            return None, f"{BUDGET}: no {BUDGET_KEY}"
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            return None, f"{BUDGET}: {BUDGET_KEY} {v!r} is not a number > 0"
        return float(v), ""

    def pytest_terminal_summary(self, terminalreporter: pytest.TerminalReporter) -> None:
        shown = sorted(((n, r) for n, r in self.items.items() if r["cpu"] is not None), key=lambda x: -x[1]["cpu"])
        if not shown:
            return
        tr = terminalreporter
        tr.write_sep("=", "CPU seconds per item (its processes and their waited-for children)")
        for n, r in shown:
            tr.write_line(f"{_secs(r['cpu']):>9} cpu {_secs(r['wall']):>9} wall  {n}" + ("  (e2e)" if r["e2e"] else ""))
        for line, s, n in sorted(self.shared, key=lambda x: -x[1]):
            tr.write_line(f"{_secs(s):>9} cpu {'':>9}       shared set-up {line} (built in {n}; its own line, report-only)")
        b, why = self.budget()
        if b is None:
            tr.write_line(f"cpu budget: none ({why})")
            return
        over = [(n, r) for n, r in shown if not r["e2e"] and r["cpu"] > b]
        for n, r in over:
            cpu = self.again_cpu.get(n)
            alone = "no CPU measured" if cpu is None else f"{_secs(cpu)} CPU"
            if n in self.failing:
                tr.write_line(f"OVER CPU BUDGET: {n} {_secs(r['cpu'])} CPU, alone again {alone}, budget {_secs(b)} "
                              "(changed, over twice: the gate fails)")
            elif n in self.again_cpu:
                tr.write_line(f"OVER CPU BUDGET: {n} {_secs(r['cpu'])} CPU, alone again {alone}, budget {_secs(b)} "
                              "(changed, over once: passes)")
            else:
                tr.write_line(f"OVER CPU BUDGET: {n} {_secs(r['cpu'])} CPU, budget {_secs(b)} (report-only)")
        if self.changed_why:
            tr.write_line(f"cpu budget: changed test items judged by octo-feather-gate: {self.changed_why}")
        once = len(self.again_cpu) - len(self.failing)
        tail = ([f"{len(self.failing)} changed over twice"] if self.failing else []) + (
            [f"{once} changed over once"] if once else [])
        verdict = "FAIL" if self.failing else "report-only" if not once else "passes"
        tr.write_line(f"cpu budget: {_secs(b)} per non-e2e test ({BUDGET} {BUDGET_KEY}): {len(over)} over, "
                      + "".join(f"{t}, " for t in tail) + verdict)


@pytest.hookimpl(trylast=True)   # after the junitxml plugin has written its file
def pytest_sessionfinish(session: pytest.Session):   # its exit: session.exitstatus, a budget's failure in it
    config = session.config
    if hasattr(config, "workerinput") or _COLLECT_ONLY:   # a worker, or no run: no line
        return
    xml_path = config.option.xmlpath
    try:
        if not xml_path:
            raise OSError("no --junitxml for this run")
        stopped = session.shouldfail or session.shouldstop   # it ran part of its items: no full run
        entry = _entry(xml_path, session.exitstatus, "subset" if stopped else _tier(session.config))
        entry |= {"load1_start": config.stash.get(_LOAD_START, None), "load1_end": _load1()}
        line = json.dumps(entry, separators=(",", ":"))
        d = _state_dir()
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, TREND), "a") as f:
            f.write(line + "\n")
    except (OSError, ET.ParseError, ValueError, TypeError, AttributeError) as e:
        print(f"trend: warning: line not written to {TREND} ({e}); the verdict stands", file=sys.stderr)
