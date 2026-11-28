#!/usr/bin/env python3
"""The split of scripts/octo-feather-lane (ticket #1333; design: #1274 comment 7232729794). One-shot, kit-only: it
moves the kit's own command file, so it lives with the lane's evidence, not in scripts/.

  uv run --locked --offline python evidence/gh1274-split/split.py [--tree DIR] [--no-baselines] [--meta FILE]
      [--no-helpers | --helpers]

Run in the kit's root (or --tree DIR, a copy of the kit's files). It reads the hub, scripts/octo-feather-lane, and
writes: the dispatcher in its place, one module per command group (tables.py, CUT; a def the table lacks is placed by
`place` and printed), the moved code appended to post_merge.py, merge_ask.py and start_lane.py, the justfile's
install-check line, and (unless --no-baselines) the lint baselines relocated with the code: the ruff codes that fire
on each new module, the format exclude, basedpyright's baseline. Code moved into an existing module is formatted
(ruff format) and carries line noqa (ruff check --add-noqa) only. Prints every rewrite, one line each, and writes the
same table as JSON beside it (rewrites.json) for check.py.

Then (ticket #1335; --no-helpers: not) `helpers`: merge_ask.py's helpers that other command groups reach move to the
small shared modules of tables.py SHARED, which merge_ask.py imports; it prints the reached list and every rewrite, and
adds them to rewrites.json (key `helpers`). `--helpers` runs that step alone, on a tree already split.

Deterministic: the same hub gives the same files. A hub already split (it imports lane_cli) is refused.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import symtable
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tables as T  # noqa: E402

GROUP_MODULES = set(T.CUT) - {"lane_cli"}
DOCLINE = {
    "lane_cli": "the lane commands' shared parts: what two or more command groups use, the help's order "
                "(help_doc) and the live kit install's rule (kit_install).",
    "lane_ticketing": "octo-feather-lane's tickets, ticket, done, seam and skills.",
    "lane_reporting": "octo-feather-lane's report and spend.",
    "lane_review": "octo-feather-lane's verdict, fields, resolution and judge.",
    "lane_reflection": "octo-feather-lane's reflect and intake, and archive's reflection half.",
    "pi_sessions": "what a Pi session read: the session reader octo-feather-lane's skills and report share.",
    "ci_start": "octo-feather-lane's ci-start.",
}
BANNER = ("# --- moved from scripts/octo-feather-lane (ticket #1333, evidence/gh1274-split/split.py): {what}; help: "
          "octo-feather-lane --help ---")


class Refused(Exception):
    pass


def refuse(msg: str) -> None:
    raise Refused(msg)


# ---------------------------------------------------------------- reading the hub


class Item:
    """One top-level statement of the hub: its kind, names, and source lines (leading comments included)."""

    def __init__(self, node: ast.stmt, lines: list[str], start: int) -> None:
        self.node, self.start, self.end = node, start, node.end_lineno or node.lineno
        self.text = lines[start - 1:self.end]
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            self.kind, self.names = "def", [node.name]
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            self.kind, self.names = "import", [(a.asname or a.name).split(".")[0] for a in node.names]
        elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
            self.kind, self.names = "assign", [t.id for t in node.targets]  # type: ignore[attr-defined]
        else:
            self.kind, self.names = "other", []


def items_of(src: str) -> tuple[ast.Module, list[Item]]:
    tree, lines = ast.parse(src), src.splitlines()
    out, prev_end = [], 0
    for n in tree.body:
        first = min([n.lineno, *[d.lineno for d in getattr(n, "decorator_list", [])]])
        start = first
        for k in range(first - 1, prev_end, -1):   # comment lines in the gap before it go with it
            s = lines[k - 1].strip()
            if s.startswith("#"):
                start = k
            elif s:
                break
        out.append(Item(n, lines, start))
        prev_end = n.end_lineno or n.lineno
    return tree, out


def global_reads(src: str, node: ast.FunctionDef | ast.ClassDef, future: bool) -> set[str]:
    """Module-level names NODE reads: its body's (symtable), its decorators', defaults' and (without
    `from __future__ import annotations`) annotations'."""
    seg = ast.get_source_segment(src, node, padded=True) or ""
    sub = symtable.symtable(re_indent(seg), "<f>", "exec")
    out: set[str] = set()

    def walk(t: symtable.SymbolTable) -> None:
        for s in t.get_symbols():
            if s.is_referenced() and s.is_global():
                out.add(s.get_name())
        for c in t.get_children():
            walk(c)
    for c in sub.get_children():
        walk(c)
    outer: list[ast.AST] = list(getattr(node, "decorator_list", []))
    if isinstance(node, ast.FunctionDef):
        outer += [*node.args.defaults, *[d for d in node.args.kw_defaults if d]]
        if not future:
            outer += [a.annotation for a in [*node.args.args, *node.args.kwonlyargs] if a.annotation]
            outer += [node.returns] if node.returns else []
    else:
        outer += node.bases
    for o in outer:
        out |= {x.id for x in ast.walk(o) if isinstance(x, ast.Name)}
    return out


def re_indent(seg: str) -> str:
    lines = seg.splitlines()
    pad = len(lines[0]) - len(lines[0].lstrip())
    return "\n".join(l[pad:] for l in lines) + "\n"


def local_names(node: ast.AST) -> set[str]:
    """Every name NODE binds anywhere inside it (args, assignments, imports, nested defs)."""
    out: set[str] = set()
    for x in ast.walk(node):
        if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
            out.add(x.id)
        elif isinstance(x, ast.arg):
            out.add(x.arg)
        elif isinstance(x, (ast.Import, ast.ImportFrom)):
            out |= {(a.asname or a.name).split(".")[0] for a in x.names}
        elif isinstance(x, (ast.FunctionDef, ast.ClassDef)) and x is not node:
            out.add(x.name)
    return out


# ---------------------------------------------------------------- where each def and constant goes


def place(defs: dict[str, Item], reads: dict[str, set[str]], hub_modules: set[str]) -> tuple[dict[str, str], list[str]]:
    """Each def's module: the design's table, else the design's rule, printed: an entry and its helpers go where the
    group they serve is (the modules of the defs it reads and that read it, lane_cli aside); serving two or more,
    lane_cli when it reads no kit module, else the existing module whose kit code it reads (owner decision 1)."""
    where = {n: m for n, m in T.MODULE_OF.items() if n in defs}
    gone = sorted(set(T.MODULE_OF) - set(defs))
    notes = [f"design table names {', '.join(gone)}, which the hub no longer defines"] if gone else []
    todo = [n for n in defs if n not in where and n != "main"]
    for _ in range(len(todo) + 1):
        for n in list(todo):
            near = {where[m] for m in reads[n] if m in where} | {where[m] for m in defs if n in reads[m] and m in where}
            near -= {"lane_cli"}
            kit = reads[n] & hub_modules
            if len(near) == 1:
                where[n] = near.pop(); why = f"serves {where[n]}'s group only"
            elif len(near) > 1 and not kit:
                where[n] = "lane_cli"; why = f"serves {', '.join(sorted(near))}, reads no kit module"
            elif len(near) > 1 and len(kit & set(T.EXISTING)) == 1:
                where[n] = (kit & set(T.EXISTING)).pop()
                why = f"serves {', '.join(sorted(near))}; its logic is {where[n]}.py's (owner decision 1)"
            else:
                continue
            todo.remove(n)
            notes.append(f"placed by the rule: {n} -> {where[n]} ({why})")
    if todo:
        refuse(f"cannot place {', '.join(todo)} by the design's rule: add them to tables.py CUT")
    return where, notes


# ---------------------------------------------------------------- line edits


class Fn:
    """One moved def: its hub lines, the line edits made to them, and the names it reads."""

    def __init__(self, name: str, item: Item, module: str, origin: str = "octo-feather-lane") -> None:
        self.name, self.item, self.module, self.origin = name, item, module, origin
        self.lines = list(item.text)
        self.edits: list[dict[str, object]] = []   # {class, at (0-based hub line), old, new: [lines]}
        self.inserts: list[str] = []                # local import lines, after the docstring
        self.renames: dict[str, str] = {}           # new name -> the hub's key (check.py)

    def edit_line(self, at: int, new: str, cls: str) -> None:
        old = self.lines[at]
        if old != new:
            self.edits.append({"class": cls, "at": at, "old": old, "new": [new]})
            self.lines[at] = new


def spans(src_lines: list[str], node: ast.AST, base_line: int) -> tuple[int, int, int]:
    """(0-based line in the item, char start, char end) of a single-line NODE; columns from ast are utf-8 bytes."""
    if node.lineno != node.end_lineno:
        refuse(f"multi-line expression at hub line {node.lineno}")
    line = src_lines[node.lineno - 1].encode()
    a = len(line[:node.col_offset].decode()); b = len(line[:node.end_col_offset].decode())
    return node.lineno - base_line, a, b


