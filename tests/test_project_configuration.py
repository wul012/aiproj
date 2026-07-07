from __future__ import annotations

import json
import sys
import tomllib
import unittest

from tests._bootstrap import ROOT

from scripts._bootstrap import BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS
from scripts._normalization_guard import FOCUSED_TEST_MODULES, build_command
from minigpt.ci_workflow_hygiene_policy import COVERAGE_FAIL_UNDER_FLOOR, REQUIRED_COMMAND_FRAGMENTS


def read_requirements() -> set[str]:
    return {
        line.strip()
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def read_coverage_floor_policy() -> dict[str, object]:
    return json.loads((ROOT / "docs" / "static-analysis" / "coverage-floor.json").read_text(encoding="utf-8"))


class ProjectConfigurationTests(unittest.TestCase):
    def test_pyproject_declares_src_layout_and_test_discovery(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["build-system"]["build-backend"], "setuptools.build_meta")
        self.assertEqual(pyproject["tool"]["setuptools"]["packages"]["find"]["where"], ["src"])
        self.assertEqual(pyproject["tool"]["pytest"]["ini_options"]["pythonpath"], ["src"])
        self.assertEqual(pyproject["tool"]["pytest"]["ini_options"]["testpaths"], ["tests"])
        self.assertEqual(pyproject["tool"]["pytest"]["ini_options"]["python_files"], ["test_*.py"])

    def test_runtime_dependencies_are_aligned_with_requirements(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project_dependencies = set(pyproject["project"]["dependencies"])
        requirements = read_requirements()

        self.assertIn("torch>=2.6", project_dependencies)
        self.assertIn("numpy>=2.0", project_dependencies)
        self.assertTrue(project_dependencies.issubset(requirements))
        self.assertIn("coverage>=7.0", requirements)
        self.assertIn("ruff>=0.8,<1.0", requirements)
        self.assertIn("mypy>=1.13,<2.0", requirements)
        self.assertTrue(pyproject["tool"]["mypy"]["strict"])
        self.assertEqual(pyproject["tool"]["mypy"]["follow_imports"], "skip")

    def test_ci_uses_the_standard_coverage_entrypoint(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        coverage_floor = read_coverage_floor_policy()["fail_under"]
        coverage_command = (
            f"python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under {coverage_floor}"
        )

        self.assertIn("pip install -r requirements.txt", workflow)
        self.assertIn("python -B scripts/check_normalization_guard.py", workflow)
        self.assertIn("python -B scripts/check_project_docs_readability.py", workflow)
        self.assertIn("python -B scripts/check_static_analysis.py --out-dir runs/static-analysis-ci", workflow)
        self.assertIn("python -B scripts/check_type_analysis.py --out-dir runs/type-analysis-ci", workflow)
        self.assertIn(
            "python -B scripts/check_model_capability_honest_measurement.py "
            "--out-dir runs/model-capability-honest-measurement-ci",
            workflow,
        )
        self.assertIn(coverage_command, workflow)
        self.assertIn("python -B scripts/check_source_encoding.py", workflow)

    def test_coverage_floor_is_committed_and_ratchet_locked(self) -> None:
        policy = read_coverage_floor_policy()

        self.assertEqual(policy["schema_version"], 1)
        self.assertEqual(policy["tool"], "coverage")
        self.assertEqual(policy["observed_baseline_version"], "v1262.0.0")
        self.assertEqual(policy["observed_baseline_percent"], 90.98)
        self.assertEqual(policy["floor_policy"], "observed_baseline_minus_two_points")
        self.assertEqual(policy["fail_under"], 88.98)
        self.assertEqual(COVERAGE_FAIL_UNDER_FLOOR, policy["fail_under"])
        self.assertEqual(REQUIRED_COMMAND_FRAGMENTS["coverage_fail_under_gate"], "--fail-under 88.98")

    def test_start_here_points_to_unittest_discovery(self) -> None:
        start_here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")

        self.assertIn("python -B scripts/check_engineering_health.py", start_here)
        self.assertIn("python -B scripts/check_static_analysis.py", start_here)
        self.assertIn("python -B scripts/check_type_analysis.py", start_here)
        self.assertIn("python -B scripts/check_model_capability_honest_measurement.py", start_here)
        self.assertIn("python -m unittest discover -s tests -v", start_here)
        self.assertIn("python -B scripts/check_normalization_guard.py", start_here)
        self.assertIn("docs/architecture-map.md", start_here)
        self.assertIn("docs/engineering-workflow.md", start_here)

    def test_normalization_guard_has_documented_entrypoint(self) -> None:
        workflow = (ROOT / "docs" / "engineering-workflow.md").read_text(encoding="utf-8")
        roadmap = (ROOT / "docs" / "normalization-roadmap.md").read_text(encoding="utf-8")
        command = build_command()

        self.assertEqual(command[:4], [sys.executable, "-B", "-m", "unittest"])
        self.assertIn("tests.test_script_bootstrap", FOCUSED_TEST_MODULES)
        self.assertIn("tests.test_source_encoding_hygiene", FOCUSED_TEST_MODULES)
        self.assertIn("tests.test_ci_workflow", FOCUSED_TEST_MODULES)
        self.assertIn("tests.test_test_coverage_report", FOCUSED_TEST_MODULES)
        self.assertIn("tests.test_project_docs_readability", FOCUSED_TEST_MODULES)
        self.assertGreaterEqual(len(BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS), 6)
        self.assertIn("python -B scripts/check_normalization_guard.py", workflow)
        self.assertIn("scripts/check_static_analysis.py", workflow)
        self.assertIn("scripts/check_normalization_guard.py", roadmap)

    def test_normalization_docs_are_indexed(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        docs_readme = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        docs = [
            "architecture-map.md",
            "module-inventory.md",
            "public-api.md",
            "normalization-roadmap.md",
            "engineering-workflow.md",
            "normalization-guard.md",
            "script-entrypoints.md",
        ]

        for doc in docs:
            self.assertTrue((ROOT / "docs" / doc).is_file(), doc)
            self.assertIn(f"(docs/{doc})", root_readme)
            self.assertIn(f"({doc})", docs_readme)


if __name__ == "__main__":
    unittest.main()
