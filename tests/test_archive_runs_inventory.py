from __future__ import annotations

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from scripts.check_archive_runs_inventory import (
    InventoryBudget,
    build_inventory,
    main as inventory_main,
    write_outputs,
)


class ArchiveRunsInventoryTests(unittest.TestCase):
    def test_inventory_records_archive_and_runs_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a", "b", "c", "d", "e", "f", "runs"):
                (root / name).mkdir()
            (root / "e" / "sample.txt").write_text("x" * 2048, encoding="utf-8")
            report = build_inventory(
                root,
                generated_at="2026-07-06T00:00:00Z",
                budget=InventoryBudget(archive_total_warning_mb=1.0, archive_root_warning_mb=1.0, runs_warning_mb=1.0),
            )

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["warning_only"])
        self.assertEqual(report["summary"]["archive_root_count"], 6)
        self.assertEqual(report["summary"]["run_root_count"], 1)
        self.assertEqual(len(report["rows"]), 7)
        self.assertEqual(report["summary"]["warning_count"], 0)

    def test_inventory_is_warning_only_when_budget_is_exceeded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a", "b", "c", "d", "e", "f", "runs"):
                (root / name).mkdir()
            (root / "e" / "large.bin").write_bytes(b"x" * 2048)
            report = build_inventory(
                root,
                budget=InventoryBudget(archive_total_warning_mb=0.0001, archive_root_warning_mb=0.0001, runs_warning_mb=0.0001),
            )

        self.assertEqual(report["status"], "pass")
        self.assertGreater(report["summary"]["warning_count"], 0)
        self.assertEqual(report["decision"], "archive_runs_inventory_recorded_with_warnings")

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a", "b", "c", "d", "e", "f", "runs"):
                (root / name).mkdir()
            report = build_inventory(root)
            outputs = write_outputs(report, root / "out")
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                exit_code = inventory_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--force"])

            cli_files = sorted((root / "cli-out").glob("*"))
            output_paths_exist = all(Path(path).exists() for path in outputs.values())

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(output_paths_exist)
        self.assertEqual({path.suffix for path in cli_files}, {".json", ".csv", ".txt", ".md", ".html"})
        self.assertIn("warning_only=True", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
