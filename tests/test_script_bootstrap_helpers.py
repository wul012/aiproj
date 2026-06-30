from __future__ import annotations

import ast
import unittest

from tests._bootstrap import ROOT
from tests.script_bootstrap_helpers import (
    arg_names,
    function_def,
    has_direct_script_entrypoint,
    is_dunder_main_check,
    module_name,
    raises_system_exit_from_main,
)


class ScriptBootstrapHelperTests(unittest.TestCase):
    def test_helper_module_exports_are_explicit_and_resolvable(self) -> None:
        helper_path = ROOT / "tests" / "script_bootstrap_helpers.py"
        self.assertTrue(helper_path.is_file())

        import tests.script_bootstrap_helpers as helpers

        exports = getattr(helpers, "__all__", None)
        self.assertIsInstance(exports, list)
        self.assertEqual(len(exports), len(set(exports)))
        self.assertEqual([], [name for name in exports if not hasattr(helpers, name)])

    def test_function_def_and_arg_names_read_top_level_cli_contracts(self) -> None:
        tree = ast.parse(
            "def parse_args(argv):\n"
            "    return argv\n"
            "\n"
            "def main(argv, *, force=False) -> int:\n"
            "    return 0\n"
        )

        main = function_def(tree, "main")

        self.assertIsNotNone(function_def(tree, "parse_args"))
        self.assertIsNone(function_def(tree, "missing"))
        self.assertEqual(arg_names(main), ("argv", "force"))
        self.assertEqual(arg_names(None), ())

    def test_system_exit_detection_requires_main_call(self) -> None:
        ready_tree = ast.parse("raise SystemExit(main())\n")
        unrelated_tree = ast.parse("raise SystemExit(2)\n")

        self.assertTrue(raises_system_exit_from_main(ready_tree))
        self.assertFalse(raises_system_exit_from_main(unrelated_tree))

    def test_dunder_main_entrypoint_detection_is_top_level_only(self) -> None:
        script_tree = ast.parse(
            'if __name__ == "__main__":\n'
            "    raise SystemExit(main())\n"
        )
        nested_tree = ast.parse(
            "def wrapper():\n"
            '    if __name__ == "__main__":\n'
            "        raise SystemExit(main())\n"
        )

        self.assertTrue(is_dunder_main_check(script_tree.body[0].test))
        self.assertTrue(has_direct_script_entrypoint(script_tree))
        self.assertFalse(has_direct_script_entrypoint(nested_tree))

    def test_module_name_translates_repository_relative_script_paths(self) -> None:
        self.assertEqual(module_name("scripts/check_normalization_guard.py"), "scripts.check_normalization_guard")
        self.assertEqual(module_name("scripts/devtools/check_project_docs_readability_v1131.py"), "scripts.devtools.check_project_docs_readability_v1131")


if __name__ == "__main__":
    unittest.main()
