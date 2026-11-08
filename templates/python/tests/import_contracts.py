"""The import contract that keeps shared test support in one place (#684; owner ruling #577:
shared stand-ins and helpers live in the testkit, the tdd skill's mocking.md, Test support).

Contract type `sibling_imports`, an import-linter custom contract type (its documented extension
point; registered in pyproject.toml [tool.importlinter] contract_types, run by `lint-imports`).
Fields: `containers`, the test trees it checks (module names under a root package), and
`shared_modules`, the import names of the declared shared location (optional). Each module in a
container that imports a module beside it (a file or package in its own directory) breaks it,
named with its file, line and the module, unless that module is one of `shared_modules` or the
importer is test_X importing X (a kit test's scenario). Modules inside a shared package import
freely. Files are named relative to the working directory, where lint-imports finds the root.

Why a custom type: pytest puts a flat test directory (no __init__.py) itself on sys.path, so a
test's `from b_helpers import x` is an absolute import of a top-level module. import-linter's
built-in types (forbidden, protected, layers, independence, acyclic_siblings) cannot name it:
under the directory's namespace root grimp records it only as an external top-level `b_helpers`,
indistinguishable by name from the standard library's, and a single file as its own root is
refused (grimp NotATopLevelModule). This type matches that external name against the modules
grimp found beside the importer. Kit and templates alike: templates/python carries its own copy,
tests/import_contracts.py, because a template ships standalone; the two stay identical.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

from importlinter import Contract, ContractCheck, fields, output

if TYPE_CHECKING:
    import grimp


def _file(module: str) -> str:
    base = module.replace(".", "/")
    return f"{base}.py" if Path(f"{base}.py").is_file() else f"{base}/__init__.py"


def _names(contract: Contract, field: str) -> list[str]:
    """FIELD's parsed value (import-linter sets it on the instance; absent: none)."""
    return cast("list[str] | None", getattr(contract, field)) or []


class SiblingImportsContract(Contract):
    type_name = "sibling_imports"

    containers = fields.ListField(subfield=fields.StringField())
    shared_modules = fields.ListField(subfield=fields.StringField(), required=False)

    def check(self, graph: grimp.ImportGraph, verbose: bool) -> ContractCheck:  # noqa: ARG002, FBT001
        roots = _names(self, "containers")
        shared = set(_names(self, "shared_modules"))
        broken: list[str] = []
        for importer in sorted(graph.modules):
            root = next((r for r in roots if importer.startswith(f"{r}.")), None)
            if root is None or shared & set(importer[len(root) + 1 :].split(".")[:-1]):
                continue
            parent, _, leaf = importer.rpartition(".")
            for imported in sorted(graph.find_modules_directly_imported_by(importer)):
                if imported.startswith(f"{parent}."):
                    name = imported[len(parent) + 1 :].split(".")[0]
                elif graph.is_module_squashed(imported) and f"{parent}.{imported}" in graph.modules:
                    name = imported
                else:
                    continue
                if name in shared or leaf == f"test_{name}":
                    continue
                broken.extend(
                    f"{_file(importer)}:{d['line_number']} imports {name}, a module beside it "
                    f"({_file(f'{parent}.{name}')}): {d['line_contents']}"
                    for d in graph.get_import_details(importer=importer, imported=imported)
                )
        return ContractCheck(kept=not broken, metadata={"broken": broken})

    def render_broken_contract(self, check: ContractCheck) -> None:
        for line in check.metadata["broken"]:
            output.print_error(line, bold=False)
        where = ", ".join(sorted(_names(self, "shared_modules"))) or "the declared shared location"
        output.print(f"Shared test support lives in one place ({where}): move it there.")
