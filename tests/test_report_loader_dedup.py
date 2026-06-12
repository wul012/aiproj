from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.report_loader_dedup import (
    MIGRATED_MODULES,
    build_report_loader_dedup_report,
    resolve_exit_code,
    write_report_loader_dedup_outputs,
)
from scripts.generate_report_loader_dedup_v1140 import main as cli_main


class ReportLoaderDedupTests(unittest.TestCase):
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
            exit_code = cli_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-dedup-ready", "--force"])

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
