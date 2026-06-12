from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.publication_receipt_template import (
    REQUIRED_SECTIONS,
    build_publication_receipt_template_report,
    resolve_exit_code,
    write_publication_receipt_template_outputs,
)
from scripts.publication.check_pub_receipt_template_v1132 import main as cli_main


class PublicationReceiptTemplateTests(unittest.TestCase):
    def test_template_report_passes_when_sections_and_layers_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_template_fixture(root)
            report = build_publication_receipt_template_report(root, generated_at="2026-06-12T00:00:00Z")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["ready_section_count"], len(REQUIRED_SECTIONS))
        self.assertTrue(report["summary"]["template_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_template_report_fails_when_section_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_template_fixture(root, omit="## Verification")
            report = build_publication_receipt_template_report(root)

        self.assertEqual(report["status"], "fail")
        self.assertGreater(report["summary"]["failed_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_template_fixture(root)
            report = build_publication_receipt_template_report(root)
            outputs = write_publication_receipt_template_outputs(report, root / "out")
            exit_code = cli_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-pass", "--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})


def _write_template_fixture(root: Path, *, omit: str | None = None) -> None:
    (root / "scripts" / "publication").mkdir(parents=True)
    (root / "scripts" / "devtools").mkdir(parents=True)
    docs = root / "docs"
    docs.mkdir(parents=True)
    sections = [section for section in REQUIRED_SECTIONS if section != omit]
    (docs / "publication-receipt-template.md").write_text("\n\n".join(sections), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
