from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.publication_naming_readability import (
    LONG_NAME_WARN,
    build_publication_naming_readability_report,
    resolve_exit_code,
    write_publication_naming_readability_outputs,
)
from minigpt.readability_report_artifacts import render_readability_html, render_readability_markdown, render_readability_text
from scripts.publication.check_publication_naming_readability_v1130 import main as cli_main


class PublicationNamingReadabilityTests(unittest.TestCase):
    def test_report_flags_legacy_repeated_receipt_index_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "scripts" / "build_randomized_holdout_publication_receipt_index_receipt_index_v999.py"
            target.parent.mkdir(parents=True)
            target.write_text("print('legacy')\n", encoding="utf-8")
            report = build_publication_naming_readability_report(root, generated_at="2026-06-12T00:00:00Z")

        self.assertEqual(report["status"], "watch")
        self.assertEqual(report["decision"], "publication_short_alias_policy_ready")
        self.assertEqual(report["summary"]["repeated_receipt_index_file_count"], 1)
        self.assertTrue(report["summary"]["policy_ready"])
        self.assertEqual(resolve_exit_code(report, require_policy_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_clean_new_names=True), 1)

    def test_short_names_do_not_create_watch_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "scripts" / "publication" / "build_pub_receipt_review_v1130.py"
            target.parent.mkdir(parents=True)
            target.write_text("print('short')\n", encoding="utf-8")
            report = build_publication_naming_readability_report(root)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["repeated_receipt_index_file_count"], 0)
        self.assertLess(len(target.name), LONG_NAME_WARN)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src" / "minigpt" / "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v999.py"
            target.parent.mkdir(parents=True)
            target.write_text("VALUE = 1\n", encoding="utf-8")
            out_dir = root / "out"
            report = build_publication_naming_readability_report(root)
            outputs = write_publication_naming_readability_outputs(report, out_dir)
            exit_code = cli_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-policy-ready", "--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("policy_ready=True", render_readability_text(report))
        self.assertIn("Naming Pressure Rows", render_readability_markdown(report, row_title="Naming Pressure Rows"))
        self.assertIn("MiniGPT publication naming", render_readability_html(report))


if __name__ == "__main__":
    unittest.main()
