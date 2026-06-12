from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from minigpt.report_utils import locate_upstream_report, read_json_object


class ReportLoadingTests(unittest.TestCase):
    def test_locate_upstream_report_resolves_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = root / "example.json"

            self.assertEqual(locate_upstream_report(root, "example.json"), expected)

    def test_locate_upstream_report_keeps_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "already-selected.json"

            self.assertEqual(locate_upstream_report(path, "example.json"), path)

    def test_read_json_object_accepts_bom_prefixed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.json"
            path.write_text('{"status": "pass"}', encoding="utf-8-sig")

            self.assertEqual(read_json_object(path, description="sample report"), {"status": "pass"})

    def test_read_json_object_rejects_non_dict_with_exact_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.json"
            path.write_text('["not", "a", "dict"]', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "sample report must be a JSON object"):
                read_json_object(path, description="sample report")


if __name__ == "__main__":
    unittest.main()
