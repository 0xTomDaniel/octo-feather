#!/usr/bin/env python3
"""check.py's names probe: every global each moved function reads, and what it resolves to, as a JSON descriptor.

  python probe.py base ROOT   the hub (and post_merge.py for kit_install) as ROOT/scripts holds them before the split
  python probe.py new ROOT    each function in the module the split put it in

Run with PYTHONHASHSEED=0 (a set constant's repr is then the same in both runs). Descriptors: a def the split moved is
("def", module the table puts it in, qualname), so the two runs agree only when a name reaches the moved def in its
new home; another function or class ("obj", module, qualname); a binding ("partial", func, args, keywords); a module
("module", name); a builtin; else ("const", repr) with ROOT written <ROOT>.
"""

from __future__ import annotations

import ast
import builtins
import functools
import hashlib
import importlib
import importlib.machinery
import importlib.util
import json
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tables as T  # noqa: E402
from split import global_reads  # noqa: E402  (the same reader the split placed by; symtable)

mode, root = sys.argv[1], Path(sys.argv[2]).resolve()
meta = json.loads((HERE / "rewrites.json").read_text(encoding="utf-8"))
WHERE: dict[str, str] = meta["where"]
sys.path.insert(0, str(root / "scripts"))
HUBMOD = "octo_feather_lane"


def load_hub() -> types.ModuleType:
    loader = importlib.machinery.SourceFileLoader(HUBMOD, str(root / "scripts" / "octo-feather-lane"))
    spec = importlib.util.spec_from_loader(HUBMOD, loader)
    assert spec
    mod = importlib.util.module_from_spec(spec)
    sys.modules[HUBMOD] = mod
    loader.exec_module(mod)
    return mod


def desc(obj: object, depth: int = 0) -> object:
    if depth > 4:
        return "..."
    if isinstance(obj, types.ModuleType):
        return ["module", obj.__name__]
    if isinstance(obj, functools.partial):
        return ["partial", desc(obj.func, depth + 1), [desc(a, depth + 1) for a in obj.args],
                sorted([k, desc(v, depth + 1)] for k, v in obj.keywords.items())]
    if hasattr(obj, "__wrapped__") and callable(obj):
        return ["wrapped", desc(obj.__wrapped__, depth + 1)]  # type: ignore[attr-defined]
    if isinstance(obj, (types.FunctionType, type)):
        mod, qual = obj.__module__, obj.__qualname__
        top = qual.split(".")[0]
        if mod == HUBMOD or (mod in T.EXISTING and top in T.FROM_EXISTING and mode == "base"):
            mod = WHERE.get(top, mod)
        cells = []
        if isinstance(obj, types.FunctionType) and obj.__closure__ and "<locals>" in qual:
            cells = [desc(c.cell_contents, depth + 1) for c in obj.__closure__]
        return ["def" if top in WHERE and mod == WHERE.get(top) else "obj", mod, qual, *cells]
    if isinstance(obj, (types.BuiltinFunctionType,)) and getattr(builtins, getattr(obj, "__name__", ""), None) is obj:
        return ["builtin", obj.__name__]
    return ["const", canon(obj).replace(str(root), "<ROOT>")]


def canon(obj: object) -> str:
    """repr, a set's members sorted (its iteration order is its insertion history, not its value)."""
    if isinstance(obj, (set, frozenset)):
        return f"{type(obj).__name__}({sorted(canon(x) for x in obj)})"
    if isinstance(obj, dict):
        return "{" + ", ".join(f"{canon(k)}: {canon(v)}" for k, v in obj.items()) + "}"
    if isinstance(obj, (tuple, list)):
        return f"{type(obj).__name__}({[canon(x) for x in obj]})"
    return repr(obj)


def refs(src: str, node: ast.FunctionDef | ast.ClassDef, future: bool) -> set[str]:
    return global_reads(src, node, future)


def node_of(src: str, name: str) -> ast.FunctionDef | ast.ClassDef:
    for n in ast.parse(src).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name:
            return n
    raise SystemExit(f"probe: no def {name}")


