from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

SRC = ROOT / "src" / "minigpt"

EXPECTED_OWNER_PACKAGE_NAMES = (
    "core",
    "training",
    "evaluation",
    "serving",
    "reports",
    "governance",
)

CORE_FLAT_MODULES = [
    SRC / "model.py",
    SRC / "tokenizer.py",
    SRC / "dataset.py",
    SRC / "history.py",
    SRC / "rope.py",
]

OWNER_PACKAGES = {
    "core": SRC / "core",
    "training": SRC / "training",
    "evaluation": SRC / "evaluation",
    "serving": SRC / "serving",
    "reports": SRC / "reports",
    "governance": SRC / "governance",
}

OUTER_GOVERNANCE_PREFIXES = (
    "minigpt.governance",
    "minigpt.release",
    "minigpt.registry",
    "minigpt.maturity",
    "minigpt.maintenance",
    "minigpt.randomized_holdout",
    "minigpt.model_capability",
    "minigpt.bounded_objective",
    "minigpt.baseline_candidate",
)

CORE_PROHIBITED_PREFIXES = OUTER_GOVERNANCE_PREFIXES + (
    "minigpt.training",
    "minigpt.evaluation",
    "minigpt.serving",
    "minigpt.server",
    "minigpt.reports",
    "minigpt.dashboard",
    "minigpt.manifest",
    "minigpt.artifact_map",
)

OWNER_PROHIBITED_PREFIXES = {
    "core": CORE_PROHIBITED_PREFIXES,
    "training": OUTER_GOVERNANCE_PREFIXES + ("minigpt.serving", "minigpt.server"),
    "evaluation": OUTER_GOVERNANCE_PREFIXES + ("minigpt.serving", "minigpt.server"),
    "serving": OUTER_GOVERNANCE_PREFIXES,
    "reports": OUTER_GOVERNANCE_PREFIXES,
    "governance": (
        "minigpt.core",
        "minigpt.training",
        "minigpt.evaluation",
        "minigpt.serving",
        "minigpt.server",
    ),
}

TRANSITIONAL_PACKAGE_DIRS = [
    SRC / name for name in EXPECTED_OWNER_PACKAGE_NAMES
]


