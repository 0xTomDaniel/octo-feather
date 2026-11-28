#!/usr/bin/env python3
"""lane_cli: the lane commands' shared parts: what two or more command groups use, the help's order (help_doc) and the live kit install's rule (kit_install). Moved from scripts/octo-feather-lane, the dispatcher (ticket #1333)."""

import ast
import datetime
import functools
import importlib.machinery
import importlib.util
import os
import re
import subprocess
from pathlib import Path
from typing import cast

import tracker_calls

dtm = datetime   # the hub's `import datetime as dtm`


def kit_install() -> Path:
    """The live kit install, the one rule for which dir it is: just install-check asks this too
    (#422)."""
    return Path(os.environ.get("OCTO_FEATHER_KIT_INSTALL") or KIT)


NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
KIT = Path(__file__).resolve().parent.parent


class Refuse(Exception):
    """A refusal: message names the fix, exit 1, nothing moved."""


gh = functools.partial(tracker_calls.gh, err=Refuse)   # the lane's gh calls raise its own Refuse
pr_view = functools.partial(tracker_calls.pr_view, err=Refuse)


def lanes_dir() -> Path:
    state = Path(__file__).resolve().with_name("octo-feather-state")
    out = subprocess.run([str(state)], capture_output=True, text=True, check=True).stdout
    return Path(out.strip()) / "lanes"


def lane_name(args: list[str], cmd: str = "archive") -> str:
    if len(args) != 1 or not NAME.fullmatch(args[0]) or args[0].endswith((".toml", ".jsonl")):
        raise Refuse(f"usage: octo-feather-lane {cmd} NAME (the lane record's name without .toml, e.g. supervisor-gh12; got {' '.join(args) or 'nothing'})")
    return args[0]


@functools.cache
def reflect_module():
    """scripts/octo-feather-reflect: the question list, brief, reflector run, reply parser and log lines."""
    loader = importlib.machinery.SourceFileLoader("octo_feather_reflect", str(KIT / "scripts" / "octo-feather-reflect"))
    spec = importlib.util.spec_from_loader("octo_feather_reflect", loader)
    assert spec is not None, "a SourceFileLoader always yields a spec"
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def pr_number(s: str) -> int:
    if not re.fullmatch(r"[1-9][0-9]*", s or ""):
        raise Refuse(f"PR must be a positive integer, got {s!r}")
    return int(s)


def take_repo(args: list[str]) -> tuple[list[str], str | None]:
    if "--repo" not in args:
        return args, None
    i = args.index("--repo")
    if i + 1 >= len(args) or not re.fullmatch(r"[\w.-]+/[\w.-]+", args[i + 1]):
        raise Refuse("--repo needs OWNER/NAME")
    return args[:i] + args[i + 2:], args[i + 1]


def no_traceback(fn):
    """Malformed PR data from gh is a refusal naming the fix, never a traceback."""
    def run(args: list[str]) -> int:
        try:
            return fn(args)
        except (KeyError, TypeError, AttributeError, ValueError, IndexError) as e:
            raise Refuse(f"unexpected PR data from gh ({type(e).__name__}: {e}): check the gh on PATH (gh --version), then rerun") from e
    return run


class Unchecked(Refuse):
    """Nothing could be checked (gh, file or specs error): exit 2, no ticket reported as passed."""


def q(v: str) -> str:
    """V as a Markdown code span."""
    return f"`` {v} ``" if "`" in v else f"`{v}`"


def state_dir() -> Path:
    return lanes_dir().parent


# octo-feather-lane --help, in order: (module, chunk) for each chunk of a module's HELP.
HELP_ORDER = (
    ("lane_cli", "header"),
    ("lane_reflection", "archive"),
    ("lane_reflection", "reflect"),
    ("post_merge", "archive-merged"),
    ("lane_review", "verdict-usage"),
    ("merge_ask", "merge-ask-usage"),
    ("ci_start", "ci-start-usage"),
    ("lane_review", "judge"),
    ("merge_ask", "merge-ask"),
    ("lane_ticketing", "tickets"),
    ("lane_reporting", "spend"),
    ("lane_reflection", "intake"),
    ("lane_reporting", "report"),
    ("post_merge", "merge"),
    ("start_lane", "start"),
    ("lane_cli", "footer"),
)


def help_doc() -> str:
    """octo-feather-lane --help: each module's HELP chunks in HELP_ORDER, read from its source, never imported
    (the dispatcher loads only the module of the command it runs)."""
    here, chunks = Path(__file__).resolve().parent, dict[str, dict[str, str]]()
    for mod in dict.fromkeys(m for m, _ in HELP_ORDER):
        tree = ast.parse((here / f"{mod}.py").read_text(encoding="utf-8"))
        node = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "HELP" for t in n.targets))
        chunks[mod] = cast("dict[str, str]", ast.literal_eval(node.value))
    return "".join(chunks[m][c] for m, c in HELP_ORDER)


# This module's chunks of octo-feather-lane --help, joined in lane_cli.HELP_ORDER by lane_cli.help_doc.
HELP = {
    "header": """\
octo-feather-lane: lane bookkeeping in this Herdr session's state dir (spec comms #lane-record).

""",
    "footer": """\
One subcommand per function, listed in COMMANDS; add a subcommand there.
""",
}
