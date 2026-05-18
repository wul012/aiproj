from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.report_utils import (  # noqa: E402
    count_available_artifacts,
    display_command,
    first_present,
    html_escape,
    list_of_dicts,
    make_artifact_row,
    make_artifact_rows,
    markdown_cell,
    number_or_default,
    number_or_none,
    write_csv_row,
    write_json_payload,
)


class ReportUtilsTests(unittest.TestCase):
    def test_artifact_rows_record_path_existence_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "report.json"
            missing = root / "missing.json"
            existing.write_text("{}", encoding="utf-8")

            rows = make_artifact_rows([("json", existing), ("missing", missing)])

            self.assertEqual(rows[0]["key"], "json")
            self.assertTrue(rows[0]["exists"])
            self.assertEqual(rows[0]["count"], 1)
            self.assertFalse(rows[1]["exists"])
            self.assertEqual(count_available_artifacts(rows), 1)

    def test_artifact_row_accepts_explicit_virtual_counts(self) -> None:
        row = make_artifact_row("variant_reports", "runs/variants", exists=True, count=3)

        self.assertEqual(row["path"], "runs\\variants" if sys.platform == "win32" else "runs/variants")
        self.assertTrue(row["exists"])
        self.assertEqual(row["count"], 3)

    def test_text_helpers_escape_markdown_html_and_command_parts(self) -> None:
        command = display_command(["python", "script name.py", 'say"hi'])

        self.assertIn('"script name.py"', command)
        self.assertIn('"say\\"hi"', command)
        self.assertEqual(markdown_cell("a|b\nc"), "a\\|b c")
        self.assertEqual(html_escape("<tag>"), "&lt;tag&gt;")

    def test_json_and_csv_writers_create_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_path = root / "nested" / "report.json"
            csv_path = root / "nested" / "report.csv"

            write_json_payload({"name": "MiniGPT", "items": [1, 2]}, json_path)
            write_csv_row({"name": "MiniGPT", "items": [1, 2]}, csv_path, ["name", "items"])

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertEqual(payload["items"], [1, 2])
            self.assertIn("MiniGPT", csv_text)
            self.assertIn("[1, 2]", csv_text)

    def test_list_of_dicts_filters_invalid_items(self) -> None:
        self.assertEqual(list_of_dicts([{"a": 1}, "bad", {"b": 2}]), [{"a": 1}, {"b": 2}])

    def test_first_present_returns_first_non_none_value(self) -> None:
        self.assertEqual(first_present(None, 0, "fallback"), 0)
        self.assertEqual(first_present(None, "", "fallback"), "")
        self.assertIsNone(first_present(None, None))

    def test_number_helpers_keep_none_and_default_semantics(self) -> None:
        self.assertEqual(number_or_none("3", int), 3)
        self.assertEqual(number_or_none("2.5"), 2.5)
        self.assertIsNone(number_or_none(""))
        self.assertIsNone(number_or_none(None))
        self.assertIsNone(number_or_none(True, int))
        self.assertEqual(number_or_default("bad", 7, int), 7)
        self.assertEqual(number_or_default("4.5", 0.0), 4.5)


if __name__ == "__main__":
    unittest.main()
