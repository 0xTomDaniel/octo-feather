#!/usr/bin/env python3
"""Tracked language classification and executable declarations, kit stdlib only."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast


class ToolRequired(TypedDict):
    program: str
    argv: list[str]
    recipe: str
    install: str


class Tool(ToolRequired, total=False):
    adapter: str


class Language(TypedDict):
    extensions: list[str]
    shebangs: list[str]
    tools: list[str]


class Exemption(TypedDict):
    path: str
    reason: str


class Declaration(TypedDict):
    languages: dict[str, Language]
    tools: dict[str, Tool]
    exemptions: list[Exemption]
    noncode_extensions: list[str]
    noncode_paths: list[str]
    executable_roots: list[str]


class Recipe(TypedDict):
    body: list[list[str]]
    dependencies: list[dict[str, object]]


class Assignment(TypedDict):
    value: object


class Dump(TypedDict):
    recipes: dict[str, Recipe]
    assignments: dict[str, Assignment]


class DeclarationError(ValueError):
    """The declaration cannot guarantee the claimed execution."""


# The argv prefixes a declared tool may run its program through (complete argv, nothing else).
LAUNCHERS = (
    ["pnpm", "exec"],
    ["uv", "run", "--locked", "--offline", "--no-sync"],
)


def read_declaration(path: Path) -> Declaration:
    return cast("Declaration", json.loads(path.read_text()))


def executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        message = f"{name}: missing executable; install it before running the gate"
        raise DeclarationError(message)
    return path


def interpreter(first: bytes) -> str:
    if not first.startswith(b"#!"):
        return ""
    words = shlex.split(first[2:].decode("utf-8", "replace"))
    if words and Path(words[0]).name == "env":
        words = words[1:]
        while words:
            if words[0] in {"-u", "--unset", "-C", "--chdir"}:
                words = words[2:]
            elif words[0].startswith("-") or "=" in words[0]:
                words = words[1:]
            else:
                break
    if not words:
        return ""
    program = Path(words[0]).name
    if re.fullmatch(r"(python|pypy)[0-9.]*", program):
        return "python"
    if program == "uv" and words[1:2] == ["run"] and "--script" in words[2:]:
        return "python"
    return program


def classify(root: Path, declaration: Declaration) -> dict[str, list[str]]:
    names = (
        subprocess.check_output([executable("git"), "ls-files", "-z"], cwd=root)
        .decode()
        .split("\0")
    )
    result: dict[str, list[str]] = {language: [] for language in declaration["languages"]}
    for name in filter(None, names):
        path = Path(name)
        if any(
            name == item["path"] or name.startswith(item["path"].rstrip("/") + "/")
            for item in declaration["exemptions"]
            if item["reason"].strip()
        ):
            continue
        first = (root / path).read_bytes().split(b"\n", 1)[0]
        shebang = interpreter(first)
        matches = [
            language
            for language, entry in declaration["languages"].items()
            if path.suffix in entry["extensions"] or shebang in entry["shebangs"]
        ]
        if len(matches) == 1:
            result[matches[0]].append(name)
        elif matches:
            msg = f"{name}: ambiguous language; fix declaration"
            raise DeclarationError(msg)
        elif (
            path.suffix not in declaration["noncode_extensions"]
            and name not in declaration["noncode_paths"]
        ):
            msg = f"{name}: unknown type; declare its language or reasoned exemption"
            raise DeclarationError(msg)
    return result


def gate_dump(root: Path) -> Dump:
    return cast(
        "Dump",
        json.loads(
            subprocess.check_output(
                [executable("just"), "--dump", "--dump-format", "json"], cwd=root
            )
        ),
    )


def validate_bindings(root: Path, declaration: Declaration) -> None:
    dump = gate_dump(root)
    recipes = dump["recipes"]
    tools = declaration["tools"]
    required = {tool for entry in declaration["languages"].values() for tool in entry["tools"]}
    for key in required:
        if key not in tools:
            msg = f"{key}: missing tool; restore its executable declaration"
            raise DeclarationError(msg)
    names = {tool["recipe"] for tool in tools.values()}
    for name in names | {"check-tests"}:
        command = 'gate "$@"' if name == "check-tests" else f"run {name}"
        expected = [[f"@python3 scripts/check-languages {command}"]]
        recipe = recipes.get(name)
        if recipe is None or recipe["body"] != expected or recipe["dependencies"]:
            msg = f"{name}: altered binding; use the complete invocation {expected[0][0]}"
            raise DeclarationError(msg)
    if "check" not in recipes or recipes["check"]["dependencies"] != [
        {"arguments": [], "recipe": "check-tests"}
    ]:
        msg = "check: restore the check-tests dependency"
        raise DeclarationError(msg)
    gate = dump["assignments"]["GATE_RECIPES"]["value"]
    if not isinstance(gate, str):
        msg = "GATE_RECIPES: use a literal recipe list"
        raise DeclarationError(msg)
    for key, tool in tools.items():
        if tool["recipe"] not in gate.split():
            msg = f"{key}: bind {tool['recipe']} in the reachable gate"
            raise DeclarationError(msg)
        argv = tool["argv"]
        empty: list[str] = []
        launcher = next((item for item in LAUNCHERS if argv[: len(item)] == item), empty)
        prefix = [*launcher, tool["program"]]
        if not argv or argv[: len(prefix)] != prefix or not all(argv):
            msg = f"{key}: argv must execute declared program {tool['program']}"
            raise DeclarationError(msg)


def tool_argv(program: str) -> list[str]:
    """Native baseline adapters obtain their actual executable prefix here."""
    declaration = read_declaration(Path("languages.json"))
    prefixes = [
        tool["argv"] for tool in declaration["tools"].values() if tool["program"] == program
    ]
    if not prefixes or any(prefix != prefixes[0] for prefix in prefixes):
        msg = f"{program}: restore one consistent declared argv"
        raise DeclarationError(msg)
    return prefixes[0]


def require_executables(root: Path, declaration: Declaration, files: dict[str, list[str]]) -> None:
    for paths in files.values():
        for name in paths:
            if str(Path(name).parent) in declaration.get("executable_roots", []) and not os.access(
                root / name, os.X_OK
            ):
                msg = f"not executable: {name}; chmod +x {name}"
                raise DeclarationError(msg)


def prepare_typescript(root: Path) -> int:
    result = subprocess.run(
        [executable("pnpm"), "install", "--offline", "--frozen-lockfile"], cwd=root, check=False
    )
    if result.returncode:
        sys.stderr.write(
            "check-ts: fetch them once, with network: "
            f"pnpm install --frozen-lockfile --dir {root}\n"
        )
    return result.returncode


def compile_python(root: Path, tool: Tool, files: list[str]) -> int:
    with tempfile.TemporaryDirectory() as folder:
        return subprocess.run(
            [*tool["argv"], *files],
            cwd=root,
            env=dict(os.environ, PYTHONPYCACHEPREFIX=folder),
            check=False,
        ).returncode


def typescript(root: Path, tool: Tool, files: list[str]) -> int:
    with tempfile.TemporaryDirectory(dir=root) as folder:
        config = Path(folder) / "tsconfig.json"
        config.write_text(
            json.dumps(
                {
                    "extends": str(root / "tsconfig.json"),
                    "files": [str(root / path) for path in files],
                    "include": [],
                    "exclude": [],
                    "compilerOptions": {"typeRoots": [str(root / "node_modules/@types")]},
                }
            )
        )
        result = subprocess.run([*tool["argv"], "--project", str(config)], cwd=root, check=False)
    if result.returncode:
        sys.stderr.write("check-ts: fix each tsc error above at its file(line,col)\n")
    return result.returncode


def mirror(path: str) -> str:
    """A repo path with each dot-leading component `.x` written `_.x`."""
    return "/".join(f"_{c}" if c.startswith(".") else c for c in path.split("/"))


def pyright_report(
    root: Path, argv: list[str], files: list[str], options: list[str]
) -> dict[str, object]:
    """basedpyright (argv) over exactly the files, through a throwaway mirror of links whose
    project root holds the repo's pyproject.toml linked in: basedpyright drops a file under a dot
    directory (.agents/) even when named, so `.x` reads `_.x` there. Diagnostics come back with
    repo paths; fewer files analyzed than named is an error."""
    with tempfile.TemporaryDirectory() as folder:
        mirrored = Path(folder).resolve()
        config = mirrored / "pyproject.toml"
        config.symlink_to((root / "pyproject.toml").resolve())
        back: dict[str, str] = {}
        for name in files:
            link = mirrored / mirror(name)
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to((root / name).resolve())
            back[str(link)] = name
        command = [*argv, "--outputjson", "-p", str(config), *options, *back]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    # --writebaseline prints its summary line before the JSON report.
    start = result.stdout.find("{\n")
    try:
        report = cast("dict[str, object]", json.loads(result.stdout[max(start, 0) :]))
    except json.JSONDecodeError as error:
        msg = (
            f"basedpyright gave no JSON (exit {result.returncode}): {result.stdout} {result.stderr}"
        ).strip()
        raise DeclarationError(msg) from error
    summary = cast("dict[str, int]", report.get("summary") or {})
    if summary.get("filesAnalyzed") != len(files):
        analyzed = summary.get("filesAnalyzed")
        msg = f"basedpyright analyzed {analyzed} files, not the {len(files)} named"
        raise DeclarationError(msg)
    for item in cast("list[dict[str, object]]", report.get("generalDiagnostics") or []):
        item["file"] = back.get(str(item.get("file")), str(item.get("file")))
    return report


def pyright(root: Path, tool: Tool, files: list[str]) -> int:
    report = pyright_report(root, tool["argv"], files, [])
    bad = 0
    for item in cast("list[dict[str, object]]", report.get("generalDiagnostics") or []):
        if item.get("severity") not in {"error", "warning"}:
            continue
        start = cast("dict[str, dict[str, int]]", item.get("range") or {}).get("start", {})
        sys.stdout.write(
            f"{item['file']}:{start.get('line', 0) + 1}: {item.get('rule')} {item.get('message')}\n"
        )
        bad = 1
    if bad:
        sys.stderr.write("check-types: change the code so basedpyright accepts each line above\n")
    else:
        sys.stdout.write(f"types: ok (basedpyright analyzed {len(files)} files)\n")
    return bad


def execute_tool(root: Path, tool: Tool, files: list[str]) -> int:
    adapter = tool.get("adapter", "direct")
    if adapter in ("lint", "format", "types"):
        # Native baseline owner obtains executable argv through tool_argv.
        command = [
            executable("uv"),
            "run",
            "--locked",
            "--offline",
            "--no-sync",
            "octo-feather-lint",
            adapter,
        ]
    elif not files:
        return 0
    elif adapter == "compile":
        return compile_python(root, tool, files)
    elif adapter == "tsc":
        return typescript(root, tool, files)
    elif adapter == "pyright":
        return pyright(root, tool, files)
    elif adapter == "direct":
        command = [*tool["argv"], *files]
    else:
        msg = f"{tool['program']}: unknown native adapter {adapter}"
        raise DeclarationError(msg)
    result = subprocess.run(command, cwd=root, check=False)
    if result.returncode and tool["program"] == "eslint":
        sys.stderr.write(
            "check-ts: fix each eslint finding; stale suppressions: "
            "pnpm exec eslint --prune-suppressions\n"
        )
    return result.returncode


def execute(root: Path, declaration: Declaration, recipe: str) -> int:
    validate_bindings(root, declaration)
    classified = classify(root, declaration)
    selected = [
        (key, tool) for key, tool in declaration["tools"].items() if tool["recipe"] == recipe
    ]
    if not selected:
        msg = f"{recipe}: no declared tools; restore its binding"
        raise DeclarationError(msg)
    if recipe == "check-scripts":
        require_executables(root, declaration, classified)
    if any(tool["program"] == "tsc" for _, tool in selected):
        status = prepare_typescript(root)
        if status:
            return status
    bad = 0
    for key, tool in selected:
        files = sorted(
            {
                path
                for language, entry in declaration["languages"].items()
                if key in entry["tools"]
                for path in classified[language]
            }
        )
        try:
            status = execute_tool(root, tool, files)
        except OSError as error:
            msg = f"{key}: {error}; {tool['install']}"
            raise DeclarationError(msg) from error
        bad = bad or status
    if recipe == "check-ts" and not bad:
        sys.stdout.write("ts: ok (classified tracked TypeScript and JavaScript: tsc, eslint)\n")
    return bad
