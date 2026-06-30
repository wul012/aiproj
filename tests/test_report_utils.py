from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt.reports.utils import write_output_bundle


class ReportUtilsTests(unittest.TestCase):
    def test_active_engineering_report_writers_use_shared_output_bundle(self) -> None:
        owner_path_targets = (
            ROOT / "src" / "minigpt" / "source_encoding_hygiene.py",
            ROOT / "src" / "minigpt" / "ci_workflow_hygiene_artifacts.py",
            ROOT / "src" / "minigpt" / "test_coverage_report.py",
            ROOT / "scripts" / "_engineering_health.py",
        )

        for path in owner_path_targets:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn("minigpt.reports.utils", text)
                self.assertIn("write_output_bundle", text)

        base_artifacts = ROOT / "src" / "minigpt" / "readability_report_artifacts.py"
        base_text = base_artifacts.read_text(encoding="utf-8")
        self.assertIn("write_output_bundle", base_text)
        self.assertIn("minigpt.report_utils", base_text)
        self.assertNotIn("minigpt.reports.utils", base_text)

    def test_reports_utils_stays_a_thin_report_utils_facade(self) -> None:
        path = ROOT / "src" / "minigpt" / "reports" / "utils.py"
        text = path.read_text(encoding="utf-8")

        self.assertIn("from minigpt.report_utils import", text)
        self.assertNotIn("from minigpt.reports import", text)
        self.assertNotIn("import minigpt.reports", text)

    def test_write_output_bundle_writes_named_outputs_and_returns_paths(self) -> None:
        self.assertTrue((ROOT / "src" / "minigpt" / "report_utils.py").is_file())

        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_output_bundle(
                tmp,
                {"text": "report.txt", "nested": "nested/report.md"},
                {
                    "text": lambda path: path.write_text("plain", encoding="utf-8"),
                    "nested": lambda path: path.write_text("# title\n", encoding="utf-8"),
                },
            )

            root = Path(tmp)
            self.assertEqual(set(outputs), {"text", "nested"})
            self.assertEqual(Path(outputs["text"]), root / "report.txt")
            self.assertEqual((root / "report.txt").read_text(encoding="utf-8"), "plain")
            self.assertEqual((root / "nested" / "report.md").read_text(encoding="utf-8"), "# title\n")

    def test_write_output_bundle_rejects_mismatched_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "missing writers: markdown"):
                write_output_bundle(
                    tmp,
                    {"json": "report.json", "markdown": "report.md"},
                    {"json": lambda path: path.write_text("{}", encoding="utf-8")},
                )

            with self.assertRaisesRegex(ValueError, "missing filenames: html"):
                write_output_bundle(
                    tmp,
                    {"json": "report.json"},
                    {
                        "json": lambda path: path.write_text("{}", encoding="utf-8"),
                        "html": lambda path: path.write_text("<html></html>", encoding="utf-8"),
                    },
                )


if __name__ == "__main__":
    unittest.main()