def imports_for(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.append(node.module)
    return imports


def matching_prefix(module: str, prefixes: tuple[str, ...]) -> str | None:
    return next((prefix for prefix in prefixes if module.startswith(prefix)), None)


def package_files(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_owner_package_inventory_matches_current_directories(self) -> None:
        actual = tuple(
            sorted(
                path.name
                for path in SRC.iterdir()
                if path.is_dir() and (path / "__init__.py").is_file()
            )
        )

        self.assertEqual(tuple(sorted(EXPECTED_OWNER_PACKAGE_NAMES)), actual)
        self.assertEqual(tuple(directory.name for directory in TRANSITIONAL_PACKAGE_DIRS), EXPECTED_OWNER_PACKAGE_NAMES)

    def test_module_inventory_documents_current_owner_packages(self) -> None:
        text = (ROOT / "docs" / "module-inventory.md").read_text(encoding="utf-8")

        self.assertIn("## Normalized Owner Packages", text)
        for name in EXPECTED_OWNER_PACKAGE_NAMES:
            with self.subTest(name=name):
                self.assertIn(f"`minigpt.{name}`", text)

    def test_core_flat_modules_do_not_import_outer_layers(self) -> None:
        violations = []
        for path in CORE_FLAT_MODULES:
            for module in imports_for(path):
                prefix = matching_prefix(module, CORE_PROHIBITED_PREFIXES)
                if prefix is not None:
                    violations.append(f"{path.relative_to(ROOT)} imports {module} via {prefix}")

        self.assertEqual([], violations)

    def test_owner_packages_do_not_import_forbidden_layers(self) -> None:
        violations = []
        for owner, directory in OWNER_PACKAGES.items():
            for path in package_files(directory):
                for module in imports_for(path):
                    prefix = matching_prefix(module, OWNER_PROHIBITED_PREFIXES[owner])
                    if prefix is not None:
                        violations.append(f"{path.relative_to(ROOT)} imports {module} via {prefix}")

        self.assertEqual([], violations)

    def test_transitional_package_files_stay_small(self) -> None:
        oversized = []
        for directory in TRANSITIONAL_PACKAGE_DIRS:
            for path in package_files(directory):
                line_count = len(path.read_text(encoding="utf-8").splitlines())
                if line_count > 220:
                    oversized.append(f"{path.relative_to(ROOT)} has {line_count} lines")

        self.assertEqual([], oversized)

    def test_owner_package_all_exports_are_unique_and_resolvable(self) -> None:
        violations = []
        for path, module_name in owner_initializer_facades():
            violations.extend(facade_export_integrity_violations(path, module_name))

        self.assertEqual([], violations)

    def test_owner_package_initializers_remain_facade_only(self) -> None:
        violations = []
        for name, directory in OWNER_PACKAGES.items():
            path = directory / "__init__.py"
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                message = facade_initializer_violation(name, node)
                if message is not None:
                    violations.append(f"{path.relative_to(ROOT)}: {message}")

        self.assertEqual([], violations)

    def test_transitional_package_submodules_remain_facade_only(self) -> None:
        violations = []
        for directory in TRANSITIONAL_PACKAGE_DIRS:
            for path in package_files(directory):
                if path.name == "__init__.py":
                    continue
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in tree.body:
                    message = transitional_submodule_violation(node)
                    if message is not None:
                        violations.append(f"{path.relative_to(ROOT)}: {message}")

        self.assertEqual([], violations)

    def test_owner_package_initializer_imports_match_all_exports(self) -> None:
        violations = []
        for path, _ in owner_initializer_facades():
            violations.extend(facade_import_export_alignment_violations(path))

        self.assertEqual([], violations)

    def test_transitional_submodule_imports_match_all_exports(self) -> None:
        violations = []
        for path, _ in transitional_submodule_facades():
            violations.extend(facade_import_export_alignment_violations(path))

        self.assertEqual([], violations)

    def test_transitional_submodule_all_exports_are_unique_and_resolvable(self) -> None:
        violations = []
        for path, module_name in transitional_submodule_facades():
            violations.extend(facade_export_integrity_violations(path, module_name))

        self.assertEqual([], violations)


def facade_initializer_violation(owner: str, node: ast.stmt) -> str | None:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        return None
    if isinstance(node, ast.ImportFrom):
        allowed_prefix = f"minigpt.{owner}."
        if any(alias.name == "*" for alias in node.names):
            return "contains wildcard import"
        if node.module == "__future__" or (node.module or "").startswith(allowed_prefix):
            return None
        return f"imports outside owner facade path: {node.module}"
    if isinstance(node, ast.Assign):
        target_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if target_names == ["__all__"]:
            return None
        return "contains non-__all__ assignment"
    return f"contains implementation statement {type(node).__name__}"


def transitional_submodule_violation(node: ast.stmt) -> str | None:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        return None
    if isinstance(node, ast.ImportFrom):
        if any(alias.name == "*" for alias in node.names):
            return "contains wildcard import"
        return None
    if isinstance(node, ast.Assign):
        target_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if target_names == ["__all__"]:
            return None
        return "contains non-__all__ assignment"
    return f"contains implementation statement {type(node).__name__}"


def owner_initializer_facades() -> list[tuple[Path, str]]:
    return [
        (directory / "__init__.py", f"minigpt.{name}")
        for name, directory in OWNER_PACKAGES.items()
    ]


def transitional_submodule_facades() -> list[tuple[Path, str]]:
    facades: list[tuple[Path, str]] = []
    for directory in TRANSITIONAL_PACKAGE_DIRS:
        for path in package_files(directory):
            if path.name != "__init__.py":
                facades.append((path, module_name_for_source(path)))
    return facades


def module_name_for_source(path: Path) -> str:
    return ".".join(path.relative_to(ROOT / "src").with_suffix("").parts)


def facade_export_integrity_violations(path: Path, module_name: str) -> list[str]:
    module = importlib.import_module(module_name)
    exports = facade_all_export_list(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
    if not isinstance(exports, list):
        return [f"{path.relative_to(ROOT)} does not expose a list __all__"]

    violations = []
    duplicates = sorted({item for item in exports if exports.count(item) > 1})
    if duplicates:
        violations.append(f"{path.relative_to(ROOT)} has duplicate __all__ exports: {', '.join(duplicates)}")

    missing = [item for item in exports if not hasattr(module, item)]
    if missing:
        violations.append(f"{path.relative_to(ROOT)} has unresolved __all__ exports: {', '.join(missing)}")
    return violations


def facade_import_export_alignment_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported_names = facade_imported_names(tree)
    exported_names = facade_all_exports(tree)

    violations = []
    extra_imports = sorted(imported_names - exported_names)
    if extra_imports:
        violations.append(f"{path.relative_to(ROOT)} imports names outside __all__: {', '.join(extra_imports)}")

    missing_imports = sorted(exported_names - imported_names)
    if missing_imports:
        violations.append(f"{path.relative_to(ROOT)} exports names without explicit imports: {', '.join(missing_imports)}")
    return violations


def facade_imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.module == "__future__":
            continue
        for alias in node.names:
            names.add(alias.asname or alias.name)
    return names


def facade_all_exports(tree: ast.Module) -> set[str]:
    exports = facade_all_export_list(tree)
    return set(exports) if isinstance(exports, list) else set()


def facade_all_export_list(tree: ast.Module) -> object:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                return ast.literal_eval(node.value)
    return None


if __name__ == "__main__":
    unittest.main()
