from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import comparison as comparison_facade
from minigpt import comparison_artifacts


def build_report() -> dict[str, object]:
    return {
        "generated_at": "2026-05-15T00:00:00Z",
        "run_count": 2,
        "baseline": {"name": "<baseline>", "path": "runs/base"},
        "summary": {
            "improved_best_val_loss_count": 1,
            "regressed_best_val_loss_count": 0,
            "model_signature_count": 2,
            "dataset_version_count": 2,
        },
        "runs": [
            {
                "name": "base",
                "path": "runs/base",
                "tokenizer": "char",
                "dataset_version": "demo@v1",
                "dataset_fingerprint": "abc123",
                "best_val_loss": 2.0,
                "eval_loss": 2.2,
                "perplexity": 10.0,
                "total_parameters": 100,
                "model_signature": "tok=char|L=1|H=1|E=32|B=16|V=20|P=100|steps=2",
            },
            {
                "name": "wide",
                "path": "runs/wide",
                "tokenizer": "char",
                "dataset_version": "demo@v2",
                "dataset_fingerprint": "def456",
                "best_val_loss": 1.5,
                "eval_loss": 2.0,
                "perplexity": 9.0,
                "total_parameters": 160,
                "model_signature": "tok=char|L=1|H=1|E=64|B=16|V=20|P=160|steps=2",
            },
        ],
        "baseline_deltas": [
            {
                "name": "base",
                "path": "runs/base",
                "baseline_name": "<baseline>",
                "is_baseline": True,
                "best_val_loss_delta": 0.0,
                "best_val_loss_delta_pct": 0.0,
                "eval_loss_delta": 0.0,
                "perplexity_delta": 0.0,
                "total_parameters_delta": 0,
                "total_parameters_ratio": 1.0,
                "max_iters_delta": 0,
                "tokenizer_changed": False,
                "model_signature_changed": False,
                "dataset_version_changed": False,
                "best_val_loss_relation": "baseline",
            },
            {
                "name": "wide",
                "path": "runs/wide",
                "baseline_name": "<baseline>",
                "is_baseline": False,
                "best_val_loss_delta": -0.5,
                "best_val_loss_delta_pct": -25.0,
                "eval_loss_delta": -0.2,
                "perplexity_delta": -1.0,
                "total_parameters_delta": 60,
                "total_parameters_ratio": 1.6,
                "max_iters_delta": 0,
                "tokenizer_changed": False,
                "model_signature_changed": True,
                "dataset_version_changed": True,
                "best_val_loss_relation": "improved",
            },
        ],
        "recommendations": [
            "wide beats the baseline by -0.5 best_val_loss; inspect generation quality before promoting it.",
        ],
    }


class ComparisonArtifactTests(unittest.TestCase):
    def test_facade_exports_match_artifact_module(self) -> None:
        self.assertIs(comparison_facade.render_comparison_html, comparison_artifacts.render_comparison_html)
        self.assertIs(comparison_facade.render_comparison_markdown, comparison_artifacts.render_comparison_markdown)
        self.assertIs(comparison_facade.write_comparison_csv, comparison_artifacts.write_comparison_csv)
        self.assertIs(comparison_facade.write_comparison_svg, comparison_artifacts.write_comparison_svg)
        self.assertIs(comparison_facade.write_comparison_outputs, comparison_artifacts.write_comparison_outputs)

    def test_write_outputs_and_escape(self) -> None:
        report = build_report()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "comparison-out"
            outputs = comparison_artifacts.write_comparison_outputs(report, out_dir)

            self.assertEqual(set(outputs), {"json", "csv", "svg", "markdown", "html"})
            for path in outputs.values():
                self.assertTrue(Path(path).exists())

            html_text = Path(outputs["html"]).read_text(encoding="utf-8")
            md_text = Path(outputs["markdown"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            svg_text = Path(outputs["svg"]).read_text(encoding="utf-8")
            json_text = Path(outputs["json"]).read_text(encoding="utf-8")

            self.assertIn("&lt;baseline&gt;", html_text)
            self.assertIn("MiniGPT baseline model comparison", md_text)
            self.assertIn("best_val_loss_delta", csv_text)
            self.assertIn("<svg", svg_text)
            self.assertEqual(json.loads(json_text)["run_count"], 2)

    def test_renderers_include_summary(self) -> None:
        report = build_report()
        markdown = comparison_artifacts.render_comparison_markdown(report)
        html_text = comparison_artifacts.render_comparison_html(report)

        self.assertIn("Runs", markdown)
        self.assertIn("Improved", html_text)
        self.assertIn("&lt;baseline&gt;", html_text)


if __name__ == "__main__":
    unittest.main()
