from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import generation_quality, generation_quality_artifacts
from minigpt.generation_quality import (
    build_generation_quality_report,
    render_generation_quality_html,
    write_generation_quality_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_eval_suite(root: Path, *, title_case: str = "good") -> Path:
    payload = {
        "schema_version": 1,
        "checkpoint": str(root / "checkpoint.pt"),
        "tokenizer": str(root / "tokenizer.json"),
        "suite": str(root / "prompts.json"),
        "case_count": 3,
        "avg_continuation_chars": 10,
        "avg_unique_chars": 6,
        "results": [
            {
                "name": title_case,
                "prompt": "人工智能",
                "generated": "人工智能模型可以学习数据质量",
                "continuation": "模型可以学习数据质量",
                "char_count": 9,
                "unique_char_count": 9,
            },
            {
                "name": "repeat",
                "prompt": "模型",
                "generated": "模型哈哈哈哈哈哈哈哈哈哈",
                "continuation": "哈哈哈哈哈哈哈哈哈哈",
                "char_count": 10,
                "unique_char_count": 1,
            },
            {
                "name": "empty",
                "prompt": "数据",
                "generated": "数据",
                "continuation": "",
                "char_count": 0,
                "unique_char_count": 0,
            },
        ],
    }
    path = root / "eval_suite" / "eval_suite.json"
    write_json(path, payload)
    return path


class GenerationQualityTests(unittest.TestCase):
    def test_generation_quality_facade_keeps_artifact_writer_identity(self) -> None:
        self.assertIs(
            generation_quality.render_generation_quality_html,
            generation_quality_artifacts.render_generation_quality_html,
        )
        self.assertIs(
            generation_quality.write_generation_quality_outputs,
            generation_quality_artifacts.write_generation_quality_outputs,
        )

    def test_build_generation_quality_report_marks_pass_warn_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = make_eval_suite(Path(tmp))

            report = build_generation_quality_report(path, generated_at="2026-05-13T00:00:00Z")

            self.assertEqual(report["source_type"], "eval_suite")
            self.assertEqual(report["summary"]["overall_status"], "fail")
            self.assertEqual(report["summary"]["pass_count"], 1)
            self.assertEqual(report["summary"]["warn_count"], 1)
            self.assertEqual(report["summary"]["fail_count"], 1)
            self.assertEqual(report["cases"][0]["status"], "pass")
            self.assertEqual(report["cases"][1]["status"], "warn")
            self.assertEqual(report["cases"][2]["status"], "fail")
            self.assertIn("low_diversity", {flag["id"] for flag in report["cases"][1]["flags"]})
            self.assertIn("empty_continuation", {flag["id"] for flag in report["cases"][2]["flags"]})
            flag_summary = report["summary"]["flag_summary"]
            self.assertEqual(flag_summary["flag_id_counts"]["empty_continuation"], 1)
            self.assertEqual(flag_summary["flag_id_counts"]["low_diversity"], 1)
            self.assertEqual(flag_summary["flag_id_counts"]["high_ngram_repetition"], 1)
            self.assertEqual(flag_summary["flag_id_counts"]["long_repeat_run"], 1)
            self.assertEqual(flag_summary["flag_level_counts"]["fail"], 1)
            self.assertEqual(flag_summary["flag_level_counts"]["warn"], 3)
            self.assertEqual(flag_summary["worst_cases"][0]["name"], "empty")
            self.assertIn("Fix failed generation cases", " ".join(report["recommendations"]))
            self.assertIn("Prioritize dominant generation flag", " ".join(report["recommendations"]))

    def test_build_generation_quality_report_reads_sample_lab_generated_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "prompt": "token",
                "max_new_tokens": 20,
                "checkpoint": str(root / "checkpoint.pt"),
                "tokenizer": str(root / "tokenizer.json"),
                "results": [
                    {
                        "name": "balanced",
                        "temperature": 0.8,
                        "top_k": 30,
                        "seed": 22,
                        "generated": "tokenabcdefghi",
                    }
                ],
            }
            path = root / "sample_lab.json"
            write_json(path, payload)

            report = build_generation_quality_report(path)

            self.assertEqual(report["source_type"], "sample_lab")
            self.assertEqual(report["summary"]["overall_status"], "pass")
            self.assertEqual(report["cases"][0]["continuation_preview"], "abcdefghi")

    def test_write_generation_quality_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = make_eval_suite(root)
            report = build_generation_quality_report(path)

            outputs = write_generation_quality_outputs(report, root / "quality")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["svg"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            self.assertIn("## Flag Breakdown", markdown)
            self.assertIn("## Cases", markdown)
            self.assertIn("Flag Breakdown", html)
            self.assertIn("generation_quality", Path(outputs["json"]).name)

    def test_render_generation_quality_html_escapes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = make_eval_suite(Path(tmp), title_case="<script>")
            report = build_generation_quality_report(path, title="<Quality>")

            html = render_generation_quality_html(report)

            self.assertIn("&lt;Quality&gt;", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<strong><script>", html)

    def test_generation_quality_rejects_bad_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = make_eval_suite(Path(tmp))

            with self.assertRaises(ValueError):
                build_generation_quality_report(path, min_unique_ratio=0)


if __name__ == "__main__":
    unittest.main()