def apply_spans(fn: Fn, changes: list[tuple[int, int, int, str, str]]) -> None:
    """CHANGES: (line in item, start, end, new text, class); right to left within a line."""
    by: dict[int, list[tuple[int, int, str, str]]] = {}
    for at, a, b, new, cls in changes:
        by.setdefault(at, []).append((a, b, new, cls))
    for at, cs in sorted(by.items()):
        line = fn.lines[at]
        for a, b, new, _ in sorted(cs, reverse=True):
            line = line[:a] + new + line[b:]
        fn.edit_line(at, line, "; ".join(sorted({c for *_, c in cs})))


# ---------------------------------------------------------------- the split


def split(root: Path, baselines: bool, meta_path: Path = HERE / "rewrites.json") -> list[str]:
    scripts = root / "scripts"
    hub_src = (scripts / "octo-feather-lane").read_text(encoding="utf-8")
    if re.search(r"^from lane_cli import|^import lane_cli", hub_src, re.M):
        refuse("scripts/octo-feather-lane is already the dispatcher (it imports lane_cli): run the split on the hub as "
               "main holds it before the split (git show <main before #1333>:scripts/octo-feather-lane)")
    tree, items = items_of(hub_src)
    hub_lines = hub_src.splitlines()
    doc = ast.get_docstring(tree, clean=False)
    if doc is None or not any(i.kind == "assign" and i.names == ["COMMANDS"] for i in items):
        refuse("scripts/octo-feather-lane has no docstring or no COMMANDS table: not the hub this split reads")
    existing_src = {m: (scripts / f"{m}.py").read_text(encoding="utf-8") for m in T.EXISTING}
    if any("# --- moved from scripts/octo-feather-lane" in s for s in existing_src.values()):
        refuse("post_merge.py, merge_ask.py or start_lane.py already holds moved code: the split runs once on main")

    defs = {i.names[0]: i for i in items if i.kind == "def"}
    consts = {n: i for i in items if i.kind == "assign" for n in i.names}
    imports = [i for i in items if i.kind == "import"]
    imported = {n: i for i in imports for n in i.names}
    hub_modules = {n for i in imports for a, n in zip(i.node.names, i.names, strict=True)  # type: ignore[attr-defined]
                   if isinstance(i.node, ast.Import)} - {"functools", "hashlib", "importlib", "json", "os", "re",
                                                         "shlex", "subprocess", "sys", "tempfile", "time",
                                                         "dataclasses", "dtm"}
    reads = {n: global_reads(hub_src, i.node, False) for n, i in defs.items()}  # type: ignore[arg-type]
    creads = {n: {x.id for x in ast.walk(i.node.value) if isinstance(x, ast.Name)} for n, i in consts.items()}  # type: ignore[attr-defined]
    where, notes = place(defs, reads, hub_modules)
    commands = consts.pop("COMMANDS")
    cmd_map = {k.value: v.id for k, v in zip(commands.node.value.keys, commands.node.value.values, strict=True)}  # type: ignore[attr-defined]
    table: list[str] = [f"note: {n}" for n in notes]

    # constants: their one user module, else lane_cli (reading stdlib and tracker_calls only), else each user's own
    users: dict[str, set[str]] = {n: set() for n in consts}
    for n, r in reads.items():
        for c in r & set(consts):
            users[c].add(where.get(n, "main"))
    for _ in range(3):
        for c, r in creads.items():
            for d in r & set(consts):
                users[d] |= users[c]
    users = {c: u - {"main"} for c, u in users.items()}
    cwhere: dict[str, list[str]] = {}
    for c, u in users.items():
        kit = creads[c] & (hub_modules - {"tracker_calls"})
        if not u:
            table.append(f"note: constant {c} has no reader: dropped")
            continue
        if len(u) == 1:
            cwhere[c] = sorted(u)
        elif not kit:
            cwhere[c] = ["lane_cli"]
            table.append(f"note: constant {c} read by {', '.join(sorted(u))}: lane_cli")
        else:
            cwhere[c] = sorted(u)
            table.append(f"note: binding {c} read by {', '.join(sorted(u))} reads {', '.join(sorted(kit))}: one per module")
    for c, ms in list(cwhere.items()):   # a lane_cli constant's own constants go there too
        if ms == ["lane_cli"]:
            for d in creads[c] & set(consts):
                if "lane_cli" not in cwhere[d]:
                    cwhere[d] = sorted({*cwhere[d], "lane_cli"})

    fns = {n: Fn(n, i, where[n]) for n, i in defs.items() if n != "main"}
    # kit_install moves out of post_merge.py (design section 1)
    pm_tree, pm_items = items_of(existing_src["post_merge"])
    moved_existing = {}
    for name, (src_mod, dst) in T.FROM_EXISTING.items():
        it = next(i for i in items_of(existing_src[src_mod])[1] if i.kind == "def" and i.names == [name])
        moved_existing[name] = (src_mod, it)
        fns[name] = Fn(name, it, dst, origin=f"{src_mod}.py")
        where[name] = dst

    # what each module defines already (existing modules) and how
    def top_bindings(src: str) -> dict[str, str]:
        out = {}
        for i in items_of(src)[1]:
            for n in i.names:
                out[n] = binding_key(i, n)
        return out

    def binding_key(i: Item, n: str) -> str:
        if isinstance(i.node, ast.ImportFrom):
            a = next(a for a in i.node.names if (a.asname or a.name) == n)
            return f"from {i.node.module} import {a.name}"
        if isinstance(i.node, ast.Import):
            a = next(a for a in i.node.names if (a.asname or a.name).split(".")[0] == n)
            return f"import {a.name.split('.')[0]}" + (f" as {a.asname}" if a.asname else "")
        if i.kind == "assign":
            return "= " + ast.unparse(i.node.value)  # type: ignore[attr-defined]
        return f"def {n}@{id(i)}"
    ex_bind = {m: top_bindings(s) for m, s in existing_src.items()}
    for name, (src_mod, _) in T.FROM_EXISTING.items():
        ex_bind[src_mod].pop(name)

    # ------------------------------------------------ per function rewrites
    need: dict[str, dict[str, set[str]]] = {m: {} for m in T.CUT}   # module -> provider -> names (top-level)
    aliases: dict[str, dict[str, str]] = {m: {} for m in T.CUT}      # module -> alias -> its definition line
    need["post_merge"].setdefault("lane_cli", set()).add("kit_install")   # post_merge.py's own callers of it
    need["lane_cli"].setdefault("import ast", set()).add("ast")   # help_doc's
    need["lane_cli"].setdefault("from typing", set()).add("cast")
    alias_lines: list[str] = []
    for i in imports:   # the hub's `import X as Y`: lane_cli binds Y = X, read from there (no ICN001, no F401)
        if isinstance(i.node, ast.Import):
            for a in i.node.names:
                if a.asname:
                    need["lane_cli"].setdefault(f"import {a.name}", set()).add(a.name)
                    alias_lines.append(f"{a.asname} = {a.name}   # the hub's `import {a.name} as {a.asname}`")
                    table.append(f"note: {a.asname}: lane_cli binds `{a.asname} = {a.name}` (the hub's import alias); "
                                 "each module reads it from there")
    # a binding over merge_ask's code is not made at the top of post_merge.py or start_lane.py (they never load
    # merge_ask at the top): merge_ask.py holds it, read where the call is
    lazy_mods = ("post_merge", "start_lane")
    for c, ms in cwhere.items():
        if "merge_ask" in creads[c] and set(ms) & set(lazy_mods):
            cwhere[c] = sorted((set(ms) - set(lazy_mods)) | {"merge_ask"})
            table.append(f"note: binding {c}: post_merge.py and start_lane.py read it from merge_ask.py where the call is")

    def held_as(c: str, m: str) -> str:
        """The name module M holds the hub's constant C under."""
        return prefixed(c) if m in T.EXISTING and c in ex_bind[m] and not same_binding(c, m) else c

    def same_binding(g: str, m: str) -> bool:
        if g not in ex_bind[m]:
            return False
        have = ex_bind[m][g]
        if g in consts:
            v = consts[g].node.value  # type: ignore[attr-defined]
            if isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name) and v.value.id == m and v.attr == g:
                return True   # `g = m.g` in the hub: m's own g
            return have == "= " + ast.unparse(v)
        if g in imported:
            prov, key = provider(g, m, where, cwhere, defs, consts, imported, consts_lines=hub_lines)
            return have == hub_binding_key(g, prov, key, imported, consts)
        return False

    def const_needs(c: str, m: str) -> None:
        for g in sorted(creads[c]):
            if g == m:
                continue
            if g in consts:
                if m not in cwhere.get(g, []):
                    need[m].setdefault("lane_cli", set()).add(g)
            elif g in defs:
                if where[g] != m:
                    need[m].setdefault(where[g], set()).add(g)
            elif g in imported:
                if m in T.EXISTING and g in ex_bind[m]:
                    continue
                prov, key = provider(g, m, where, cwhere, defs, consts, imported, consts_lines=hub_lines)
                if prov != m:
                    need[m].setdefault(prov, set()).add(key)

    for n, fn in fns.items():
        m, node = fn.module, fn.item.node
        src = hub_src if fn.origin == "octo-feather-lane" else existing_src[fn.origin[:-3]]
        src_lines = src.splitlines()
        r = reads[n] if fn.origin == "octo-feather-lane" else global_reads(src, node, True)  # type: ignore[arg-type]
        fn_locals = local_names(node)
        # design section 4.2: a moved function reading the hub's own identity outside the tables is refused, before
        # any file is written (a moved __file__, __doc__ or sys.argv names the new module or process, not the hub)
        if "__doc__" in r and n not in T.DOC_READERS:
            refuse(f"{n} reads __doc__ and is not in the table (tables.py DOC_READERS)")
        if any(isinstance(x, ast.Attribute) and x.attr == "argv" and isinstance(x.value, ast.Name)
               and x.value.id == "sys" for x in ast.walk(node)):
            refuse(f"{n} reads sys.argv and is not in the table")
        if "__file__" in r and n not in T.LAUNCH and n not in T.DIR_READERS:
            refuse(f"{n} reads __file__ and is not in the table (tables.py LAUNCH, DIR_READERS)")
        changes: list[tuple[int, int, int, str, str]] = []
        local_imports: dict[str, list[str]] = {}
        typed_local: list[str] = []

        def rename(g: str, new: str, cls: str) -> None:
            fn.renames[new] = g
            for x in ast.walk(node):
                if isinstance(x, ast.Name) and x.id == g:
                    at, a, b = spans(src_lines, x, fn.item.start)
                    changes.append((at, a, b, new, cls))

        # self-qualified names: M.X inside M
        if m in T.EXISTING and m in r:
            for x in ast.walk(node):
                if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == m:
                    at, a, b = spans(src_lines, x.value, fn.item.start)
                    if fn.lines[at][b:b + 1] != ".":
                        refuse(f"{n}: {m}.{x.attr} not written as {m}.X")
                    new = x.attr
                    if x.attr in fn_locals or x.attr not in ex_bind[m]:
                        new = f"{m}_{x.attr}"
                        aliases[m][new] = f"{new} = {x.attr}"
                    fn.renames[new] = f"{m}.{x.attr}"
                    changes.append((at, a, b + 1 + len(x.attr), new, "self-qualified"))
                elif (isinstance(x, ast.Constant) and isinstance(x.value, str) and f"{m}." in x.value
                      and re.fullmatch(r"[\w\[\], |.]+", x.value)):
                    at, a, b = spans(src_lines, x, fn.item.start)
                    changes.append((at, a, b, fn.lines[at][a:b].replace(f"{m}.", ""), "self-qualified"))
            r = r - {m}
        # the launch path
        if n in T.LAUNCH:
            hits = [x for x in ast.walk(node) if isinstance(x, ast.Call) and ast.unparse(x) == T.LAUNCH_FROM]
            if not hits:
                refuse(f"{n} is in the launch table but runs no {T.LAUNCH_FROM}")
            for x in hits:
                at, a, b = spans(src_lines, x, fn.item.start)
                changes.append((at, a, b, T.LAUNCH_TO, "launch path"))
        # the hub's docstring
        if n in T.DOC_READERS:
            for x in ast.walk(node):
                if isinstance(x, ast.Name) and x.id == "__doc__":
                    at, a, b = spans(src_lines, x, fn.item.start)
                    changes.append((at, a, b, "help_doc()", "the hub's own docstring"))
            r = r - {"__doc__"}
            need[m].setdefault("lane_cli", set()).add("help_doc")
        # every other global it reads
        for g in sorted(r - {"__file__", "__doc__"}):
            if g not in defs and g not in consts and g not in imported and g not in where:
                if not hasattr(__import__("builtins"), g):
                    refuse(f"{n} reads {g}, which the hub does not define")
                continue
            if g in consts and m in lazy_mods and m not in cwhere[g] and "merge_ask" in cwhere[g]:
                held = held_as(g, "merge_ask")
                local_imports.setdefault("merge_ask", []).append(g if held == g else f"{held} as {g}")
                continue
            prov, key = provider(g, m, where, cwhere, defs, consts, imported, consts_lines=hub_lines)
            if m in T.EXISTING and g in ex_bind[m] and not (g in where and where[g] == m):
                if same_binding(g, m):
                    continue
                new = prefixed(g)
                rename(g, new, "same name, another object")
                if prov == m:   # a hub constant this module holds under another name
                    aliases[m][new] = binding_line(consts[g], new, m)
                    const_needs(g, m)
                elif prov in GROUP_MODULES or (prov == "import merge_ask" and m in lazy_mods):
                    local_imports.setdefault(prov, []).append(f"{key} as {new}")
                else:
                    need[m].setdefault(prov, set()).add(f"{key.split(' as ')[0]} as {new}")
                continue
            if prov == m:
                continue
            if key in T.TYPED and (prov in GROUP_MODULES or prov == "lane_cli"):   # read typed (tables.py, TYPED)
                typed_line = f'{key} = cast("{T.TYPED[key]}", {prov}.{key})'
                need[m].setdefault("from typing", set()).update({"Any", "cast"})
                need[m].setdefault("from collections.abc", set()).add("Callable")
                if prov in GROUP_MODULES:
                    local_imports.setdefault(f"import {prov}", []).append(prov)
                    typed_local.append(typed_line)
                else:
                    need[m].setdefault(f"import {prov}", set()).add(prov)
                    aliases[m][key] = typed_line
                continue
            if prov in GROUP_MODULES or (prov == "import merge_ask" and m in lazy_mods):
                local_imports.setdefault(prov, []).append(key)
            else:
                need[m].setdefault(prov, set()).add(key)
        apply_spans(fn, changes)
        for prov, names in sorted(local_imports.items()):   # isort's form: plain names together, each alias alone
            if prov.startswith("import "):
                fn.inserts.append(f"import {prov.split()[-1]}")
                continue
            plain = sorted({x for x in names if " as " not in x})
            if plain:
                fn.inserts.append(f"from {prov} import {', '.join(plain)}")
            fn.inserts += [f"from {prov} import {x}" for x in sorted({x for x in names if " as " in x})]
        fn.inserts = sorted(fn.inserts, key=lambda l: (not l.startswith("import "), l)) + sorted(typed_local)
        if fn.inserts:
            insert_at(fn, node)
        if "__file__" in r and n not in T.LAUNCH:
            uses = {ast.unparse(p) for p in ast.walk(node) if isinstance(p, ast.Attribute)
                    and isinstance(p.value, ast.Call) and ast.unparse(p.value) == T.LAUNCH_FROM}
            if not uses or not uses <= {"Path(__file__).resolve().parent", "Path(__file__).resolve().with_name"}:
                refuse(f"{n} reads __file__ and is not in the table")
            table.append(f"note: {n} reads __file__ for its directory only ({', '.join(sorted(uses))}): "
                         f"{m}.py sits beside the hub, unchanged")

    # ------------------------------------------------ module texts
    help_chunks = chunks(doc, hub_src)
    out: dict[str, str] = {}
    order = [n for n in [*defs, *T.FROM_EXISTING] if n in fns]
    const_order = [c for c in consts if c in cwhere]
    for m in T.CUT:
        body: list[str] = []
        mine = [it for it in items if (it.kind == "def" and it.names[0] in fns and fns[it.names[0]].module == m)
                or (it.kind == "assign" and it.names[0] in cwhere and m in cwhere[it.names[0]])]
        if m == "lane_cli":
            body += [*alias_lines, "", "", *fn_text(fns["kit_install"]), "", ""]
        for it in mine:
            if it.kind == "def":
                body += [*fn_text(fns[it.names[0]]), "", ""]
                continue
            c = it.names[0]
            if m not in T.EXISTING:
                if body[-2:] == ["", ""] and body[-3:-2] and not body[-3].startswith((" ", ")", "}", "]")):
                    body = body[:-2]   # constants stay together, as in the hub
                body += [*it.text, "", ""]
            elif c in ex_bind[m]:
                if same_binding(c, m):
                    continue
                aliases[m][held_as(c, m)] = binding_line(it, held_as(c, m), m)
            else:
                body += [binding_line(it, c, m), "", ""]
            const_needs(c, m)

        chunks_m = [(name, text) for (_, mod, name), text in zip(T.HELP, help_chunks, strict=True) if mod == m]
        if m == "lane_cli":
            body += help_order_text()
        body += help_dict(chunks_m)
        if aliases[m]:
            body = [*(line for _, line in sorted(aliases[m].items())), "", "", *body]
        out[m] = assemble(m, body, need[m], imported)
    out["octo-feather-lane"] = dispatcher(cmd_map, fns)

    # ------------------------------------------------ write
    files = {}
    for m, text in out.items():
        p = scripts / (m if m == "octo-feather-lane" else f"{m}.py")
        if m in T.EXISTING:
            src = existing_src[m]
            for name, (src_mod, it) in moved_existing.items():
                if src_mod == m:
                    src = cut_def(src, it)
            if m == "post_merge":
                if src.count(T.PM_DOC_FROM) != 1:
                    refuse("post_merge.py's docstring line naming kit_install() is not there exactly once")
                src = src.replace(T.PM_DOC_FROM, T.PM_DOC_TO)
            text = insert_imports(src, IMPORTS[m]).rstrip("\n") + "\n\n\n" + text
        files[p] = text
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
        p.chmod(0o755)
        if p.name != "octo-feather-lane":
            isort_top(root, p)
    jf = root / "justfile"
    jt = jf.read_text(encoding="utf-8")
    if jt.count(T.JUSTFILE_FROM) != 1:
        refuse("justfile: the install-check line loading the lane script for kit_install is not there exactly once")
    jf.write_text(jt.replace(T.JUSTFILE_FROM, T.JUSTFILE_TO), encoding="utf-8")
    table.append("justfile install-check: kit_install read from scripts/lane_cli.py, not the lane script (one line)")
    for name, (src_mod, dst) in T.FROM_EXISTING.items():
        table.append(f"{dst}.py {name}: moved from {src_mod}.py unchanged (design section 1: lane_cli holds it)")
    table.append("post_merge.py docstring: its interface line says kit_install() is lane_cli.py's, imported there")

    # ------------------------------------------------ format and noqa the existing modules' moved code
    for m in T.EXISTING:
        p = str(scripts / f"{m}.py")
        run(["ruff", "format", "--quiet", p], root)
        run(["ruff", "check", "--quiet", "--add-noqa", p], root, ok=(0, 1))
        run(["ruff", "format", "--quiet", p], root)

    # ------------------------------------------------ the printed table
    rows = []
    for n in order:
        fn = fns[n]
        for e in fn.edits:
            rows.append({"function": n, "module": fn.module, **e})
        if fn.inserts:
            rows.append({"function": n, "module": fn.module, "class": "calls between groups", "at": -1, "old": "",
                         "new": fn.inserts, "after": fn.insert_after})  # type: ignore[attr-defined]
        if fn.module in T.EXISTING:
            rows.append({"function": n, "module": fn.module, "class": "formatted", "at": -1, "old": "", "new": []})
    for r in rows:
        if r["class"] == "formatted":
            table.append(f"{r['module']}.py {r['function']}: formatted (ruff format, line noqa; check 1 compares its ast)")
        elif r["at"] == -1:
            table.append(f"{r['module']}.py {r['function']}: {r['class']}: inserted `{'; '.join(r['new'])}`")
        else:
            table.append(f"{r['module']}.py {r['function']} line {int(r['at']) + 1}: {r['class']}: "
                         f"`{str(r['old']).strip()}` -> `{r['new'][0].strip()}`")
    meta = {"rows": rows, "where": {n: fn.module for n, fn in fns.items()},
            "origin": {n: fn.origin for n, fn in fns.items()},
            "renames": {n: fn.renames for n, fn in fns.items() if fn.renames},
            "inserts": {n: fn.inserts for n, fn in fns.items() if fn.inserts}, "table": table}
    meta_path.write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if baselines:   # the lint's file set is git's: the new modules known to git first (intent to add)
        run(["git", "add", "--intent-to-add", *[f"scripts/{m}.py" for m in T.NEW]], root)
        table += relocate_baselines(root)
    return table


