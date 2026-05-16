from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.data_prep import build_prepared_dataset, write_prepared_dataset
from minigpt import dataset_card_artifacts
from minigpt import dataset_card as dataset_card_facade
from minigpt.dataset_card import (
    build_dataset_card,
    render_dataset_card_html,
    render_dataset_card_markdown,
    write_dataset_card_outputs,
)


class DatasetCardTests(unittest.TestCase):
    def make_dataset_dir(self, root: Path, *, duplicate: bool = False, description: str = "demo dataset") -> Path:
        source = root / "sources"
        source.mkdir()
        if duplicate:
            text = "重复的一整行文本用于检测质量\n重复的一整行文本用于检测质量\n"
            (source / "a.txt").write_text(text, encoding="utf-8")
            (source / "b.txt").write_text(text, encoding="utf-8")
        else:
            lines = [
                "人工智能模型训练需要数据质量记录，方便后续复现实验。",
                "不同句子可以减少重复，帮助学习项目观察语料变化。",
                "这个数据集只用于 MiniGPT 教学实验，不代表真实生产数据。",
                "版本说明记录来源、指纹、质量状态和输出文件路径。",
                "数据卡进一步说明预期用途、限制和质量告警边界。",
                "训练脚本可以从准备好的 corpus.txt 读取统一语料。",
                "质量报告会提示重复来源、过短文本和重复行。",
                "这些轻量检查不能替代人工审核、授权确认和安全评估。",
                "项目通过小数据集理解语言模型训练与治理证据链。",
            ]
            (source / "a.txt").write_text("\n".join(lines), encoding="utf-8")
        dataset = build_prepared_dataset([source])
        out_dir = root / "datasets" / "demo-zh" / "v1"
        write_prepared_dataset(
            dataset,
            out_dir,
            dataset_name="demo-zh",
            dataset_version="v1",
            dataset_description=description,
            source_roots=[source],
        )
        return out_dir

    def test_build_dataset_card_summarizes_dataset_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self.make_dataset_dir(Path(tmp))

            card = build_dataset_card(dataset_dir, generated_at="2026-05-13T00:00:00Z")

            self.assertEqual(card["schema_version"], 1)
            self.assertEqual(card["dataset"]["id"], "demo-zh@v1")
            self.assertEqual(card["summary"]["readiness_status"], "ready")
            self.assertEqual(card["summary"]["quality_status"], "pass")
            self.assertEqual(card["summary"]["source_count"], 1)
            self.assertEqual(len(card["summary"]["short_fingerprint"]), 12)
            self.assertTrue(card["summary"]["output_text_exists"])
            self.assertTrue(card["provenance"]["sources"])
            self.assertEqual(card["quality"]["issue_codes"], [])
            self.assertTrue(any(item["key"] == "dataset_version" and item["exists"] for item in card["artifacts"]))
            self.assertTrue(card["recommendations"])
            self.assertEqual(card["warnings"], [])

    def test_build_dataset_card_marks_quality_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self.make_dataset_dir(Path(tmp), duplicate=True)

            card = build_dataset_card(dataset_dir)

            self.assertEqual(card["summary"]["readiness_status"], "review")
            self.assertEqual(card["summary"]["quality_status"], "warn")
            self.assertIn("duplicate_source", card["quality"]["issue_codes"])
            self.assertIn("repeated_line", card["quality"]["issue_codes"])
            self.assertGreater(card["summary"]["warning_count"], 0)
            self.assertTrue(any("Inspect quality issue codes" in item for item in card["recommendations"]))

    def test_write_dataset_card_outputs_and_renderers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self.make_dataset_dir(Path(tmp), description="<demo> dataset")
            card = build_dataset_card(dataset_dir, title="<Dataset Card>")

            outputs = write_dataset_card_outputs(card, dataset_dir)
            markdown = render_dataset_card_markdown(card)
            html = render_dataset_card_html(card)

            self.assertEqual(set(outputs), {"json", "markdown", "html"})
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["dataset"]["id"], "demo-zh@v1")
            saved_card = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertTrue(any(item["key"] == "dataset_card_html" and item["exists"] for item in saved_card["artifacts"]))
            self.assertIn("## Intended Use", markdown)
            self.assertIn("## Quality", markdown)
            self.assertIn("&lt;Dataset Card&gt;", html)
            self.assertIn("&lt;demo&gt; dataset", html)
            self.assertNotIn("<h1><Dataset Card>", html)

    def test_build_dataset_card_records_missing_inputs_as_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "empty-dataset"
            dataset_dir.mkdir()

            card = build_dataset_card(dataset_dir)

            self.assertEqual(card["summary"]["readiness_status"], "incomplete")
            self.assertTrue(card["warnings"])
            self.assertIn("Resolve missing or invalid dataset evidence files", " ".join(card["recommendations"]))

    def test_facade_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(dataset_card_facade.write_dataset_card_outputs, dataset_card_artifacts.write_dataset_card_outputs)
        self.assertIs(dataset_card_facade.render_dataset_card_html, dataset_card_artifacts.render_dataset_card_html)
        self.assertIs(dataset_card_facade.render_dataset_card_markdown, dataset_card_artifacts.render_dataset_card_markdown)


if __name__ == "__main__":
    unittest.main()
