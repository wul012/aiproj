from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.benchmark_scorecard_comparison import load_benchmark_scorecard
from minigpt.benchmark_scorecard_decision import load_benchmark_scorecard_comparison
from minigpt.promoted_training_scale_comparison import load_training_scale_promotion_index
from minigpt.promoted_training_scale_decision import load_promoted_training_scale_comparison
from minigpt.report_loader_dedup import (
    GOVERNANCE_READER_MIGRATED_MODULES,
    MIGRATED_MODULES,
    build_report_loader_dedup_report,
    resolve_exit_code,
    write_report_loader_dedup_outputs,
)
from minigpt.training_portfolio_comparison import load_training_portfolio
from minigpt.training_scale_handoff import load_training_scale_workflow
from minigpt.training_scale_promotion import load_training_scale_handoff
from minigpt.training_scale_run_comparison import load_training_scale_run
from minigpt.training_scale_run_decision import load_training_scale_run_comparison
from scripts.generate_report_loader_dedup_v1140 import main as cli_main
from tests._bootstrap import ROOT


class ReportLoaderDedupTests(unittest.TestCase):
    def test_current_repository_governance_loaders_use_shared_reader(self) -> None:
        report = build_report_loader_dedup_report(ROOT, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(
            report["summary"]["governance_reader_migrated_module_count"],
            len(GOVERNANCE_READER_MIGRATED_MODULES),
        )
        self.assertEqual(report["summary"]["migrated_private_loader_copy_count"], 0)

    def test_migrated_governance_loaders_keep_strict_object_contracts(self) -> None:
        contracts = (
            (load_benchmark_scorecard, "benchmark scorecard"),
            (load_benchmark_scorecard_comparison, "benchmark scorecard comparison"),
            (load_training_scale_workflow, "training scale workflow"),
            (load_training_scale_handoff, "training scale handoff"),
            (load_training_scale_run, "training scale run"),
            (load_training_scale_run_comparison, "training scale run comparison"),
            (load_training_portfolio, "training portfolio"),
            (load_training_scale_promotion_index, "training scale promotion index"),
            (load_promoted_training_scale_comparison, "promoted training scale comparison"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "not-an-object.json"
            source.write_text("[]", encoding="utf-8-sig")

            for loader, description in contracts:
                with self.subTest(description=description):
                    with self.assertRaisesRegex(ValueError, f"{description} must be a JSON object"):
                        loader(source)

    def test_report_passes_when_migrated_modules_use_shared_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_modules(root, migrated=True)
            report = build_report_loader_dedup_report(root)

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["summary"]["dedup_ready"])
        self.assertEqual(report["summary"]["migrated_module_count"], len(MIGRATED_MODULES))
        self.assertEqual(resolve_exit_code(report, require_dedup_ready=True), 0)

    def test_report_fails_when_target_module_keeps_private_loader_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_modules(root, migrated=True)
            _write_module(root, MIGRATED_MODULES[0], private_loader=True)
            report = build_report_loader_dedup_report(root)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_target_private_loader_copy", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_dedup_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_modules(root, migrated=True)
            outputs = write_report_loader_dedup_outputs(build_report_loader_dedup_report(root), root / "out")
            exit_code = cli_main(
                ["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-dedup-ready", "--force"]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})


def _write_modules(root: Path, *, migrated: bool) -> None:
    for module_name in MIGRATED_MODULES:
        _write_module(root, module_name, private_loader=not migrated)


def _write_module(root: Path, module_name: str, *, private_loader: bool) -> None:
    source_dir = root / "src" / "minigpt"
    source_dir.mkdir(parents=True, exist_ok=True)
    if private_loader:
        body = 'import json\nfrom pathlib import Path\ndef read_json_report(path):\n    return json.loads(Path(path).read_text(encoding="utf-8-sig"))\n'
    else:
        body = "from minigpt.report_utils import locate_upstream_report, read_json_object\n"
        body += "def read_json_report(path):\n    return read_json_object(path, description='sample')\n"
    (source_dir / module_name).write_text(body, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
