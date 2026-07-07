from __future__ import annotations

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from tests._bootstrap import ROOT

from minigpt.project_docs_readability import (
    DOC_TARGETS,
    FRONT_DOOR_TARGETS,
    LEGACY_V1131_OUTPUT_STEM,
    STABLE_OUTPUT_STEM,
    build_project_docs_readability_report,
    resolve_exit_code,
    write_project_docs_readability_outputs,
)
from scripts.check_project_docs_readability import main as cli_main
from scripts.devtools.check_project_docs_readability_v1131 import main as legacy_cli_main


class ProjectDocsReadabilityTests(unittest.TestCase):
    def test_docs_split_passes_when_targets_and_links_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_docs_fixture(root)
            report = build_project_docs_readability_report(root, generated_at="2026-06-12T00:00:00Z")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["row_count"], len(DOC_TARGETS) + len(FRONT_DOOR_TARGETS))
        self.assertEqual(report["summary"]["ready_row_count"], len(DOC_TARGETS) + len(FRONT_DOOR_TARGETS))
        self.assertEqual(report["summary"]["doc_target_count"], len(DOC_TARGETS))
        self.assertEqual(report["summary"]["ready_doc_count"], len(DOC_TARGETS))
        self.assertEqual(report["summary"]["front_door_target_count"], len(FRONT_DOOR_TARGETS))
        self.assertEqual(report["summary"]["front_door_failed_count"], 0)
        self.assertEqual(report["summary"]["forbidden_term_hit_count"], 0)
        self.assertEqual(report["summary"]["missing_readme_link_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_docs_split_fails_when_readme_link_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_docs_fixture(root)
            (root / "README.md").write_text("# MiniGPT\n\n[Overview](docs/overview.md)\n", encoding="utf-8")
            report = build_project_docs_readability_report(root)

        self.assertEqual(report["status"], "fail")
        self.assertGreater(report["summary"]["missing_readme_link_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_docs_split_fails_when_front_door_has_mojibake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_docs_fixture(root)
            (root / "START_HERE.md").write_text(
                "# Start Here: MiniGPT From Scratch\n\n"
                "docs/architecture-map.md docs/engineering-workflow.md scripts/check_normalization_guard.py \u9225\n",
                encoding="utf-8",
            )
            report = build_project_docs_readability_report(root)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["front_door_failed_count"], 1)
        self.assertEqual(report["summary"]["forbidden_term_hit_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_docs_fixture(root)
            report = build_project_docs_readability_report(root)
            outputs = write_project_docs_readability_outputs(report, root / "out")
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = cli_main(
                    ["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-pass", "--force"]
                )
            cli_outputs = sorted((root / "cli-out").glob("*"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(all(Path(path).stem == STABLE_OUTPUT_STEM for path in outputs.values()))
        self.assertTrue(cli_outputs)
        self.assertTrue(all(path.stem == STABLE_OUTPUT_STEM for path in cli_outputs))

    def test_legacy_v1131_cli_keeps_legacy_output_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_docs_fixture(root)
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = legacy_cli_main(
                    ["--root", str(root), "--out-dir", str(root / "legacy-out"), "--require-pass", "--force"]
                )
            legacy_outputs = sorted((root / "legacy-out").glob("*"))

        self.assertEqual(exit_code, 0)
        self.assertTrue(legacy_outputs)
        self.assertTrue(all(path.stem == LEGACY_V1131_OUTPUT_STEM for path in legacy_outputs))

    def test_stable_cli_is_documented_for_maintainers(self) -> None:
        workflow = (ROOT / "docs" / "engineering-workflow.md").read_text(encoding="utf-8")
        roadmap = (ROOT / "docs" / "normalization-roadmap.md").read_text(encoding="utf-8")

        self.assertIn("python -B scripts/check_project_docs_readability.py", workflow)
        self.assertIn("scripts/check_project_docs_readability.py", roadmap)


def _write_docs_fixture(root: Path) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True)
    links = []
    for target in DOC_TARGETS:
        path = root / str(target["path"])
        body = [
            str(target["title"]),
            "",
            (
                "MiniGPT AI governance publication receipt training evaluation holdout contract check "
                "lookup-only promotion model quality governance core f/ screenshot artifact owner class "
                "Owner class compatibility path Normalized Owner Packages minigpt.governance "
                "recursively scans "
                "Tier 1 compatibility owner packages flat modules minigpt.evaluation.prediction minigpt.serving.chat minigpt.reports.utils "
                "Root Facade Export Budget _root_exports.py _root_*exports*.py "
                "Current Phase owner packages Next Actions unittest CI check_engineering_health.py "
                "stable maintainer Current Maintained Script Surface CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS "
                "FOUNDATION_ACTIVE_CLI_ENTRYPOINTS REPORT_ACTIVE_CLI_ENTRYPOINTS GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS "
                "Normalized Active CLIs Promotion Rule Text Hygiene import-safe root `minigpt` facade mojibake historical "
                "SCRIPT_ENTRYPOINT_SURFACES SCRIPT_SUPPORT_MODULES "
                "repository-relative POSIX `.py` paths "
                "not runnable maintainer entrypoints support module `__all__` "
                "Support modules are also import-safe FOCUSED_TEST_MODULES tests.test_script_bootstrap tests.test_script_bootstrap_helpers tests.test_script_surface_registry tests.test_script_cli_contracts "
                "tests.test_report_utils tests.test_report_utils_helpers tests.test_active_cli_coverage tests.test_active_cli_behavior tests.test_model_cli_behavior tests.test_serving_cli_behavior tests.test_report_cli_behavior tests.test_governance_cli_behavior "
                "tests.test_governance_extended_cli_behavior ACTIVE_CLI_BEHAVIOR_COVERAGE tests.test_test_coverage_report "
                "transitional package files stay small facade-only package initializers hidden re-export drift "
                "facade-only transitional submodules explicit imports aligned with `__all__` submodule `__all__` tables"
                " Gate-By-Gate Evidence Matrix No-Promotion Boundary scripts/check_aiproj_track_closeout.py"
            ),
        ]
        path.write_text("\n".join(body), encoding="utf-8")
        links.append(f"- [{path.stem}]({target['path']})")
    (root / "README.md").write_text("# MiniGPT\n\n" + "\n".join(links) + "\n", encoding="utf-8")
    (root / "START_HERE.md").write_text(
        "\n".join(
            [
                "# Start Here: MiniGPT From Scratch",
                "",
                "Read docs/architecture-map.md and docs/engineering-workflow.md first.",
                "Use docs/normalization-guard.md for the focused guard inventory.",
                "Use docs/script-entrypoints.md for the stable maintainer script map.",
                "Run scripts/check_normalization_guard.py before changing normalized surfaces.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (docs / "README.md").write_text(
        "\n".join(
            [
                "# MiniGPT Documentation Map",
                "",
                "- architecture-map.md",
                "- engineering-workflow.md",
                "- normalization-roadmap.md",
                "- normalization-guard.md",
                "- script-entrypoints.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
