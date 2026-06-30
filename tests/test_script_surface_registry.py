from __future__ import annotations

import ast
import contextlib
import importlib
import io
import unittest
from pathlib import Path

from scripts._bootstrap import (
    BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS,
    BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS,
    CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS,
    PROJECT_ROOT,
    SCRIPT_ENTRYPOINT_SURFACES,
    SCRIPT_SUPPORT_MODULES,
)
from tests._bootstrap import ROOT
from tests.script_bootstrap_helpers import (
    function_def,
    has_direct_script_entrypoint,
    module_name as script_module_name,
)


class ScriptSurfaceRegistryTests(unittest.TestCase):
    def test_current_maintained_script_entrypoints_are_partitioned(self) -> None:
        engineering = set(BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS)
        active_cli = set(BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS)
        current = set(CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS)

        self.assertEqual(PROJECT_ROOT, ROOT)
        self.assertFalse(engineering & active_cli)
        self.assertEqual(current, engineering | active_cli)
        self.assertEqual(len(CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS), len(current))
        for relative in CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS:
            with self.subTest(relative=relative):
                self.assertTrue(relative.startswith("scripts/"))
                self.assertNotIn("/devtools/", relative.replace("\\", "/"))
                self.assertTrue((PROJECT_ROOT / relative).is_file())

    def test_script_entrypoint_surfaces_are_tuple_based_posix_paths(self) -> None:
        bootstrap_module = importlib.import_module("scripts._bootstrap")
        self.assertIn("SCRIPT_ENTRYPOINT_SURFACES", getattr(bootstrap_module, "__all__"))
        self.assertIn("CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS", SCRIPT_ENTRYPOINT_SURFACES)
        self.assertIn("BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS", SCRIPT_ENTRYPOINT_SURFACES)

        for surface_name, paths in SCRIPT_ENTRYPOINT_SURFACES.items():
            with self.subTest(surface_name=surface_name):
                self.assertIs(paths, getattr(bootstrap_module, surface_name))
                self.assertTrue(surface_name.endswith("_ENTRYPOINTS"))
                self.assertIsInstance(paths, tuple)
                self.assertEqual(len(paths), len(set(paths)))

            for relative in paths:
                with self.subTest(surface_name=surface_name, relative=relative):
                    self.assertIsInstance(relative, str)
                    self.assertTrue(relative.startswith("scripts/"))
                    self.assertTrue(relative.endswith(".py"))
                    self.assertNotIn("\\", relative)
                    self.assertNotIn("//", relative)
                    self.assertNotIn("..", relative.split("/"))
                    self.assertFalse(Path(relative).is_absolute())
                    self.assertTrue((PROJECT_ROOT / relative).is_file())

    def test_current_maintained_script_entrypoints_import_without_cli_side_effects(self) -> None:
        for relative in CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS:
            module_name = script_module_name(relative)
            with self.subTest(relative=relative):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    module = importlib.import_module(module_name)
                    importlib.reload(module)

                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(stderr.getvalue(), "")
                self.assertTrue(callable(getattr(module, "main", None)))

    def test_script_support_modules_are_internal_support_surface(self) -> None:
        self.assertGreaterEqual(len(SCRIPT_SUPPORT_MODULES), 3)
        self.assertEqual(len(SCRIPT_SUPPORT_MODULES), len(set(SCRIPT_SUPPORT_MODULES)))
        maintained_entrypoint_paths = set(CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS)

        for module_name in SCRIPT_SUPPORT_MODULES:
            module_path = module_name.replace(".", "/") + ".py"
            path = PROJECT_ROOT / module_path
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            with self.subTest(module_name=module_name):
                self.assertTrue(module_name.startswith("scripts._"))
                self.assertTrue(path.is_file())
                self.assertNotIn(module_path, maintained_entrypoint_paths)
                self.assertIsNone(function_def(tree, "main"))
                self.assertIsNone(function_def(tree, "parse_args"))
                self.assertFalse(has_direct_script_entrypoint(tree))

    def test_script_support_modules_have_clean_export_tables(self) -> None:
        violations = []
        for module_name in SCRIPT_SUPPORT_MODULES:
            module = importlib.import_module(module_name)
            exports = getattr(module, "__all__", None)
            if not isinstance(exports, list):
                violations.append(f"{module_name} does not expose a list __all__")
                continue

            duplicates = sorted({item for item in exports if exports.count(item) > 1})
            if duplicates:
                violations.append(f"{module_name} has duplicate __all__ exports: {', '.join(duplicates)}")

            missing = [item for item in exports if not hasattr(module, item)]
            if missing:
                violations.append(f"{module_name} has unresolved __all__ exports: {', '.join(missing)}")

        self.assertEqual([], violations)

    def test_script_support_modules_import_without_side_effects(self) -> None:
        for module_name in SCRIPT_SUPPORT_MODULES:
            with self.subTest(module_name=module_name):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    module = importlib.import_module(module_name)
                    importlib.reload(module)

                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(stderr.getvalue(), "")

    def test_stable_script_entrypoints_are_documented(self) -> None:
        text = (PROJECT_ROOT / "docs" / "script-entrypoints.md").read_text(encoding="utf-8")

        self.assertIn("stable maintainer", text)
        self.assertIn("Current Maintained Script Surface", text)
        self.assertIn("CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS", text)
        self.assertIn("FOUNDATION_ACTIVE_CLI_ENTRYPOINTS", text)
        self.assertIn("REPORT_ACTIVE_CLI_ENTRYPOINTS", text)
        self.assertIn("GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS", text)
        self.assertIn("ACTIVE_CLI_BEHAVIOR_COVERAGE", text)
        self.assertIn("Promotion Rule", text)
        self.assertIn("Text Hygiene", text)
        self.assertIn("import-safe", text)
        self.assertIn('parse_args(["--help"])', text)
        self.assertIn("Local Aggregate", text)
        self.assertIn("CI-Backed Gates", text)
        self.assertIn("historical", text)
        self.assertIn("SCRIPT_ENTRYPOINT_SURFACES", text)
        self.assertIn("SCRIPT_SUPPORT_MODULES", text)
        self.assertIn("repository-relative POSIX `.py` paths", text)
        self.assertIn("not runnable maintainer entrypoints", text)
        self.assertIn("support module `__all__`", text)
        self.assertIn("Support modules are also import-safe", text)
        for module_name in SCRIPT_SUPPORT_MODULES:
            with self.subTest(module_name=module_name):
                self.assertIn(module_name.replace(".", "/") + ".py", text)
        for relative in BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS:
            with self.subTest(relative=relative):
                self.assertIn(relative, text)
        for relative in BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS:
            with self.subTest(relative=relative):
                self.assertIn(relative, text)


if __name__ == "__main__":
    unittest.main()
