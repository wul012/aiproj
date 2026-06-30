from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt.report_utils import (
    CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON,
    archived_reference_path,
    as_dict,
    ci_boundary_plan_check_ready_regression_count,
    ci_regression_reason_count,
    count_available_artifacts,
    csv_cell,
    display_command,
    first_present,
    format_mapping,
    html_escape,
    list_of_dicts,
    list_of_strs,
    locate_upstream_report,
    make_artifact_row,
    make_artifact_rows,
    markdown_cell,
    number_or_default,
    number_or_none,
    positive_int_mapping,
    read_json_object,
    resolve_archived_reference_path,
    string_list,
    write_csv_row,
    write_json_payload,
)


class ReportUtilsHelperTests(unittest.TestCase):
    def test_report_utils_module_exists_in_src_layout(self) -> None:
        self.assertTrue((ROOT / "src" / "minigpt" / "report_utils.py").is_file())

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

        self.assertEqual(Path(row["path"]), Path("runs/variants"))
        self.assertTrue(row["exists"])
        self.assertEqual(row["count"], 3)

    def test_archived_reference_path_accepts_windows_separators(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "d" / "448" / "evidence" / "receipt.json"
            target.parent.mkdir(parents=True)
            target.write_text("{}", encoding="utf-8")

            archived = "d\\448\\evidence\\receipt.json"

            self.assertEqual(archived_reference_path(archived), Path("d") / "448" / "evidence" / "receipt.json")
            self.assertEqual(resolve_archived_reference_path(archived, target.parent), target)
            self.assertIsNone(resolve_archived_reference_path("", target.parent))

    def test_json_readers_and_writers_create_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_path = root / "nested" / "report.json"
            object_path = root / "nested" / "object.json"

            write_json_payload({"name": "MiniGPT", "items": [1, 2]}, json_path)
            object_path.write_text('{"status": "pass"}', encoding="utf-8")

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["items"], [1, 2])
            self.assertEqual(read_json_object(object_path, description="fixture"), {"status": "pass"})
            self.assertEqual(locate_upstream_report(root / "nested", "report.json"), json_path)
            self.assertEqual(locate_upstream_report(json_path, "ignored.json"), json_path)

    def test_read_json_object_rejects_non_object_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "items.json"
            path.write_text("[1, 2]", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "fixture must be a JSON object"):
                read_json_object(path, description="fixture")

    def test_csv_and_text_helpers_preserve_report_safe_cells(self) -> None:
        command = display_command(["python", "script name.py", 'say"hi'])

        self.assertIn('"script name.py"', command)
        self.assertIn('"say\\"hi"', command)
        self.assertEqual(markdown_cell("a|b\nc"), "a\\|b c")
        self.assertEqual(html_escape("<tag>"), "&lt;tag&gt;")
        self.assertEqual(csv_cell({"b": 2, "a": 1}), '{"a": 1, "b": 2}')
        self.assertEqual(csv_cell(None), "")

    def test_csv_writer_uses_declared_field_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "nested" / "report.csv"

            write_csv_row({"name": "MiniGPT", "items": [1, 2]}, csv_path, ["name", "items"])

            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertTrue(csv_text.startswith("name,items"))
            self.assertIn("MiniGPT", csv_text)
            self.assertIn("[1, 2]", csv_text)

    def test_collection_helpers_filter_unexpected_shapes(self) -> None:
        self.assertEqual(as_dict({"a": 1}), {"a": 1})
        self.assertEqual(as_dict(["bad"]), {})
        self.assertEqual(list_of_dicts([{"a": 1}, "bad", {"b": 2}]), [{"a": 1}, {"b": 2}])
        self.assertEqual(list_of_dicts({"bad": True}), [])
        self.assertEqual(list_of_strs(["a", 2]), ["a", "2"])
        self.assertEqual(list_of_strs("bad"), [])
        self.assertEqual(string_list(["a", 2]), ["a", "2"])
        self.assertEqual(string_list("bad"), [])

    def test_first_present_and_number_helpers_keep_none_and_default_semantics(self) -> None:
        self.assertEqual(first_present(None, 0, "fallback"), 0)
        self.assertEqual(first_present(None, "", "fallback"), "")
        self.assertIsNone(first_present(None, None))
        self.assertEqual(number_or_none("3", int), 3)
        self.assertEqual(number_or_none("2.5"), 2.5)
        self.assertIsNone(number_or_none(""))
        self.assertIsNone(number_or_none(None))
        self.assertIsNone(number_or_none(True, int))
        self.assertEqual(number_or_default("bad", 7, int), 7)
        self.assertEqual(number_or_default("4.5", 0.0), 4.5)

    def test_positive_int_mapping_filters_and_formats_reason_counts(self) -> None:
        counts = positive_int_mapping({" b ": "2", "a": 1, "zero": 0, "bad": "x", "": 4})

        self.assertEqual(counts, {"a": 1, "b": 2})
        self.assertEqual(format_mapping(counts), "a:1, b:2")
        self.assertEqual(format_mapping({}), "none")
        self.assertEqual(positive_int_mapping(["bad"]), {})

    def test_ci_regression_reason_helpers_read_maps_and_numeric_overrides(self) -> None:
        counts = {
            "boundary_gate_plan_check_not_ready": "2",
            CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON: 1,
            "ignored-zero": 0,
        }

        self.assertEqual(
            ci_regression_reason_count(CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON, counts),
            1,
        )
        self.assertEqual(ci_regression_reason_count("missing", counts), 0)
        self.assertEqual(ci_regression_reason_count("", counts), 0)
        self.assertEqual(ci_boundary_plan_check_ready_regression_count(counts), 2)
        self.assertEqual(ci_boundary_plan_check_ready_regression_count("3", counts), 3)
        self.assertEqual(ci_boundary_plan_check_ready_regression_count("-1", counts), 0)


if __name__ == "__main__":
    unittest.main()
