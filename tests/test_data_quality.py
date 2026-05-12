from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.data_prep import build_prepared_dataset
from minigpt.data_quality import build_dataset_quality_report, sha256_text, write_dataset_quality_json, write_dataset_quality_svg


class DataQualityTests(unittest.TestCase):
    def test_sha256_text_is_stable(self) -> None:
        self.assertEqual(sha256_text("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_quality_report_detects_duplicate_sources_and_repeated_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repeated = "重复的一整行文本用于检测质量\n重复的一整行文本用于检测质量\n"
            (root / "a.txt").write_text(repeated, encoding="utf-8")
            (root / "b.txt").write_text(repeated, encoding="utf-8")
            dataset = build_prepared_dataset([root])

            report = build_dataset_quality_report(dataset, min_total_chars=10, min_source_chars=5)

            codes = {issue["code"] for issue in report["issues"]}
            self.assertEqual(report["status"], "warn")
            self.assertIn("duplicate_source", codes)
            self.assertIn("repeated_line", codes)
            self.assertEqual(len(report["fingerprint"]), 64)

    def test_quality_report_can_pass_for_reasonable_small_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("人工智能模型训练需要数据质量记录。\n不同句子可以减少重复。", encoding="utf-8")
            dataset = build_prepared_dataset([root])

            report = build_dataset_quality_report(dataset, min_total_chars=10, min_source_chars=5)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["warning_count"], 0)

    def test_write_quality_outputs_json_and_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("MiniGPT dataset quality", encoding="utf-8")
            dataset = build_prepared_dataset([root])
            report = build_dataset_quality_report(dataset, min_total_chars=10, min_source_chars=5)

            write_dataset_quality_json(report, root / "dataset_quality.json")
            write_dataset_quality_svg(report, root / "dataset_quality.svg")

            self.assertEqual(json.loads((root / "dataset_quality.json").read_text(encoding="utf-8"))["schema_version"], 1)
            self.assertIn("<svg", (root / "dataset_quality.svg").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
