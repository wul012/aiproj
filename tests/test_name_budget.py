from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from minigpt.name_budget import (
    build_name_report,
    scan_names,
    write_name_outputs,
)
from scripts.check_name_budget import main as cli_main


LONG_VAR = "PUBLIC_VARIABLE_NAME_THAT_EXCEEDS_FORTY_CHARS"
LONG_FUNC = "public_function_name_that_exceeds_forty_chars"
LONG_CLASS = "PublicClassNameThatDefinitelyExceedsFortyChars"
LONG_FIELD = "public_field_name_that_exceeds_forty_chars"


class NameBudgetTests(unittest.TestCase):
    def test_scan_public_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            source.mkdir()
            long_file = source / ("public_module_name_that_exceeds_forty_chars.py")
            long_file.write_text(
                "\n".join(
                    [
                        "from other import value as PUBLIC_IMPORT_ALIAS_THAT_EXCEEDS_FORTY_CHARS",
                        f"{LONG_VAR} = 1",
                        "_PRIVATE_VARIABLE_NAME_THAT_EXCEEDS_FORTY_CHARS = 2",
                        f"def {LONG_FUNC}():",
                        "    LOCAL_VARIABLE_NAME_THAT_EXCEEDS_FORTY_CHARS = 3",
                        f"class {LONG_CLASS}:",
                        f"    {LONG_FIELD}: int = 4",
                        "    _PRIVATE_FIELD_NAME_THAT_EXCEEDS_FORTY_CHARS = 5",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = scan_names(root)

        found = {(item["kind"], item["name"]) for item in result["items"]}
        self.assertEqual(result["errors"], [])
        self.assertIn(("filename", long_file.name), found)
        self.assertIn(("variable", LONG_VAR), found)
        self.assertIn(("function", LONG_FUNC), found)
        self.assertIn(("class", LONG_CLASS), found)
        self.assertIn(("field", LONG_FIELD), found)
        self.assertNotIn("PUBLIC_IMPORT_ALIAS_THAT_EXCEEDS_FORTY_CHARS", {name for _, name in found})
        self.assertNotIn("LOCAL_VARIABLE_NAME_THAT_EXCEEDS_FORTY_CHARS", {name for _, name in found})

    def test_line_moves_keep_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, f"{LONG_VAR} = 1\n")
            baseline = root / "baseline.json"
            first = build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)
            (root / "src" / "sample.py").write_text(f"\n\n{LONG_VAR} = 1\n", encoding="utf-8")
            second = build_name_report(project_root=root, baseline_path=baseline)

        self.assertEqual(first["status"], "pass")
        self.assertEqual(second["status"], "pass")
        self.assertEqual(second["summary"]["new_violation_count"], 0)

    def test_new_name_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, "value = 1\n")
            baseline = root / "baseline.json"
            build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)
            (root / "src" / "sample.py").write_text(f"{LONG_VAR} = 1\n", encoding="utf-8")

            report = build_name_report(project_root=root, baseline_path=baseline)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["new_violation_count"], 1)
        self.assertIn("new_name_violations", report["blockers"])

    def test_update_blocks_new(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, "value = 1\n")
            baseline = root / "baseline.json"
            build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)
            before = baseline.read_bytes()
            (root / "src" / "sample.py").write_text(f"{LONG_VAR} = 1\n", encoding="utf-8")

            report = build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)

            self.assertEqual(report["status"], "fail")
            self.assertFalse(report["summary"]["baseline_update_allowed"])
            self.assertEqual(baseline.read_bytes(), before)

    def test_subset_update_shrinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, f"{LONG_VAR} = 1\n")
            baseline = root / "baseline.json"
            build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)
            (root / "src" / "sample.py").write_text("value = 1\n", encoding="utf-8")

            report = build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)
            payload = json.loads(baseline.read_text(encoding="utf-8"))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["resolved_violation_count"], 1)
        self.assertEqual(payload["violation_count"], 0)
        self.assertEqual(payload["digests"], [])

    def test_cli_adopts_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = self._project(tmp, f"{LONG_VAR} = 1\n")
            out_dir = root / "out"
            code = cli_main(
                [
                    "--project-root",
                    str(root),
                    "--baseline",
                    "baseline.json",
                    "--out-dir",
                    str(out_dir),
                    "--update-baseline",
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue((root / "baseline.json").is_file())
            self.assertTrue((out_dir / "name_budget.json").is_file())

    def test_invalid_budget_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, f"{LONG_VAR} = 1\n")
            baseline = root / "baseline.json"
            build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)
            payload = json.loads(baseline.read_text(encoding="utf-8"))
            payload["max_name_length"] = 41
            baseline.write_text(json.dumps(payload), encoding="utf-8")

            report = build_name_report(project_root=root, baseline_path=baseline)

        self.assertEqual(report["status"], "fail")
        self.assertIn("baseline_budget_invalid", report["blockers"])

    def test_invalid_digests_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, f"{LONG_VAR} = 1\n")
            baseline = root / "baseline.json"
            build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)
            payload = json.loads(baseline.read_text(encoding="utf-8"))
            payload["digests"] = 42
            baseline.write_text(json.dumps(payload), encoding="utf-8")

            report = build_name_report(project_root=root, baseline_path=baseline)

        self.assertEqual(report["status"], "fail")
        self.assertIn("baseline_digests_invalid", report["blockers"])

    def test_html_has_empty_favicon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, "value = 1\n")
            baseline = root / "baseline.json"
            report = build_name_report(project_root=root, baseline_path=baseline, update_baseline=True)
            outputs = write_name_outputs(report, root / "out")

            html = Path(outputs["html"]).read_text(encoding="utf-8")

        self.assertIn('<link rel="icon" href="data:,">', html)

    @staticmethod
    def _project(tmp: str, source: str) -> Path:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "scripts").mkdir()
        (root / "src" / "sample.py").write_text(source, encoding="utf-8")
        return root


if __name__ == "__main__":
    unittest.main()
