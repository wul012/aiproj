from __future__ import annotations

import ast
import contextlib
import importlib
import io
import unittest

from scripts._bootstrap import (
    BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS,
    BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS,
    PROJECT_ROOT,
)
from tests._bootstrap import ROOT
from tests.script_bootstrap_helpers import (
    arg_names,
    function_def,
    module_name as script_module_name,
    raises_system_exit_from_main,
)

ACTIVE_CLI_FORBIDDEN_MOJIBAKE_MARKERS = (
    "\ufffd",
    "\u6d5c\u54c4\u4f10",
    "\u93c5\u9e3f\u5158",
    "\u6d63\u72b3",
    "\u6d93\u20ac\u6d93",
    "\u755d\u5a32",
    "\u9354\u2542\u589c",
    "\u9286",
)

LEGACY_PARENT_BOOTSTRAP = "Path(__file__).resolve()" + ".parents[1]"
LEGACY_SYS_PATH_INSERT = "sys.path" + '.insert(0, str(ROOT / "src"))'


class ScriptCliContractTests(unittest.TestCase):
    def test_current_engineering_entrypoints_use_shared_bootstrap(self) -> None:
        self.assertEqual(PROJECT_ROOT, ROOT)
        self.assertGreaterEqual(len(BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS), 6)
        self.assertEqual(len(BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS), len(set(BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS)))
        for relative in BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS:
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("_bootstrap", text)
                self.assertNotIn(LEGACY_PARENT_BOOTSTRAP, text)
                self.assertNotIn(LEGACY_SYS_PATH_INSERT, text)

    def test_current_active_cli_entrypoints_use_shared_bootstrap(self) -> None:
        self.assertGreaterEqual(len(BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS), 4)
        self.assertEqual(len(BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS), len(set(BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS)))
        for relative in BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS:
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("_bootstrap", text)
                self.assertIn("ensure_src_path()", text)
                self.assertNotIn(LEGACY_PARENT_BOOTSTRAP, text)
                self.assertNotIn(LEGACY_SYS_PATH_INSERT, text)

    def test_active_cli_entrypoints_have_testable_cli_contract(self) -> None:
        for relative in BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS:
            path = PROJECT_ROOT / relative
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            main = function_def(tree, "main")
            parse_args = function_def(tree, "parse_args")

            with self.subTest(relative=relative):
                self.assertIsNotNone(main)
                self.assertIn("argv", arg_names(main))
                self.assertEqual(ast.unparse(main.returns) if main.returns else "", "int")
                self.assertTrue(raises_system_exit_from_main(tree))
                self.assertIsNotNone(parse_args)
                self.assertIn("argv", arg_names(parse_args))

    def test_active_cli_entrypoints_do_not_ship_mojibake_default_text(self) -> None:
        violations = []
        for relative in BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS:
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for marker in ACTIVE_CLI_FORBIDDEN_MOJIBAKE_MARKERS:
                if marker in text:
                    violations.append(f"{relative} contains mojibake marker {marker!r}")

        self.assertEqual([], violations)

    def test_active_cli_mojibake_markers_are_ascii_escaped_in_source(self) -> None:
        text = (PROJECT_ROOT / "tests" / "test_script_cli_contracts.py").read_text(encoding="utf-8")
        block_start = text.index("ACTIVE_CLI_FORBIDDEN_MOJIBAKE_MARKERS")
        block_end = text.index("\n\nclass ScriptCliContractTests", block_start)
        marker_block = text[block_start:block_end]
        non_ascii = sorted({char for char in marker_block if ord(char) > 127})

        self.assertEqual([], non_ascii)

    def test_active_cli_help_uses_parse_args_and_exits_zero(self) -> None:
        for relative in BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS:
            module = importlib.import_module(script_module_name(relative))
            stdout = io.StringIO()
            stderr = io.StringIO()

            with self.subTest(relative=relative):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as raised:
                        module.parse_args(["--help"])

                self.assertEqual(raised.exception.code, 0)
                self.assertIn("usage:", stdout.getvalue())
                self.assertEqual(stderr.getvalue(), "")

    def test_current_engineering_entrypoints_have_testable_cli_contract(self) -> None:
        for relative in BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS:
            path = PROJECT_ROOT / relative
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            main = function_def(tree, "main")
            parse_args = function_def(tree, "parse_args")

            with self.subTest(relative=relative):
                self.assertIsNotNone(main)
                self.assertIn("argv", arg_names(main))
                self.assertEqual(ast.unparse(main.returns) if main.returns else "", "int")
                self.assertTrue(raises_system_exit_from_main(tree))
                if parse_args is not None:
                    self.assertIn("argv", arg_names(parse_args))


if __name__ == "__main__":
    unittest.main()
