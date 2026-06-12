from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_regression_inventory import (
    build_model_capability_regression_inventory,
    locate_regression_plan,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_inventory_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.evaluation.inventory_model_capability_regression_evidence_v1136 import main as cli_main


class ModelCapabilityRegressionInventoryTests(unittest.TestCase):
    def test_inventory_ready_when_existing_files_cover_plan_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = _write_plan(root)
            _write_file(root / "scripts" / "check_required_term.py")
            _write_file(root / "src" / "minigpt" / "required_term_coverage.py")
            _write_file(root / "tests" / "test_required_term_coverage.py")
            report = build_model_capability_regression_inventory(read_json_report(plan_path), root=root, plan_path=plan_path)

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["summary"]["inventory_ready"])
        self.assertEqual(report["summary"]["ready_item_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_inventory_ready=True), 0)

    def test_inventory_fails_when_tests_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = _write_plan(root)
            _write_file(root / "scripts" / "check_required_term.py")
            report = build_model_capability_regression_inventory(read_json_report(plan_path), root=root, plan_path=plan_path)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["ready_item_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_inventory_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = _write_plan(root)
            _write_file(root / "src" / "minigpt" / "required_term_coverage.py")
            _write_file(root / "tests" / "test_required_term_coverage.py")
            report = build_model_capability_regression_inventory(read_json_report(plan_path), root=root, plan_path=plan_path)
            outputs = write_model_capability_regression_inventory_outputs(report, root / "out")
            exit_code = cli_main([str(plan_path.parent), "--root", str(root), "--out-dir", str(root / "cli-out"), "--require-inventory-ready", "--force"])
            located = locate_regression_plan(plan_path.parent)

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertEqual(located, plan_path)


def _write_plan(root: Path) -> Path:
    out_dir = root / "plan"
    out_dir.mkdir(parents=True)
    path = out_dir / "model_capability_regression_plan_v1135.json"
    write_json_payload(
        {
            "status": "pass",
            "plan": {"plan_ready": True},
            "summary": {"plan_ready": True},
            "rows": [{"check_id": "required_term_coverage", "scope": "surface", "evidence_kind": "coverage"}],
        },
        path,
    )
    return path


def _write_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("VALUE = 1\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