def prefixed(g: str) -> str:
    """The name a moved function reads the hub's G under where its new module binds G otherwise."""
    return f"LANE_{g}" if g.isupper() else f"lane_{g}"


def provider(g: str, m: str, where: dict[str, str], cwhere: dict[str, list[str]], defs: dict[str, Item],
             consts: dict[str, Item], imported: dict[str, Item], consts_lines: list[str]) -> tuple[str, str]:
    """Where module M gets global G: (module or import statement, name)."""
    _ = consts_lines
    if g in defs or g in where:
        return where[g], g
    if g in consts:
        ms = cwhere[g]
        if m in ms:
            return m, g
        if ms == ["lane_cli"]:
            return "lane_cli", g
        refuse(f"constant {g} not available in {m}")
    if g in imported:
        i = imported[g]
        if isinstance(i.node, ast.ImportFrom):
            a = next(a for a in i.node.names if (a.asname or a.name) == g)
            if i.node.module == m:
                return m, g
            if i.node.module == "post_merge" and a.name == "kit_install":
                return "lane_cli", g
            return f"from {i.node.module}", a.name + (f" as {a.asname}" if a.asname else "")
        al = [a for a in i.node.names if (a.asname or a.name).split(".")[0] == g]  # type: ignore[attr-defined]
        if al[0].name == m:
            return m, g
        if al[0].asname and m != "lane_cli":   # one `import X as Y` (ICN001 in the hub), lane_cli's: Y read from there
            return "lane_cli", g
        return "import " + al[0].name.split(".")[0], ", ".join(a.name + (f" as {a.asname}" if a.asname else "") for a in al)
    if g in ("help_doc",):
        return "lane_cli", g
    refuse(f"{g}: no provider for module {m}")
    return "", ""


