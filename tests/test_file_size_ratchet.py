from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt.file_size_ratchet import build_file_size_ratchet_report, write_file_size_ratchet_outputs
from scripts.check_file_size_ratchet import main as cli_main


class FileSizeRatchetTests(unittest.TestCase):
    def test_current_repository_file_size_ratchet_passes_with_explicit_waivers(self) -> None:
        report = build_file_size_ratchet_report(project_root=ROOT, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "continue_with_file_size_ratchet")
        self.assertGreater(report["summary"]["scanned_file_count"], 1000)
        self.assertEqual(report["summary"]["max_line_limit"], 800)
        self.assertEqual(report["summary"]["waiver_count"], 8)
        self.assertEqual(report["summary"]["unwaived_over_limit_count"], 0)
        self.assertEqual(report["summary"]["waiver_growth_violation_count"], 0)
        self.assertEqual(report["summary"]["largest_file_path"], "tests/test_promoted_training_scale_seed_handoff.py")

    def test_unwaived_over_limit_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            (root / "tests" / "test_large.py").write_text("x = 1\n" * 801, encoding="utf-8")
            config = root / "file-size.json"
            config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "policy": "aiproj_file_size_ratchet",
                        "warning_line_limit": 500,
                        "max_line_limit": 800,
                        "targets": ["tests"],
                        "waivers": [],
                    }
                ),
                encoding="utf-8",
            )

            report = build_file_size_ratchet_report(config, project_root=root, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["unwaived_over_limit_count"], 1)
        self.assertIn(
            "max_lines:tests/test_large.py", {item["check_id"] for item in report["checks"] if item["status"] == "fail"}
        )

    def test_waived_file_growth_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            (root / "tests" / "test_legacy.py").write_text("x = 1\n" * 805, encoding="utf-8")
            config = root / "file-size.json"
            config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "policy": "aiproj_file_size_ratchet",
                        "warning_line_limit": 500,
                        "max_line_limit": 800,
                        "targets": ["tests"],
                        "waivers": [
                            {
                                "path": "tests/test_legacy.py",
                                "baseline_lines": 804,
                                "reason": "legacy broad test",
                                "followup": "split before adding cases",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_file_size_ratchet_report(config, project_root=root, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["waiver_growth_violation_count"], 1)
        self.assertIn(
            "waiver_no_growth:tests/test_legacy.py",
            {item["check_id"] for item in report["checks"] if item["status"] == "fail"},
        )

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            out_dir = Path(tmp) / "out"
            exit_code = cli_main(["--out-dir", str(out_dir)])
            outputs = write_file_size_ratchet_outputs(
                build_file_size_ratchet_report(project_root=ROOT, generated_at="2026-01-01T00:00:00Z"),
                Path(tmp) / "manual",
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((out_dir / "file_size_ratchet.json").is_file())
            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("MiniGPT File Size Ratchet", Path(outputs["markdown"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
