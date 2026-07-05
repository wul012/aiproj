from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path

from scripts._bootstrap import (
    BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS,
    CI_ENGINEERING_ENTRYPOINTS,
    HEALTH_ENGINEERING_ENTRYPOINTS,
    LOCAL_ONLY_ENGINEERING_ENTRYPOINTS,
    PROJECT_ROOT,
    SRC_ROOT,
    ensure_src_path,
)

ensure_src_path()

from minigpt.ci_workflow_hygiene import REQUIRED_COMMAND_FRAGMENTS  # noqa: E402
from scripts._normalization_guard import FOCUSED_TEST_MODULES, build_command, focused_test_paths
from scripts.check_normalization_guard import main as normalization_guard_main


class ScriptBootstrapTests(unittest.TestCase):
    def test_project_paths_are_resolved_from_repository_root(self) -> None:
        self.assertEqual(PROJECT_ROOT, Path(__file__).resolve().parents[1])
        self.assertEqual(SRC_ROOT, PROJECT_ROOT / "src")
        self.assertTrue((SRC_ROOT / "minigpt").is_dir())

    def test_ensure_src_path_is_idempotent_and_preferred(self) -> None:
        original_path = list(sys.path)
        try:
            sys.path[:] = [path for path in sys.path if path != str(SRC_ROOT)]
            self.assertNotIn(str(SRC_ROOT), sys.path)

            returned = ensure_src_path()
            ensure_src_path()

            self.assertEqual(returned, SRC_ROOT)
            self.assertEqual(sys.path[0], str(SRC_ROOT))
            self.assertEqual(sys.path.count(str(SRC_ROOT)), 1)
        finally:
            sys.path[:] = original_path

    def test_tests_package_import_bootstraps_src_for_direct_unittest_modules(self) -> None:
        script = (
            "import sys\n"
            "from pathlib import Path\n"
            "src = str(Path.cwd() / 'src')\n"
            "sys.path[:] = [path for path in sys.path if path != src]\n"
            "import tests\n"
            "import minigpt\n"
            "print(sys.path[0])\n"
            "print(tests.__all__)\n"
        )

        completed = subprocess.run(
            [sys.executable, "-B", "-c", script],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        stdout_lines = completed.stdout.strip().splitlines()
        self.assertEqual(stdout_lines[0], str(SRC_ROOT))
        self.assertIn("ensure_src_path", stdout_lines[1])

    def test_ci_engineering_entrypoints_are_partitioned_and_required(self) -> None:
        workflow_text = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        required_fragments = set(REQUIRED_COMMAND_FRAGMENTS.values())

        self.assertEqual(
            set(BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS),
            set(LOCAL_ONLY_ENGINEERING_ENTRYPOINTS) | set(CI_ENGINEERING_ENTRYPOINTS),
        )
        self.assertFalse(set(LOCAL_ONLY_ENGINEERING_ENTRYPOINTS) & set(CI_ENGINEERING_ENTRYPOINTS))
        self.assertEqual(CI_ENGINEERING_ENTRYPOINTS[: len(HEALTH_ENGINEERING_ENTRYPOINTS)], HEALTH_ENGINEERING_ENTRYPOINTS)
        self.assertNotIn("scripts/run_test_coverage.py", HEALTH_ENGINEERING_ENTRYPOINTS)
        self.assertIn("scripts/check_engineering_health.py", LOCAL_ONLY_ENGINEERING_ENTRYPOINTS)

        for relative in CI_ENGINEERING_ENTRYPOINTS:
            with self.subTest(relative=relative):
                self.assertIn(relative, required_fragments)
                self.assertIn(relative, workflow_text)

        for relative in LOCAL_ONLY_ENGINEERING_ENTRYPOINTS:
            with self.subTest(relative=relative):
                self.assertNotIn(relative, required_fragments)

    def test_current_normalization_tests_use_shared_test_bootstrap(self) -> None:
        command = build_command(python_executable="python")
        paths = focused_test_paths(exclude_modules={"tests.test_script_bootstrap"})

        self.assertEqual(command[:4], ["python", "-B", "-m", "unittest"])
        self.assertEqual(tuple(command[4:]), FOCUSED_TEST_MODULES)
        self.assertEqual(len(FOCUSED_TEST_MODULES), len(set(FOCUSED_TEST_MODULES)))
        self.assertIn("tests.test_script_bootstrap", FOCUSED_TEST_MODULES)
        for relative in paths:
            path = PROJECT_ROOT / relative
            text = path.read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertTrue(path.is_file())
                self.assertIn("tests._bootstrap", text)
                self.assertNotIn("Path(__file__).resolve().parents[1]", text)
                self.assertNotIn("sys.path.insert", text)

    def test_current_normalization_tests_are_documented(self) -> None:
        text = (PROJECT_ROOT / "docs" / "normalization-guard.md").read_text(encoding="utf-8")

        self.assertIn("FOCUSED_TEST_MODULES", text)
        self.assertIn("What This Guard Does Not Prove", text)
        for module in FOCUSED_TEST_MODULES:
            with self.subTest(module=module):
                self.assertIn(module, text)

    def test_normalization_guard_cli_accepts_runner_and_returns_status(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(command: list[str], **_: object) -> subprocess.CompletedProcess[list[str]]:
            calls.append(command)
            return subprocess.CompletedProcess(command, 7)

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            exit_code = normalization_guard_main(runner=fake_runner)
            bad_args_code = normalization_guard_main(["unexpected"], runner=fake_runner)

        self.assertEqual(exit_code, 7)
        self.assertEqual(bad_args_code, 2)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], build_command())
        self.assertIn("Running normalization guard", stdout.getvalue())

    def test_normalization_guard_script_rejects_unknown_arguments(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(PROJECT_ROOT / "scripts" / "check_normalization_guard.py"), "unexpected"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("does not accept positional arguments", completed.stdout)


if __name__ == "__main__":
    unittest.main()
