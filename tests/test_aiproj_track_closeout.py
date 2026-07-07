from __future__ import annotations

import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests._bootstrap import ROOT

from minigpt.aiproj_track_closeout import (
    build_aiproj_track_closeout_report,
    render_aiproj_track_closeout_html,
    render_aiproj_track_closeout_markdown,
    write_aiproj_track_closeout_outputs,
)
from scripts.check_aiproj_track_closeout import main as cli_main


class AiprojTrackCloseoutTests(unittest.TestCase):
    def test_current_repository_closeout_passes(self) -> None:
        report = build_aiproj_track_closeout_report(project_root=ROOT, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "aiproj_track_closeout_ready")
        self.assertEqual(report["summary"]["evidence_doc_count"], 6)
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertTrue(report["summary"]["no_promotion_boundary_ready"])
        self.assertTrue(report["summary"]["final_evidence_ready"])
        self.assertTrue(report["summary"]["ci_closeout_gate_ready"])

    def test_missing_final_evidence_term_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_minimal_closeout_tree(root)
            final_doc = root / "docs" / "aiproj-track-final-evidence.md"
            final_doc.write_text(
                final_doc.read_text(encoding="utf-8").replace("docs/aiproj-track-a4-code-health.md", "missing-a4-doc"),
                encoding="utf-8",
            )

            report = build_aiproj_track_closeout_report(project_root=root, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["status"], "fail")
        self.assertIn(
            "final_evidence:term:docs/aiproj-track-a4-code-health.md",
            {item["check_id"] for item in report["checks"] if item["status"] == "fail"},
        )

    def test_missing_no_promotion_boundary_term_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_minimal_closeout_tree(root)
            boundary = root / "docs" / "no-promotion-boundary.md"
            boundary.write_text(
                boundary.read_text(encoding="utf-8").replace("approved_for_promotion=False", ""), encoding="utf-8"
            )

            report = build_aiproj_track_closeout_report(project_root=root, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["status"], "fail")
        self.assertIn(
            "no_promotion:term:approved_for_promotion=False",
            {item["check_id"] for item in report["checks"] if item["status"] == "fail"},
        )

    def test_outputs_and_cli_are_wired(self) -> None:
        with TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            out_dir = Path(tmp) / "out"
            exit_code = cli_main(["--out-dir", str(out_dir)])
            outputs = write_aiproj_track_closeout_outputs(
                build_aiproj_track_closeout_report(project_root=ROOT, generated_at="2026-01-01T00:00:00Z"),
                Path(tmp) / "manual",
            )
            cli_output_exists = (out_dir / "aiproj_track_closeout.json").is_file()

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
        self.assertTrue(cli_output_exists)
        self.assertIn("aiproj Production-Excellence Closeout", render_aiproj_track_closeout_markdown({"summary": {}}))
        self.assertIn("MiniGPT aiproj closeout", render_aiproj_track_closeout_html({"summary": {}}))


def _copy_minimal_closeout_tree(root: Path) -> None:
    paths = [
        "README.md",
        "START_HERE.md",
        ".github/workflows/ci.yml",
        "docs/README.md",
        "docs/script-entrypoints.md",
        "docs/no-promotion-boundary.md",
        "docs/aiproj-track-final-evidence.md",
        "docs/aiproj-track-a0-census.md",
        "docs/aiproj-track-a1-static-analysis.md",
        "docs/aiproj-track-a2-coverage.md",
        "docs/aiproj-track-a3-honest-measurement.md",
        "docs/aiproj-track-a3-artifact-schema-guard.md",
        "docs/aiproj-track-a4-code-health.md",
    ]
    for relative in paths:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