def hub_binding_key(g: str, prov: str, key: str, imported: dict[str, Item], consts: dict[str, Item]) -> str:
    if prov.startswith("from "):
        return f"{prov} import {key.split(' as ')[0]}"
    if prov.startswith("import "):
        return f"import {key}"
    if g in consts:
        return "= " + ast.unparse(consts[g].node.value)  # type: ignore[attr-defined]
    return f"from {prov} import {g}"


def binding_line(it: Item, name: str, m: str) -> str:
    """The hub's binding statement for module M: its self-qualified names unqualified, bound to NAME."""
    text = "\n".join(it.text)
    tree = ast.parse(text)
    stmt = tree.body[-1]
    value = ast.get_source_segment(text, stmt.value)  # type: ignore[attr-defined]
    value = re.sub(rf"\b{m}\.", "", value or "")
    return f"{name} = {value}"


def const_text(it: Item, m: str, c: str) -> list[str]:
    _ = m, c
    return list(it.text)


def fn_text(fn: Fn) -> list[str]:
    return fn.lines


def insert_at(fn: Fn, node: ast.AST) -> None:
    body = node.body  # type: ignore[attr-defined]
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        after = (first.end_lineno or first.lineno) - fn.item.start + 1
        anchor = body[1] if len(body) > 1 else first
    else:
        after = first.lineno - fn.item.start
        anchor = first
    indent = " " * anchor.col_offset
    for k, line in enumerate(fn.inserts):
        fn.lines.insert(after + k, indent + line)
    fn.insert_after = after  # type: ignore[attr-defined]


def cut_def(src: str, it: Item) -> str:
    lines = src.splitlines(keepends=True)
    a, b = it.start - 1, it.end
    while b < len(lines) and not lines[b].strip():
        b += 1
    return "".join(lines[:a] + lines[b:])


def chunks(doc: str, hub_src: str) -> list[str]:
    """The docstring cut at the HELP table's first lines, each chunk as source text (its escapes as written)."""
    tree = ast.parse(hub_src)
    node = tree.body[0].value  # type: ignore[attr-defined]
    seg = ast.get_source_segment(hub_src, node) or ""
    if not seg.startswith('"""') or not seg.endswith('"""'):
        refuse("the hub's docstring is not a plain triple-quoted string")
    body = seg[3:-3]
    lines = body.splitlines(keepends=True)
    starts = []
    for first, _, name in T.HELP:
        hits = [k for k, l in enumerate(lines) if l.startswith(first)]
        if len(hits) != 1:
            refuse(f"help chunk {name}: {len(hits)} lines start with {first!r}, not one")
        starts.append(hits[0])
    if starts != sorted(starts) or starts[0] != 0:
        refuse("help chunks out of order")
    out = ["".join(lines[a:b]) for a, b in zip(starts, [*starts[1:], len(lines)], strict=True)]
    for text in out:
        if ast.literal_eval('"""' + text + '"""') is None:
            refuse("chunk")
    if "".join(ast.literal_eval('"""' + t + '"""') for t in out) != doc:
        refuse("the help chunks do not join to the hub's docstring")
    return out


def help_dict(chunks_m: list[tuple[str, str]]) -> list[str]:
    if not chunks_m:
        return []
    out = ["# This module's chunks of octo-feather-lane --help, joined in lane_cli.HELP_ORDER by lane_cli.help_doc.",
           "HELP = {"]
    for name, text in chunks_m:
        if text.endswith('"') or '"""' in text:
            refuse(f"help chunk {name} cannot be written as a triple-quoted string")
        out.append(f'    "{name}": """\\')
        if not text.endswith("\n"):
            refuse(f"help chunk {name} does not end a line")
        out += text[:-1].split("\n")
        out.append('""",')
    out.append("}")
    return out


