from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.source_encoding_hygiene import build_source_encoding_report, render_source_encoding_html, write_source_encoding_outputs


SOURCE_ROOTS = [ROOT / "src", ROOT / "scripts", ROOT / "tests"]
BOM = b"\xef\xbb\xbf"


class SourceEncodingHygieneTests(unittest.TestCase):
    def test_python_sources_do_not_start_with_bom(self) -> None:
        offenders = [
            str(path.relative_to(ROOT))
            for root in SOURCE_ROOTS
            for path in root.rglob("*.py")
            if path.is_file() and path.read_bytes().startswith(BOM)
        ]

        self.assertEqual(offenders, [], f"UTF-8 BOM is not allowed in Python sources: {', '.join(offenders)}")

    def test_report_detects_bom_and_syntax_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean = root / "clean.py"
            bom = root / "bom.py"
            broken = root / "broken.py"
            clean.write_text("def ok():\n    return 1\n", encoding="utf-8")
            bom.write_bytes(BOM + b"def ok():\n    return 1\n")
            broken.write_text("def broken(:\n    pass\n", encoding="utf-8")

            report = build_source_encoding_report([clean, bom, broken], project_root=root, generated_at="2026-05-15T00:00:00Z")

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["bom_count"], 1)
            self.assertEqual(report["summary"]["syntax_error_count"], 1)
            self.assertEqual(report["summary"]["bom_paths"], ["bom.py"])
            self.assertEqual(report["summary"]["syntax_error_paths"], ["broken.py"])

    def test_outputs_and_html_escape(self) -> None:
        report = build_source_encoding_report([], title="Encoding <gate>", generated_at="2026-05-15T00:00:00Z")
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_source_encoding_outputs(report, Path(tmp))
            html = render_source_encoding_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["status"], "pass")
            self.assertIn("parse_error", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("source_count", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Encoding &lt;gate&gt;", html)
            self.assertNotIn("Encoding <gate>", html)

    def test_cli_fails_on_bom_when_fail_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "bom.py"
            source.write_bytes(BOM + b"print('x')\n")

            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts" / "check_source_encoding.py"), str(source), "--out-dir", str(root / "out")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("bom_count=1", result.stdout)
            self.assertTrue((root / "out" / "source_encoding_hygiene.json").exists())


if __name__ == "__main__":
    unittest.main()
