from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_portfolio_batch import (
    build_training_portfolio_batch_plan,
    load_training_portfolio_batch_variants,
    render_training_portfolio_batch_html,
    render_training_portfolio_batch_markdown,
    run_training_portfolio_batch_plan,
    write_training_portfolio_batch_outputs,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class TrainingPortfolioBatchTests(unittest.TestCase):
    def test_build_batch_plan_creates_variant_matrix_and_comparison_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("MiniGPT batch data", encoding="utf-8")
            variants = [
                {"name": "small", "description": "baseline", "max_iters": 20, "block_size": 32, "seed": 1},
                {"name": "wider", "description": "larger embedding", "max_iters": 30, "n_embd": 96, "seed": 2},
            ]

            plan = build_training_portfolio_batch_plan(
                root,
                [source],
                out_root=root / "batch",
                variants=variants,
                dataset_name="demo-zh",
                baseline="small",
                python_executable="python",
            )

            self.assertEqual(plan["schema_version"], 1)
            self.assertEqual(plan["variant_count"], 2)
            self.assertEqual(plan["baseline_name"], "small")
            self.assertEqual(plan["summary"]["total_max_iters"], 50)
            self.assertEqual(plan["summary"]["model_shape_count"], 2)
            self.assertIn("compare_training_portfolios.py", " ".join(plan["comparison"]["command"]))
            self.assertEqual(plan["variants"][1]["config"]["n_embd"], 96)
            self.assertTrue(plan["variants"][0]["portfolio_path"].endswith("training_portfolio.json"))

    def test_run_batch_dry_run_writes_variant_reports_and_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("MiniGPT batch data", encoding="utf-8")
            variants = [
                {"name": "small", "max_iters": 20, "block_size": 32},
                {"name": "context", "max_iters": 20, "block_size": 96},
            ]
            plan = build_training_portfolio_batch_plan(root, [source], out_root=root / "batch", variants=variants)

            report = run_training_portfolio_batch_plan(plan, execute=False, generated_at="2026-05-14T00:00:00Z")
            outputs = write_training_portfolio_batch_outputs(report, root / "batch")

            self.assertEqual(report["execution"]["status"], "planned")
            self.assertEqual(report["execution"]["comparison_status"], "written")
            self.assertEqual(len(report["variant_results"]), 2)
            self.assertIn("json", outputs)
            self.assertTrue((root / "batch" / "variants" / "small" / "training_portfolio.json").exists())
            self.assertTrue((root / "batch" / "comparison" / "training_portfolio_comparison.json").exists())
            comparison = json.loads((root / "batch" / "comparison" / "training_portfolio_comparison.json").read_text(encoding="utf-8"))
            self.assertEqual(comparison["portfolio_count"], 2)
            self.assertEqual(comparison["summary"]["planned_count"], 2)

    def test_load_variants_accepts_object_or_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            list_path = root / "list.json"
            object_path = root / "object.json"
            write_json(list_path, [{"name": "a"}])
            write_json(object_path, {"variants": [{"name": "b", "max_iters": 10}]})

            self.assertEqual(load_training_portfolio_batch_variants(list_path)[0]["name"], "a")
            self.assertEqual(load_training_portfolio_batch_variants(object_path)[0]["max_iters"], 10)

    def test_build_batch_plan_rejects_duplicate_variant_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("MiniGPT batch data", encoding="utf-8")

            with self.assertRaises(ValueError):
                build_training_portfolio_batch_plan(
                    root,
                    [source],
                    out_root=root / "batch",
                    variants=[{"name": "dup"}, {"name": "dup"}],
                )

    def test_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("MiniGPT batch data", encoding="utf-8")
            plan = build_training_portfolio_batch_plan(
                root,
                [source],
                out_root=root / "batch",
                variants=[{"name": "<base>", "description": "<script>"}],
            )
            report = run_training_portfolio_batch_plan(plan, execute=False)

            markdown = render_training_portfolio_batch_markdown(report)
            html = render_training_portfolio_batch_html(report)

            self.assertIn("## Variants", markdown)
            self.assertIn("&lt;base&gt;", html)
            self.assertNotIn("<strong><base>", html)


if __name__ == "__main__":
    unittest.main()
