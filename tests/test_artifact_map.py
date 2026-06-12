from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.artifact_map import build_artifact_map_report, resolve_exit_code, write_artifact_map_outputs
from scripts.devtools.build_artifact_map_v1134 import main as cli_main


class ArtifactMapTests(unittest.TestCase):
    def test_artifact_map_passes_for_complete_version_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_version(root, "1130", with_summary=True, with_screenshot=True)
            report = build_artifact_map_report(root)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["scanned_version_count"], 1)
        self.assertEqual(report["summary"]["ready_version_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_complete=True), 0)

    def test_artifact_map_watches_missing_screenshot_or_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_version(root, "1131", with_summary=False, with_screenshot=True)
            _write_version(root, "1130", with_summary=True, with_screenshot=False)
            report = build_artifact_map_report(root)

        self.assertEqual(report["status"], "watch")
        self.assertEqual(report["summary"]["missing_summary_count"], 1)
        self.assertEqual(report["summary"]["missing_screenshot_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_complete=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_version(root, "1130", with_summary=True, with_screenshot=True)
            report = build_artifact_map_report(root)
            outputs = write_artifact_map_outputs(report, root / "out")
            exit_code = cli_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-ready", "--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})


def _write_version(root: Path, version: str, *, with_summary: bool, with_screenshot: bool) -> None:
    report_dir = root / "f" / version / "解释" / "report"
    report_dir.mkdir(parents=True)
    (report_dir / "report.json").write_text("{}\n", encoding="utf-8")
    (report_dir / "report.csv").write_text("status\npass\n", encoding="utf-8")
    (report_dir / "report.md").write_text("# report\n", encoding="utf-8")
    (report_dir / "report.html").write_text("<html></html>\n", encoding="utf-8")
    if with_summary:
        (root / "f" / version / "解释" / "说明.md").write_text("# summary\n", encoding="utf-8")
    if with_screenshot:
        image_dir = root / "f" / version / "图片"
        image_dir.mkdir(parents=True)
        (image_dir / "screen.png").write_bytes(b"png")


if __name__ == "__main__":
    unittest.main()
