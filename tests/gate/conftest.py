"""One JSON trend line per pytest run, written from the run's junit xml (#201, #224).

Copyable unchanged into any repo whose pytest writes junit xml (--junitxml): it names no
repo path. After the run, it appends one line to check-runs.jsonl in the state dir: the
output of `octo-feather-state` when that command is on PATH, else
${XDG_STATE_HOME:-~/.local/state}/octo-feather. Fields: start (UTC), repo (git top level
of the working dir), head, total_s (the run's elapsed wall seconds: the junit testsuite time,
which pytest's junitxml measures on the controller from session start; never a sum of item
times), exit, steps (name, seconds, result: ok, FAIL, ERROR or skipped), one per junit
testcase (under xdist their seconds overlap, so their sum exceeds total_s). A missing junit file or an unwritable state dir is a
warning on stderr, never a failure: the trend line never changes the run's exit status.
"""
import datetime, json, os, shutil, subprocess, sys
import xml.etree.ElementTree as ET

import pytest

TREND = "check-runs.jsonl"


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


def _entry(xml_path, status):
    suite = ET.parse(xml_path).getroot()
    suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
    start = datetime.datetime.fromisoformat(suite.get("timestamp")).astimezone(datetime.timezone.utc)
    return {"start": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "repo": _git("rev-parse", "--show-toplevel") or os.getcwd(),
            "head": _git("rev-parse", "HEAD"), "total_s": round(float(suite.get("time")), 3), "exit": int(status),
            "steps": [{"name": c.get("name"), "seconds": round(float(c.get("time") or 0), 3), "result": _result(c)}
                      for c in suite.iter("testcase")]}


@pytest.hookimpl(trylast=True)   # after the junitxml plugin has written its file
def pytest_sessionfinish(session, exitstatus):
    config = session.config
    if hasattr(config, "workerinput"):   # an xdist worker: the controller writes the one line
        return
    xml_path = config.option.xmlpath
    try:
        if not xml_path:
            raise OSError("no --junitxml for this run")
        line = json.dumps(_entry(xml_path, exitstatus), separators=(",", ":"))
        d = _state_dir()
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, TREND), "a") as f:
            f.write(line + "\n")
    except (OSError, ET.ParseError, ValueError, TypeError, AttributeError) as e:
        print(f"trend: warning: line not written to {TREND} ({e}); the verdict stands", file=sys.stderr)