def help_order_text() -> list[str]:
    rows = ",\n".join(f'    ("{mod}", "{name}")' for _, mod, name in T.HELP)
    return [
        "# octo-feather-lane --help, in order: (module, chunk) for each chunk of a module's HELP.",
        f"HELP_ORDER = (\n{rows},\n)",
        "",
        "",
        "def help_doc() -> str:",
        '    """octo-feather-lane --help: each module\'s HELP chunks in HELP_ORDER, read from its source, never imported',
        '    (the dispatcher loads only the module of the command it runs)."""',
        "    here, chunks = Path(__file__).resolve().parent, dict[str, dict[str, str]]()",
        "    for mod in dict.fromkeys(m for m, _ in HELP_ORDER):",
        '        tree = ast.parse((here / f"{mod}.py").read_text(encoding="utf-8"))',
        "        node = next(n for n in tree.body if isinstance(n, ast.Assign)",
        '                    and any(isinstance(t, ast.Name) and t.id == "HELP" for t in n.targets))',
        "        chunks[mod] = cast(\"dict[str, str]\", ast.literal_eval(node.value))",
        '    return "".join(chunks[m][c] for m, c in HELP_ORDER)',
        "",
        "",
    ]


STDLIB_ORDER = ["functools", "hashlib", "importlib.machinery", "importlib.util", "json", "os", "re", "shlex",
                "subprocess", "sys", "tempfile", "time"]


def assemble(m: str, body: list[str], need: dict[str, set[str]], imported: dict[str, Item]) -> str:
    """Module M's text (a new module) or its appended section (an existing one: its imports go to its top, insert_imports)."""
    _ = imported
    imp: list[str] = []
    for p, ks in need.items():
        if p.startswith("import "):
            imp += [f"import {x}" for k in ks for x in k.split(", ")]
        elif p.startswith("from ") or p == "lane_cli":
            mod = p.removeprefix("from ")
            imp += [f"from {mod} import {k}" for k in ks]
        elif p in GROUP_MODULES and p != m:
            refuse(f"{m} needs {p} at top level: {ks}")
    if m == "lane_cli":
        imp = [x for x in imp if not x.startswith("from lane_cli ")]
    imp = sorted(set(imp))
    typing_only = []
    if m not in T.EXISTING and "from collections.abc import Callable" in imp:   # read in cast types only (TC003)
        imp.remove("from collections.abc import Callable")
        imp.append("from typing import TYPE_CHECKING")
        typing_only = ["", "if TYPE_CHECKING:", "    from collections.abc import Callable"]
    if m in T.EXISTING:
        IMPORTS[m] = imp
        return "\n".join([BANNER.format(what=DOCLINE.get(m, f"{m}'s commands")), "", "", *body]).rstrip() + "\n"
    head = ["#!/usr/bin/env python3", f'"""{m}: {DOCLINE[m]} Moved from scripts/octo-feather-lane, the dispatcher (ticket #1333)."""', ""]
    return "\n".join([*head, *imp, *typing_only, "", "", *body]).rstrip() + "\n"


IMPORTS: dict[str, list[str]] = {}


def insert_imports(src: str, imp: list[str]) -> str:
    """SRC with IMP after its last top-level import statement (ruff then sorts the block: I001)."""
    tree = ast.parse(src)
    last = max(n.end_lineno or n.lineno for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
               and n.col_offset == 0 and n.lineno < 400)
    lines = src.splitlines(keepends=True)
    return "".join(lines[:last] + [l + "\n" for l in imp] + lines[last:])


def isort_top(root: Path, path: Path) -> None:
    """PATH's top import block (and the blank lines after it) as ruff's own isort (I001) writes it; the rest of PATH,
    function-local imports included, as it was."""
    def end(text: str) -> int:
        tree, lines = ast.parse(text), text.splitlines(keepends=True)
        k = max(n.end_lineno or n.lineno for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
                and n.lineno < 400)
        while k < len(lines) and not lines[k].strip():
            k += 1
        return k
    orig = path.read_text(encoding="utf-8")
    import tomlkit   # the baseline table aside (a file whose baseline ignores I001 is sorted too: #1335 rewrites them)
    doc = tomlkit.parse((root / "pyproject.toml").read_text(encoding="utf-8"))
    doc["tool"]["ruff"]["lint"].pop("extend-per-file-ignores", None)  # type: ignore[union-attr,index]
    with tempfile.TemporaryDirectory() as t:
        cfg = Path(t) / "pyproject.toml"
        cfg.write_text(tomlkit.dumps(doc), encoding="utf-8")
        run(["ruff", "check", "--quiet", "--config", str(cfg), "--select", "I001", "--fix", str(path)], root, ok=(0, 1))
    fixed = path.read_text(encoding="utf-8")
    path.write_text("".join(fixed.splitlines(keepends=True)[:end(fixed)] + orig.splitlines(keepends=True)[end(orig):]),
                    encoding="utf-8")


DOCLINE.update({"post_merge": "merge, relay, post-merge, archive and stale", "merge_ask": "merge-ask",
                "start_lane": "start"})


