from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.test_coverage_report import (  # noqa: E402
    build_test_coverage_report,
    render_test_coverage_html,
    render_test_coverage_markdown,
    write_test_coverage_outputs,
)


class TestCoverageReportTests(unittest.TestCase):
    def test_builds_summary_from_coverage_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage_json = root / "coverage.json"
            coverage_json.write_text(json.dumps(_coverage_payload(root), ensure_ascii=False, indent=2), encoding="utf-8")

            report = build_test_coverage_report(coverage_json, project_root=root, generated_at="2026-05-18T00:00:00Z")

            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["summary"]["decision"], "record_coverage_baseline")
            self.assertEqual(report["summary"]["status"], "pass")
            self.assertEqual(report["summary"]["line_coverage_percent"], 80.0)
            self.assertFalse(report["summary"]["threshold_enabled"])
            self.assertIsNone(report["summary"]["fail_under"])
            self.assertEqual(report["summary"]["coverage_gap"], 0.0)
            self.assertEqual(report["summary"]["file_count"], 2)
            self.assertEqual(report["files"][0]["path"], "src/minigpt/a.py")

    def test_fail_under_passes_when_coverage_meets_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage_json = root / "coverage.json"
            coverage_json.write_text(json.dumps(_coverage_payload(root), ensure_ascii=False), encoding="utf-8")

            report = build_test_coverage_report(coverage_json, project_root=root, fail_under=75)

            self.assertEqual(report["summary"]["status"], "pass")
            self.assertEqual(report["summary"]["decision"], "continue_with_coverage_gate")
            self.assertTrue(report["summary"]["threshold_enabled"])
            self.assertEqual(report["summary"]["fail_under"], 75.0)
            self.assertEqual(report["summary"]["coverage_gap"], 0.0)
            self.assertIn("meets the configured fail-under gate", " ".join(report["recommendations"]))

    def test_fail_under_fails_when_coverage_is_below_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage_json = root / "coverage.json"
            coverage_json.write_text(json.dumps(_coverage_payload(root), ensure_ascii=False), encoding="utf-8")

            report = build_test_coverage_report(coverage_json, project_root=root, fail_under=82.5)

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["decision"], "improve_test_coverage")
            self.assertTrue(report["summary"]["threshold_enabled"])
            self.assertEqual(report["summary"]["fail_under"], 82.5)
            self.assertEqual(report["summary"]["coverage_gap"], 2.5)
            self.assertIn("below the fail-under gate", " ".join(report["recommendations"]))

    def test_rejects_invalid_fail_under_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage_json = root / "coverage.json"
            coverage_json.write_text(json.dumps(_coverage_payload(root), ensure_ascii=False), encoding="utf-8")

            with self.assertRaises(ValueError):
                build_test_coverage_report(coverage_json, project_root=root, fail_under=101)

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage_json = root / "coverage.json"
            coverage_json.write_text(json.dumps(_coverage_payload(root), ensure_ascii=False), encoding="utf-8")
            report = build_test_coverage_report(coverage_json, project_root=root, title="Coverage <report>")

            outputs = write_test_coverage_outputs(report, root / "out")
            markdown = render_test_coverage_markdown(report)
            html = render_test_coverage_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("line_coverage_percent", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("record_coverage_baseline", markdown)
            self.assertIn("Coverage gap", markdown)
            self.assertIn("Coverage &lt;report&gt;", html)
            self.assertNotIn("Coverage <report>", html)


def _coverage_payload(root: Path) -> dict:
    return {
        "meta": {"version": "7.12.0", "format": 3},
        "files": {
            str(root / "src" / "minigpt" / "a.py"): {
                "summary": {
                    "covered_lines": 8,
                    "num_statements": 10,
                    "missing_lines": 2,
                    "percent_covered": 80.0,
                }
            },
            str(root / "src" / "minigpt" / "b.py"): {
                "summary": {
                    "covered_lines": 4,
                    "num_statements": 5,
                    "missing_lines": 1,
                    "percent_covered": 80.0,
                }
            },
        },
        "totals": {
            "covered_lines": 12,
            "num_statements": 15,
            "missing_lines": 3,
            "percent_covered": 80.0,
        },
    }


if __name__ == "__main__":
    unittest.main()
