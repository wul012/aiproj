from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from scripts.check_archived_path_portability import (  # noqa: E402
    CHECK_CSV_FILENAME,
    CHECK_HTML_FILENAME,
    CHECK_JSON_FILENAME,
    CHECK_MARKDOWN_FILENAME,
    DEFAULT_INPUTS,
    build_archived_path_portability_report,
    render_archived_path_portability_markdown,
    render_archived_path_portability_text,
    write_archived_path_portability_outputs,
)


class ArchivedPathPortabilityTests(unittest.TestCase):
    def test_report_accepts_windows_separator_artifact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "archive" / "receipt.json"
            sidecar = root / "archive" / "receipt_check.txt"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("{}", encoding="utf-8")
            sidecar.write_text("status=pass\n", encoding="utf-8")
            source = root / "report.json"
            source.write_text(
                json.dumps(
                    {
                        "receipt_path": "archive\\receipt.json",
                        "receipt_check_outputs": {"text": "archive\\receipt_check.txt"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_archived_path_portability_report([source], root=root)
            text = render_archived_path_portability_text(report)
            markdown = render_archived_path_portability_markdown(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["path_reference_count"], 2)
            self.assertEqual(report["windows_separator_count"], 2)
            self.assertEqual(report["failed_reference_count"], 0)
            self.assertIn("failed_reference_count=0", text)
            self.assertIn("archive/receipt.json", markdown.replace("\\", "/"))

    def test_report_rejects_missing_normalized_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "report.json"
            source.write_text(json.dumps({"receipt_path": "archive\\missing_receipt.json"}), encoding="utf-8")

            report = build_archived_path_portability_report([source], root=root)

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["failed_reference_count"], 1)
            self.assertTrue(any("does not resolve" in issue for issue in report["issues"]))

    def test_default_v448_archive_paths_are_portable(self) -> None:
        default_source = ROOT / "d" / "448" / "解释" / "promoted-handoff" / "promoted_training_scale_seed_handoff.json"
        if not default_source.is_file():
            self.skipTest(f"v448 archived handoff fixture is unavailable: {default_source}")

        report = build_archived_path_portability_report(DEFAULT_INPUTS, root=ROOT)

        self.assertEqual(report["status"], "pass")
        self.assertGreater(report["path_reference_count"], 0)
        self.assertGreater(report["windows_separator_count"], 0)
        self.assertEqual(report["failed_reference_count"], 0)

    def test_outputs_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "archive" / "receipt.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("{}", encoding="utf-8")
            source = root / "report.json"
            source.write_text(json.dumps({"receipt_path": "archive\\receipt.json"}), encoding="utf-8")
            report = build_archived_path_portability_report([source], root=root)
            out_dir = root / "out"

            outputs = write_archived_path_portability_outputs(report, out_dir)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_archived_path_portability.py"),
                    str(source),
                    "--root",
                    str(root),
                    "--out-dir",
                    str(root / "cli-out"),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertTrue((out_dir / CHECK_JSON_FILENAME).is_file())
            self.assertTrue((out_dir / CHECK_CSV_FILENAME).is_file())
            self.assertTrue((out_dir / CHECK_MARKDOWN_FILENAME).is_file())
            self.assertIn("References", (out_dir / CHECK_HTML_FILENAME).read_text(encoding="utf-8"))
            self.assertIn("status=pass", completed.stdout)
            self.assertIn("outputs=", completed.stdout)
            self.assertTrue(Path(outputs["json"]).is_file())


if __name__ == "__main__":
    unittest.main()
