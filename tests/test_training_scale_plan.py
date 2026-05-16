from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import training_scale_plan as training_scale_plan_facade  # noqa: E402
from minigpt import training_scale_plan_artifacts  # noqa: E402
from minigpt.training_portfolio_batch import (  # noqa: E402
    build_training_portfolio_batch_plan,
    load_training_portfolio_batch_variants,
)
from minigpt.training_scale_plan import (  # noqa: E402
    build_training_scale_plan,
    render_training_scale_plan_html,
    render_training_scale_plan_markdown,
    safe_block_size_for_char_count,
    scale_tier,
    write_training_scale_plan_outputs,
)


class TrainingScalePlanTests(unittest.TestCase):
    def test_build_training_scale_plan_summarizes_sources_and_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT 训练规模规划。\n" * 180), encoding="utf-8")

            report = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                dataset_name="demo-zh",
                dataset_version_prefix="v70",
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["dataset"]["source_count"], 1)
            self.assertIn(report["dataset"]["scale_tier"], {"tiny", "small", "medium", "large"})
            self.assertGreaterEqual(len(report["variants"]), 1)
            self.assertEqual(report["batch"]["baseline"], report["variants"][0]["name"])
            self.assertIn("run_training_portfolio_batch.py", " ".join(report["batch"]["command"]))
            self.assertEqual(report["variant_matrix"][0]["token_budget"], 8 * 64 * 50)

    def test_write_outputs_and_variants_are_batch_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT batch handoff data.\n" * 160), encoding="utf-8")
            report = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                dataset_name="demo-zh",
                dataset_version_prefix="v70",
                generated_at="2026-05-14T00:00:00Z",
            )

            outputs = write_training_scale_plan_outputs(report, root / "scale")
            loaded = load_training_portfolio_batch_variants(outputs["variants"])
            batch_plan = build_training_portfolio_batch_plan(
                root,
                [source],
                out_root=root / "batch",
                variants=loaded,
                dataset_name="demo-zh",
            )

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertEqual(batch_plan["variant_count"], len(report["variants"]))
            self.assertEqual(batch_plan["baseline_name"], report["variants"][0]["name"])
            payload = json.loads(Path(outputs["variants"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["source"], "training_scale_plan")

    def test_tiny_corpus_warns_and_can_limit_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tiny.txt"
            source.write_text("tiny", encoding="utf-8")

            report = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                max_variants=1,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["dataset"]["scale_tier"], "tiny")
            self.assertEqual(len(report["variants"]), 1)
            self.assertGreaterEqual(report["dataset"]["warning_count"], 1)
            self.assertTrue(any("tiny" in item for item in report["recommendations"]))
            self.assertLess(report["variants"][0]["block_size"], 64)
            self.assertIn("context_adjustment", report["variants"][0])
            self.assertTrue(any("block_size was reduced" in item for item in report["recommendations"]))

    def test_safe_block_size_keeps_tiny_validation_batches_possible(self) -> None:
        self.assertEqual(safe_block_size_for_char_count(507, 64), 48)
        self.assertEqual(safe_block_size_for_char_count(3, 64), 1)
        self.assertEqual(safe_block_size_for_char_count(10_000, 64), 64)
        with self.assertRaises(ValueError):
            safe_block_size_for_char_count(-1, 64)
        with self.assertRaises(ValueError):
            safe_block_size_for_char_count(100, 0)

    def test_no_recursive_ignores_nested_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "top.txt").write_text("top level corpus text" * 20, encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "nested.txt").write_text("nested corpus text" * 20, encoding="utf-8")

            report = build_training_scale_plan(
                [root],
                project_root=root,
                out_root=root / "scale",
                recursive=False,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["dataset"]["source_count"], 1)
            self.assertEqual(Path(report["sources_detail"][0]["path"]).name, "top.txt")

    def test_renderers_escape_html_and_markdown_contains_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text("MiniGPT render data" * 30, encoding="utf-8")
            report = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                dataset_name="<demo>",
                generated_at="2026-05-14T00:00:00Z",
            )

            markdown = render_training_scale_plan_markdown(report)
            html = render_training_scale_plan_html(report)

            self.assertIn("## Batch Command", markdown)
            self.assertIn("&lt;demo&gt;", html)
            self.assertNotIn("<demo>", html)

    def test_scale_tier_boundaries(self) -> None:
        self.assertEqual(scale_tier(0), "tiny")
        self.assertEqual(scale_tier(2_000), "small")
        self.assertEqual(scale_tier(20_000), "medium")
        self.assertEqual(scale_tier(200_000), "large")
        with self.assertRaises(ValueError):
            scale_tier(-1)

    def test_training_scale_plan_facade_keeps_artifact_writer_identity(self) -> None:
        self.assertIs(
            training_scale_plan_facade.write_training_scale_plan_outputs,
            training_scale_plan_artifacts.write_training_scale_plan_outputs,
        )
        self.assertIs(
            training_scale_plan_facade.render_training_scale_plan_html,
            training_scale_plan_artifacts.render_training_scale_plan_html,
        )
        self.assertIs(
            training_scale_plan_facade.render_training_scale_plan_markdown,
            training_scale_plan_artifacts.render_training_scale_plan_markdown,
        )


if __name__ == "__main__":
    unittest.main()
