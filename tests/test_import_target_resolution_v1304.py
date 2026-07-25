"""Every in-repo dotted import must name a module that exists.

Coupling class 9, found by the v1304 symbol-rename pilot: in this repo a long
historical phrase is BOTH a symbol name and a script/module name (a script is
named after the function it wraps). An identifier-level rename therefore
rewrites dotted import paths too, pointing them at modules that do not exist.

That break is invisible to ruff and to mypy, and it does not surface until
something imports the module -- which, for a script imported only by one
test, can be much later. This test closes the gap for the whole repo.
"""
from __future__ import annotations

import ast
import unittest

from tests._bootstrap import ROOT

PACKAGE_DIRS = {
    "minigpt": ROOT / "src" / "minigpt",
    "scripts": ROOT / "scripts",
    "tests": ROOT / "tests",
}


def imported_modules(tree: ast.Module) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return modules


def resolves(dotted: str) -> bool:
    head, _, rest = dotted.partition(".")
    base = PACKAGE_DIRS.get(head)
    if base is None or not rest:
        return True                      # third-party or bare package import
    target = base.joinpath(*rest.split("."))
    return target.with_suffix(".py").is_file() \
        or (target / "__init__.py").is_file()


class ImportTargetResolutionTests(unittest.TestCase):
    def test_every_in_repo_import_names_an_existing_module(self) -> None:
        unresolved = []
        for sub in ("src", "scripts", "tests"):
            for path in sorted((ROOT / sub).rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for dotted in imported_modules(tree):
                    if not resolves(dotted):
                        unresolved.append(
                            f"{path.relative_to(ROOT)}: {dotted}")
        self.assertEqual([], unresolved)


if __name__ == "__main__":
    unittest.main()
