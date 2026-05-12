from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.data_prep import (
    build_dataset_report,
    build_prepared_dataset,
    discover_text_files,
    normalize_text,
    write_prepared_dataset,
)


class DataPrepTests(unittest.TestCase):
    def test_normalize_text_strips_trailing_space_and_newlines(self) -> None:
        self.assertEqual(normalize_text(" a  \r\nb\t \n\n"), " a\nb")

    def test_discover_text_files_reads_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "skip.md").write_text("skip", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "b.txt").write_text("b", encoding="utf-8")

            files = discover_text_files([root], recursive=True)

            self.assertEqual([path.name for path in files], ["a.txt", "b.txt"])

    def test_build_prepared_dataset_combines_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.txt").write_text("hello\n", encoding="utf-8")
            (root / "two.txt").write_text("world\n", encoding="utf-8")

            dataset = build_prepared_dataset([root])

            self.assertIn("hello\n\nworld", dataset.text)
            self.assertEqual(len(dataset.sources), 2)
            self.assertGreater(dataset.char_count, 0)

    def test_build_dataset_report_contains_common_chars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.txt").write_text("aaa b", encoding="utf-8")
            dataset = build_prepared_dataset([root])

            report = build_dataset_report(dataset, output_text="corpus.txt")

            self.assertEqual(report["source_count"], 1)
            self.assertEqual(report["output_text"], "corpus.txt")
            self.assertEqual(report["most_common_chars"][0]["char"], "a")

    def test_write_prepared_dataset_outputs_text_json_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            source.write_text("MiniGPT data", encoding="utf-8")
            dataset = build_prepared_dataset([source])

            outputs = write_prepared_dataset(dataset, root / "out")

            self.assertTrue(Path(outputs["text"]).exists())
            report = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(report["source_count"], 1)
            self.assertIn("<svg", Path(outputs["svg"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