def resolve(mod: types.ModuleType, g: str) -> object:
    if g in vars(mod):
        return vars(mod)[g]
    if hasattr(builtins, g):
        return getattr(builtins, g)
    return ["unbound"]


out: dict[str, dict[str, object]] = {}
readers: list[str] = []
if mode == "base":
    hub = load_hub()
    hub_src = (root / "scripts" / "octo-feather-lane").read_text(encoding="utf-8")
    for fn, origin in meta["origin"].items():
        if origin == "octo-feather-lane":
            mod, src = hub, hub_src
        else:
            mod = importlib.import_module(origin[:-3])
            src = (root / "scripts" / origin).read_text(encoding="utf-8")
        node = node_of(src, fn)
        target = WHERE[fn]
        tsrc = (root / "scripts" / f"{target}.py")
        future = "from __future__ import annotations" in src or (
            tsrc.exists() and "from __future__ import annotations" in tsrc.read_text(encoding="utf-8"))
        r, d = refs(src, node, future), {}
        for g in sorted(r):
            val = resolve(mod, g)
            if g == target and isinstance(val, types.ModuleType):   # M.X read inside M: key M.X
                for x in ast.walk(node):
                    if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == g:
                        d[f"{g}.{x.attr}"] = desc(getattr(val, x.attr))
                continue
            if g == "__doc__":
                d[g] = ["const", hashlib.sha256(str(val).encode()).hexdigest()]
            elif g == "__file__":
                d[g] = ["dir", str(Path(str(val)).resolve().parent).replace(str(root), "<ROOT>")]
            else:
                d[g] = desc(val)
        uses_argv = any(isinstance(x, ast.Attribute) and x.attr == "argv" for x in ast.walk(node))
        if ("__file__" in r and fn not in T.LAUNCH) or ("__doc__" in r and fn not in T.DOC_READERS) or uses_argv:
            readers.append(fn)
        out[fn] = d
else:
    for fn, target in WHERE.items():
        mod = importlib.import_module(target)
        src = (root / "scripts" / f"{target}.py").read_text(encoding="utf-8")
        node = node_of(src, fn)
        future = "from __future__ import annotations" in src
        r, d = refs(src, node, future), {}
        renames: dict[str, str] = meta["renames"].get(fn, {})
        local: dict[str, object] = {}
        for line in meta["inserts"].get(fn, []):   # the imports the split inserted after the docstring
            stmt = ast.parse(line).body[0]
            if isinstance(stmt, ast.ImportFrom):
                m = importlib.import_module(stmt.module or "")
                for a in stmt.names:
                    local[a.asname or a.name] = getattr(m, a.name)
            elif isinstance(stmt, ast.Import):
                for a in stmt.names:
                    local[a.asname or a.name] = importlib.import_module(a.name)
            elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):   # NAME = cast(TYPE, M.NAME)
                at = stmt.value.args[1]
                assert isinstance(at, ast.Attribute) and isinstance(at.value, ast.Name)
                local[stmt.targets[0].id] = getattr(importlib.import_module(at.value.id), at.attr)  # type: ignore[attr-defined]
        vehicles = {ast.parse(l).body[0].value.args[1].value.id for l in meta["inserts"].get(fn, [])  # type: ignore[attr-defined]
                    if " = cast(" in l}
        names = r | (set(local) - vehicles)
        for g in sorted(names):
            if isinstance(node, ast.FunctionDef) and g not in local and g not in r:
                continue
            val = local[g] if g in local else resolve(mod, g)
            key = renames.get(g, g)
            if g == "help_doc":
                d["__doc__"] = ["const", hashlib.sha256(val().encode()).hexdigest()]
            elif g == "__file__":
                d[g] = ["dir", str(Path(str(val)).resolve().parent).replace(str(root), "<ROOT>")]
            else:
                d[key] = desc(val)
        out[fn] = d
print(json.dumps({"names": out, "readers": readers}, sort_keys=True))