def dispatcher(cmd_map: dict[str, str], fns: dict[str, Fn]) -> str:
    rows = "\n".join(f'    "{c}": ("{fns[f].module}", "{f}"),' for c, f in cmd_map.items())
    return f'''#!/usr/bin/env python3
"""octo-feather-lane: the lane commands (octo-feather-lane --help). This file only dispatches: each command's code and
help live in its module (COMMANDS), loaded when that command runs; the help is joined by lane_cli.help_doc."""

import importlib
import sys

# Kit modules, .py files beside this script, found through its own directory (symlinks resolved) on sys.path: from any
# cwd and through a symlink (scripts/correction_lanes.py docstring).
from lane_cli import Refuse, Unchecked, help_doc

COMMANDS = {{
{rows}
}}


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in COMMANDS:
        print(help_doc().strip(), file=sys.stderr); return 64
    module, function = COMMANDS[argv[0]]
    try:
        return getattr(importlib.import_module(module), function)(argv[1:])
    except Exception as e:
        pm = sys.modules.get("post_merge")   # post_merge's refusal, read only from a module already loaded
        if not isinstance(e, Refuse) and not (pm and isinstance(e, pm.Refused)):
            raise
        print(f"octo-feather-lane {{argv[0]}}: {{e}}", file=sys.stderr); return 2 if isinstance(e, Unchecked) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def run(cmd: list[str], cwd: Path, ok: tuple[int, ...] = (0,)) -> str:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if p.returncode not in ok:
        refuse(f"{' '.join(cmd)}: exit {p.returncode}: {p.stderr or p.stdout}")
    return p.stdout


# ---------------------------------------------------------------- baselines


SPLIT_FILES = ["scripts/octo-feather-lane", *[f"scripts/{m}.py" for m in T.CUT]]


def relocate_baselines(root: Path) -> list[str]:
    """The hub's ruff ignores, format exclude and basedpyright baseline, relocated to the files its code went to."""
    import tomlkit
    pp = root / "pyproject.toml"
    doc = tomlkit.parse(pp.read_text(encoding="utf-8"))
    ign = doc["tool"]["ruff"]["lint"]["extend-per-file-ignores"]  # type: ignore[index]
    fmt = doc["tool"]["ruff"]["format"]["exclude"]  # type: ignore[index]
    new_files = ["scripts/octo-feather-lane", *[f"scripts/{m}.py" for m in T.NEW]]
    # ruff: the codes that fire on each, with no baseline for them
    with tempfile.TemporaryDirectory() as t:   # a copy of pyproject.toml minus the table, as octo-feather-lint reads
        d2 = tomlkit.parse(pp.read_text(encoding="utf-8"))
        del d2["tool"]["ruff"]["lint"]["extend-per-file-ignores"]  # type: ignore[union-attr,index]
        cfg = Path(t) / "pyproject.toml"
        cfg.write_text(tomlkit.dumps(d2), encoding="utf-8")
        found = json.loads(run(["ruff", "check", "--config", str(cfg), "--output-format", "json", *new_files], root,
                               ok=(0, 1)) or "[]")
    codes: dict[str, set[str]] = {f: set() for f in new_files}
    for v in found:
        codes[os.path.relpath(v["filename"], root)].add(v["code"])
    for f in new_files:
        if codes[f]:
            arr = tomlkit.array()
            arr.multiline(True)
            for c in sorted(codes[f]):
                arr.append(c)
            ign[f] = arr
        elif f in ign:
            del ign[f]
    # format: the new files take the hub's exclude; the dispatcher's own text is formatted? keep it excluded only if
    # ruff format would change it
    unformatted = set()
    for f in new_files:
        if subprocess.run(["ruff", "format", "--check", "--quiet", f], cwd=root, check=False,
                          capture_output=True).returncode:
            unformatted.add(f)
    keep = [str(x) for x in fmt if str(x) not in new_files] + sorted(unformatted)
    fmt.clear()
    for x in sorted(keep, key=lambda s: (s.startswith("tests/"), s)) if False else keep_order(keep):
        fmt.append(x)
    fmt.multiline(True)
    pp.write_text(tomlkit.dumps(doc), encoding="utf-8")
    out = [f"baseline: ruff codes for {f}: {' '.join(sorted(codes[f])) or 'none'}" for f in new_files]
    out += [f"baseline: format exclude: {', '.join(sorted(unformatted))}"]
    # basedpyright: its baseline rewritten for the files the hub's code went to, through octo-feather-lint's mirror
    out += pyright_relocate(root)
    return out


def keep_order(keep: list[str]) -> list[str]:
    return sorted(keep)


def pyright_relocate(root: Path, files_moved: list[str] | None = None) -> list[str]:
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("octo_feather_lint", str(root / "scripts" / "octo-feather-lint"))
    spec = importlib.util.spec_from_loader("octo_feather_lint", loader)
    assert spec
    lint = importlib.util.module_from_spec(spec)
    cwd = os.getcwd()
    os.chdir(root)
    try:
        loader.exec_module(lint)
        files = lint.file_set()
        base = root / ".basedpyright" / "baseline.json"
        old = json.loads(base.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as t:
            copy = Path(t) / "baseline.json"
            copy.write_text(json.dumps({"files": {}}), encoding="utf-8")
            report = lint.pyright(files, copy, ["--writebaseline"])
            fresh = json.loads(copy.read_text(encoding="utf-8"))
    finally:
        os.chdir(cwd)
    _ = report
    keys = {f"./{f}" for f in (files_moved or SPLIT_FILES)}
    files_new = {k: v for k, v in old["files"].items() if k not in keys}
    for k in sorted(keys):
        if fresh["files"].get(k):
            files_new[k] = fresh["files"][k]
    others = {k: v for k, v in fresh["files"].items() if k not in keys}
    stray = sorted(k for k in others if others[k] != old["files"].get(k))
    if stray:
        refuse(f"basedpyright: errors outside the split files changed: {', '.join(stray)}")
    old["files"] = dict(sorted(files_new.items()))
    base.write_text(json.dumps(old, indent=4) + "\n", encoding="utf-8")
    return [f"baseline: basedpyright entries moved to {', '.join(sorted(k for k in keys if fresh['files'].get(k)))}"]


# ---------------------------------------------------------------- #1335: merge_ask.py's shared helpers


class Top:
    """One top-level statement of a module: its node, first line (the comment lines right above it, no blank line
    between, included), last line, the names it binds and its kind."""

    def __init__(self, node: ast.stmt, start: int) -> None:
        self.node, self.start, self.end = node, start, node.end_lineno or node.lineno
        self.header: tuple[int, int] | None = None   # a section comment above it, a blank line between (lines a..b)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            self.kind, self.names = "def", [node.name]
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            self.kind, self.names = "import", [(a.asname or a.name).split(".")[0] for a in node.names]
        elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
            self.kind, self.names = "assign", [t.id for t in node.targets]  # type: ignore[attr-defined]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            self.kind, self.names = "assign", [node.target.id]
        else:
            self.kind, self.names = "other", []


def tops(src: str) -> list[Top]:
    lines, out, prev = src.splitlines(), [], 0
    for n in ast.parse(src).body:
        first = min([n.lineno, *[d.lineno for d in getattr(n, "decorator_list", [])]])
        start = first
        while start - 1 > prev and lines[start - 2].strip().startswith("#"):
            start -= 1
        t = Top(n, start)
        k = start - 1   # a comment block in the gap above, blank lines around it: the section header
        while k > prev and not lines[k - 1].strip():
            k -= 1
        if k > prev and lines[k - 1].strip().startswith("#") and k < start - 1:
            a = k
            while a - 1 > prev and lines[a - 2].strip().startswith("#"):
                a -= 1
            t.header = (a, k)
        out.append(t)
        prev = t.end
    return out


def top_reads(src: str, t: Top, types: bool = True) -> set[str]:
    """The module-level names T reads: its code's (global_reads for a def), and those its type strings name (a cast's
    first argument, a quoted annotation), which the type checker resolves in the module."""
    if t.kind == "import":
        return set()
    if t.kind == "def":
        out = global_reads(src, t.node, False)  # type: ignore[arg-type]
        own = local_names(t.node)
    else:
        out, own = {x.id for x in ast.walk(t.node) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}, set()
    return out | (type_string_names(t.node) - own if types else set())


def type_string_names(node: ast.AST) -> set[str]:
    strs: list[ast.expr] = []
    for x in ast.walk(node):
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "cast" and x.args:
            strs.append(x.args[0])
        elif isinstance(x, (ast.arg, ast.AnnAssign)) and x.annotation is not None:
            strs.append(x.annotation)
        elif isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.returns is not None:
            strs.append(x.returns)
    out: set[str] = set()
    for s in strs:
        for c in ast.walk(s):
            if isinstance(c, ast.Constant) and isinstance(c.value, str):
                try:
                    out |= {n.id for n in ast.walk(ast.parse(c.value, mode="eval")) if isinstance(n, ast.Name)}
                except SyntaxError:
                    pass
    return out


def binding_stmt(t: Top, name: str) -> str:
    """The import statement binding NAME as merge_ask.py's top import T binds it."""
    n = t.node
    if isinstance(n, ast.ImportFrom):
        a = next(a for a in n.names if (a.asname or a.name) == name)
        return f"from {n.module} import {a.name}" + (f" as {a.asname}" if a.asname else "")
    a = next(a for a in n.names if (a.asname or a.name).split(".")[0] == name)  # type: ignore[attr-defined]
    return f"import {a.name}" + (f" as {a.asname}" if a.asname else "")


def merged_from(stmts: list[str]) -> list[str]:
    """`from M import a` lines joined per module (each alias alone, isort's form); `import` lines as they are."""
    plain: dict[str, set[str]] = {}
    out: set[str] = set()
    for s in stmts:
        m = re.fullmatch(r"from (\S+) import (\w+)", s)
        if m:
            plain.setdefault(m[1], set()).add(m[2])
        else:
            out.add(s)
    out |= {f"from {m} import {', '.join(sorted(ns, key=lambda x: (not x.isupper(), x)))}" for m, ns in plain.items()}
    return sorted(out)


def comment_span(line: str) -> int | None:
    """Where LINE's comment starts (tokenize), else None."""
    import io
    import tokenize
    try:
        for tok in tokenize.generate_tokens(io.StringIO(line.lstrip() + "\n").readline):
            if tok.type == tokenize.COMMENT:
                return len(line) - len(line.lstrip()) + tok.start[1]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return None


def helpers(root: Path, baselines: bool, meta_path: Path) -> list[str]:  # noqa: C901, PLR0912, PLR0915
    """Ticket #1335: merge_ask.py's helpers the command groups reach (tables.py HELPER_GROUPS) moved to the shared
    modules of tables.py SHARED, which merge_ask.py imports; every importer of a moved name reads it from its new
    module. Moved text is merge_ask.py's, unchanged. Prints the reached list and every rewrite."""
    scripts = root / "scripts"
    if any((scripts / f"{m}.py").exists() for m in T.SHARED):
        refuse(f"{', '.join(f'scripts/{m}.py' for m in T.SHARED)}: one exists already: the helpers move once")
    ma_path = scripts / "merge_ask.py"
    ma_src = ma_path.read_text(encoding="utf-8")
    ma_lines = ma_src.splitlines(keepends=True)
    items = tops(ma_src)
    bound: dict[str, Top] = {}
    for t in items:
        for n in t.names:
            bound.setdefault(n, t)
    reads = {id(t): top_reads(ma_src, t) for t in items}
    table: list[str] = []

    # what the groups read from merge_ask: `from merge_ask import X` anywhere in them, and `merge_ask.X`
    def from_ma(src: str) -> tuple[set[str], set[str]]:
        names, attrs = set(), set()
        for x in ast.walk(ast.parse(src)):
            if isinstance(x, ast.ImportFrom) and x.module == "merge_ask":
                names |= {a.name for a in x.names}
            elif isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "merge_ask":
                attrs.add(x.attr)
        return names, attrs
    roots: dict[str, set[str]] = {}
    for g in T.HELPER_GROUPS:
        a, b = from_ma((scripts / f"{g}.py").read_text(encoding="utf-8"))
        for n in a | b:
            roots.setdefault(n, set()).add(g)
    for n in sorted(roots):
        if n not in bound or bound[n].kind not in ("def", "assign"):
            refuse(f"{n}, which {', '.join(sorted(roots[n]))} read from merge_ask.py, is not a def or binding there")
        if n not in T.SHARED_OF:
            refuse(f"{n}, read from merge_ask.py by {', '.join(sorted(roots[n]))}: tables.py SHARED names no module "
                   "for it")
    # every merge_ask name the roots read, to the end; each with the modules of the roots reaching it
    reach: dict[str, set[str]] = {}
    for r in sorted(roots):
        seen, todo = set(), [r]
        while todo:
            n = todo.pop()
            if n in seen or n not in bound or bound[n].kind == "import":
                continue
            if bound[n].kind == "other":
                refuse(f"{n} is reached from {r} but bound by a statement the codemod does not move")
            seen.add(n)
            todo += sorted(reads[id(bound[n])])
        for n in seen:
            reach.setdefault(n, set()).add(T.SHARED_OF[r])
    where: dict[str, str] = {}
    for n, ms in sorted(reach.items()):
        if len(ms) > 1:
            refuse(f"{n} is reached from the roots of {', '.join(sorted(ms))}: tables.py SHARED must put it in one")
        where[n] = next(iter(ms))
    moved = [t for t in items if t.kind in ("def", "assign") and t.names[0] in where]
    for t in moved:
        if len({where[n] for n in t.names if n in where}) != 1 or any(n not in where for n in t.names):
            refuse(f"line {t.node.lineno}: binds {', '.join(t.names)}, not all reached")
        r = reads[id(t)]
        if r & {"__file__", "__doc__", "__name__", "__spec__"} or any(
                isinstance(x, ast.Attribute) and x.attr == "argv" and isinstance(x.value, ast.Name)
                and x.value.id == "sys" for x in ast.walk(t.node)):
            refuse(f"{t.names[0]} reads the module's own identity (__file__, __doc__, __name__ or sys.argv): moved, "
                   "it would read its new module's")
    table.append(f"reached: {len(where)} names, from {len(roots)} the groups read "
                 f"({', '.join(f'{g}: {len([n for n in roots if g in roots[n]])}' for g in T.HELPER_GROUPS)})")
    for m in T.SHARED:
        table.append(f"reached: {m}.py: " + " ".join(t.names[0] for t in moved if where[t.names[0]] == m))

    # names each module's code reads, and from where
    def needs_of(ts: list[Top], home: str) -> tuple[list[str], set[str]]:
        stmts, from_shared = [], set()
        for t in ts:
            for g in sorted(reads[id(t)]):
                if g in where:
                    if where[g] != home:
                        stmts.append(f"from {where[g]} import {g}")
                        from_shared.add(g)
                elif g in bound and bound[g].kind == "import":   # each statement binding it (import a.b, import a.c)
                    stmts += [binding_stmt(u, g) for u in items if u.kind == "import" and g in u.names]
                elif g in bound:
                    refuse(f"{t.names[0]} ({home}) reads {g}, which stays in merge_ask.py")
                elif not hasattr(__import__("builtins"), g):
                    refuse(f"{t.names[0]} reads {g}, which merge_ask.py does not bind")
        return stmts, from_shared
    deps = {m: {where[g] for g in needs_of([t for t in moved if where[t.names[0]] == m], m)[1]} for m in T.SHARED}
    for m, ds in deps.items():
        for d in ds:
            if m in deps[d]:
                refuse(f"{m}.py and {d}.py would import each other")

    # who imports moved names, besides the groups: every other module in scripts/ is rewritten; the tests are not,
    # so what they import from merge_ask must stay importable there
    kept_items = [t for t in items if t not in moved]
    core_reads = set().union(*(reads[id(t)] for t in kept_items if t.kind != "import"))
    all_names: set[str] = set()
    for t in kept_items:
        if t.kind == "assign" and t.names == ["__all__"]:
            all_names = set(ast.literal_eval(t.node.value))  # type: ignore[attr-defined]
    test_names: set[str] = set()
    for f in sorted((root / "tests").rglob("*.py")):
        a, b = from_ma(f.read_text(encoding="utf-8"))
        test_names |= (a | b) & set(where)
    if bad := sorted(test_names - core_reads - all_names - {"TREND"}):
        refuse(f"tests import {', '.join(bad)} from merge_ask.py, which would not hold them")
    ma_needs = sorted(set(where) & (core_reads | all_names | test_names))
    imported_from: dict[str, set[str]] = {m: set() for m in T.SHARED}   # each module's names others import
    for n in ma_needs:
        imported_from[where[n]].add(n)
    for m in T.SHARED:
        for d in deps[m]:
            imported_from[d] |= {g for g in needs_of([t for t in moved if where[t.names[0]] == m], m)[1]
                                 if where[g] == d}

    # ------------------------------------------------ the other modules' imports of moved names
    edits: dict[str, str] = {}
    pairs: dict[str, list[list[str]]] = {}   # file -> [old text, new text] of each rewrite (check.py)
    for f in sorted([*scripts.glob("*.py"), scripts / "octo-feather-lane"]):
        if f.name == "merge_ask.py" or f.stem in T.SHARED:
            continue
        src = f.read_text(encoding="utf-8")
        if "merge_ask" not in src:
            continue
        tree = ast.parse(src)
        lines = src.splitlines(keepends=True)
        line_edits: dict[int, tuple[int, int, str]] = {}   # first line -> (first, last, new text): whole statements
        spans_at: dict[int, list[tuple[int, int, str]]] = {}   # line -> (col a, col b, new) inside a line
        top_import = any(isinstance(n, ast.Import) and any(a.name == "merge_ask" for a in n.names) for n in tree.body)
        attrs = sorted({x.attr for x in ast.walk(tree) if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name)
                        and x.value.id == "merge_ask"})
        for x in ast.walk(tree):
            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "merge_ask" \
                    and x.attr in where:
                if not top_import:
                    refuse(f"{f.name}: merge_ask.{x.attr} through an import inside a function")
                at, a, b = x.value.lineno, x.value.col_offset, x.value.end_col_offset or 0
                if src.splitlines()[at - 1].encode()[:a].decode() != src.splitlines()[at - 1][:a]:
                    refuse(f"{f.name}:{at}: a non-ASCII line")
                spans_at.setdefault(at, []).append((a, b, where[x.attr]))
            if isinstance(x, ast.ImportFrom) and x.module == "merge_ask" and any(a.name in where for a in x.names):
                indent = " " * x.col_offset
                last = x.end_lineno or x.lineno
                cpos = comment_span(lines[last - 1].rstrip("\n"))
                tail = "  " + lines[last - 1].rstrip("\n")[cpos:] if cpos is not None and x.lineno == last else ""
                if cpos is not None and x.lineno != last:
                    refuse(f"{f.name}:{x.lineno}: a comment on a multi-line import")
                by: dict[str, list[str]] = {}
                for a in x.names:
                    by.setdefault(where.get(a.name, "merge_ask"), []).append(
                        a.name + (f" as {a.asname}" if a.asname else ""))
                new = merged_from([f"from {m} import {n}" for m, ns in by.items() for n in ns])
                line_edits[x.lineno] = (x.lineno, last, "".join(f"{indent}{s}{tail}\n" for s in new))
        if top_import:
            node = next(n for n in tree.body if isinstance(n, ast.Import) and any(a.name == "merge_ask" for a in n.names))
            if len(node.names) != 1:
                refuse(f"{f.name}: `import merge_ask` beside another module on one line")
            mods = sorted({where[a] for a in attrs if a in where})
            keep = ["merge_ask"] if any(a not in where for a in attrs) else []
            line_edits[node.lineno] = (node.lineno, node.lineno, "".join(f"import {m}\n" for m in [*keep, *mods]))
        if not line_edits and not spans_at:
            continue
        for at, cs in sorted(spans_at.items()):
            line = lines[at - 1].rstrip("\n")
            old = line
            cpos = comment_span(line)
            mods = sorted({m for *_, m in cs})
            if cpos is not None and len(mods) == 1:
                line = line[:cpos] + re.sub(r"\bmerge_ask(, Interface)?\b", mods[0], line[cpos:])
            for a, b, m in sorted(cs, reverse=True):
                line = line[:a] + m + line[b:]
            lines[at - 1] = line + "\n"
            table.append(f"{f.name}:{at}: `{old.strip()}` -> `{line.strip()}`")
            pairs.setdefault(f.name, []).append([old + "\n", line + "\n"])
        for first, (a, b, new) in sorted(line_edits.items(), reverse=True):
            old = "".join(lines[a - 1:b])
            lines[a - 1:b] = [new]
            table.append(f"{f.name}:{first}: `{' '.join(old.split())}` -> `{' | '.join(new.strip().splitlines())}`")
            pairs.setdefault(f.name, []).append([old, new])
        edits[f.name] = "".join(lines)

    # ------------------------------------------------ the shared modules
    out: dict[str, str] = {}
    for m, (doc, _) in T.SHARED.items():
        ts = [t for t in moved if where[t.names[0]] == m]
        stmts, _ = needs_of(ts, m)
        body: list[str] = []
        prev: Top | None = None
        for t in ts:
            k = items.index(t)
            sec = t.header
            whole = False
            if sec is not None:   # its section header goes along when the whole section does, to one module
                nxt = next((u for u in items[k + 1:] if u.header is not None), None)
                span = items[k:items.index(nxt)] if nxt else items[k:]
                whole = all(u in ts for u in span)
            if prev is not None and items.index(prev) == k - 1 and not (sec and whole):
                body += ["\n"] * (t.start - prev.end - 1 - (sec[1] - sec[0] + 1 if sec else 0))
            elif body:
                body += ["\n", "\n"]
            if sec is not None and whole:
                body += [*ma_lines[sec[0] - 1:sec[1]], *(["\n"] * (t.start - sec[1] - 1))]
                table.append(f"{m}.py: the section comment above {t.names[0]} goes along (its whole section does)")
            body += ma_lines[t.start - 1:t.end]
            prev = t
        if m == "gate_time":
            body = [T.TREND_LINE + "\n", "\n", "\n", *body]
        exports = sorted(imported_from[m] | ({"TREND"} if m == "gate_time" else set()))
        all_text = "__all__ = [  # what merge_ask.py and the lane's command groups import from here\n" + "".join(
            f'    "{n}",\n' for n in exports) + "]\n"
        import textwrap
        say = (f"{m}: {doc}. Moved from scripts/merge_ask.py, which imports them, for the lane's commands that use "
               "them (ticket #1335, evidence/gh1274-split/split.py helpers); standard library only (AGENTS.md Rules, "
               "kit scripts).")
        head = '#!/usr/bin/env python3\n"""' + "\n".join(textwrap.wrap(say, 97)) + '"""\n\n'
        runtime = set().union(*(top_reads(ma_src, t, types=False) for t in ts))
        typed = {s for s in stmts if ast.parse(s).body[0].names[0].asname not in runtime  # type: ignore[attr-defined]
                 and (ast.parse(s).body[0].names[0].asname or ast.parse(s).body[0].names[0].name).split(".")[0]  # type: ignore[attr-defined]
                 not in runtime}
        imports = merged_from([s for s in stmts if s not in typed])
        if typed:   # read in type strings only (ruff TC003): under TYPE_CHECKING, as the pilot's lane modules do
            imports = merged_from([*imports, "from typing import TYPE_CHECKING"])
            imports += ["", "if TYPE_CHECKING:", *(f"    {s}" for s in merged_from(sorted(typed)))]
            table.append(f"{m}.py: read in type strings only, imported under TYPE_CHECKING: {'; '.join(sorted(typed))}")
        out[m] = head + all_text + "\n" + "".join(f"{s}\n" for s in imports) + "\n\n" + "".join(body)
        table.append(f"{m}.py: {len(ts)} statements from merge_ask.py, text unchanged; imports: "
                     f"{'; '.join(merged_from(stmts))}; __all__: {', '.join(exports)}")

    # ------------------------------------------------ merge_ask.py: the moved statements cut, the shared ones imported
    cut: set[int] = set()
    for t in moved:
        a, b = t.start, t.end
        k = items.index(t)
        if t.header is not None:
            nxt = next((u for u in items[k + 1:] if u.header is not None), None)
            span = items[k:items.index(nxt)] if nxt else items[k:]
            if all(u in moved and where[u.names[0]] == where[t.names[0]] for u in span):
                a = t.header[0]
        while b < len(ma_lines) and not ma_lines[b].strip():
            b += 1
        cut |= set(range(a, b + 1))
    new_lines = [l for k, l in enumerate(ma_lines, 1) if k not in cut]
    text = "".join(new_lines)
    for old, new in [*T.MA_DOC_EDITS, *T.TREND_EDITS["merge_ask"]]:
        if text.count(old) != 1:
            refuse(f"merge_ask.py: {old.strip()[:60]!r} is not there exactly once")
        text = text.replace(old, new)
        table.append(f"merge_ask.py: `{' '.join(old.split())[:100]}` -> `{' '.join(new.split())[:100]}`")
        pairs.setdefault("merge_ask.py", []).append([old, new])
    # its top imports: each binding the code left no longer reads dropped; the shared names it needs added
    left = ast.parse(text)
    left_reads: set[str] = set()
    left_src = text
    for t in tops(left_src):
        if t.kind != "import":
            left_reads |= top_reads(left_src, t)
    imp_lines = text.splitlines(keepends=True)
    for n in reversed([n for n in left.body if isinstance(n, (ast.Import, ast.ImportFrom))]):
        names = [a for a in n.names if (a.asname or a.name).split(".")[0] in left_reads | all_names
                 or isinstance(n, ast.ImportFrom) and n.module == "__future__"]
        if len(names) == len(n.names):
            continue
        old = "".join(imp_lines[n.lineno - 1:n.end_lineno])
        if not names:
            new = ""
        elif isinstance(n, ast.ImportFrom):
            new = f"from {n.module} import " + ", ".join(a.name + (f" as {a.asname}" if a.asname else "")
                                                         for a in names) + "\n"
        else:
            new = "".join(f"import {a.name}" + (f" as {a.asname}" if a.asname else "") + "\n" for a in names)
        imp_lines[n.lineno - 1:n.end_lineno] = [new]
        pairs.setdefault("merge_ask.py", []).append([old, new])
        table.append(f"merge_ask.py:{n.lineno}: `{' '.join(old.split())}` -> `{' '.join(new.split()) or '(removed)'}`: "
                     "the code left no longer reads the rest")
    text = "".join(imp_lines)
    add = merged_from([f"from {where[n]} import {n}" for n in ma_needs] + ["from gate_time import TREND"])
    text = insert_imports(text, add)
    table.append(f"merge_ask.py: imports `{' | '.join(add)}`")
    out["merge_ask"] = text
    for old, new in T.TREND_EDITS["lane_reporting"]:
        src = edits["lane_reporting.py"]
        if src.count(old) != 1:
            refuse(f"lane_reporting.py: {old.strip()!r} is not there exactly once")
        edits["lane_reporting.py"] = src.replace(old, new)
        table.append(f"lane_reporting.py: `{old.strip()}` -> `{new.strip()}`")
        pairs.setdefault("lane_reporting.py", []).append([old, new])
    if not re.search(r"^import gate_time$", edits["lane_reporting.py"], re.M):
        refuse("lane_reporting.py does not import gate_time for ReportSources.TREND")

    # ------------------------------------------------ write, format, sort
    for m, text in out.items():
        p = scripts / f"{m}.py"
        p.write_text(text, encoding="utf-8")
        p.chmod(0o755)
    for name, text in edits.items():
        (scripts / name).write_text(text, encoding="utf-8")
    for m in out:   # merge_ask.py and the new modules keep ruff's format; the top import block sorted (I001)
        run(["ruff", "format", "--quiet", str(scripts / f"{m}.py")], root)
        if m in T.SHARED:   # __all__ in ruff's own order (RUF022, its safe fix)
            run(["ruff", "check", "--quiet", "--select", "RUF022", "--fix", str(scripts / f"{m}.py")], root, ok=(0, 1))
    for name in [*[f"{m}.py" for m in out], *edits]:
        isort_top(root, scripts / name)
    for m in T.SHARED:   # moved text unchanged by the format
        got = (scripts / f"{m}.py").read_text(encoding="utf-8")
        for t in moved:
            if where[t.names[0]] == m and "".join(ma_lines[t.start - 1:t.end]) not in got:
                refuse(f"{m}.py: ruff format changed {t.names[0]}'s text")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if "helpers" in meta:
        refuse(f"{meta_path}: the helpers' rows are there already")
    for n in list(meta["where"]):
        if meta["where"][n] == "merge_ask" and n in where:
            meta["where"][n] = where[n]
    meta["helpers"] = {"where": where, "roots": {n: sorted(g) for n, g in sorted(roots.items())},
                       "rewritten": sorted([*edits, "merge_ask.py"]), "lines": pairs, "table": table}
    meta_path.write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if baselines:
        run(["git", "add", "--intent-to-add", *[f"scripts/{m}.py" for m in T.SHARED]], root)
        keys = [f"scripts/{m}.py" for m in T.SHARED] + [f"scripts/{n}" for n in sorted([*edits, "merge_ask.py"])]
        table += pyright_relocate(root, keys)
    return table


def main() -> int:
    args = sys.argv[1:]
    root = Path.cwd()
    if "--tree" in args:
        root = Path(args[args.index("--tree") + 1]).resolve()
    try:
        meta = Path(args[args.index("--meta") + 1]) if "--meta" in args else HERE / "rewrites.json"
        baselines = "--no-baselines" not in args
        table = [] if "--helpers" in args else split(root, baselines, meta)
        if "--no-helpers" not in args:
            table += helpers(root, baselines, meta)
    except Refused as e:
        print(f"split: refused: {e}", file=sys.stderr)
        return 1
    print("\n".join(table))
    return 0


if __name__ == "__main__":
    sys.exit(main())
