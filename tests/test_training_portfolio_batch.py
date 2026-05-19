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
    render_training_portfolio_batch_html as facade_render_training_portfolio_batch_html,
    render_training_portfolio_batch_markdown as facade_render_training_portfolio_batch_markdown,
    run_training_portfolio_batch_plan,
    write_training_portfolio_batch_outputs,
    write_training_portfolio_batch_html as facade_write_training_portfolio_batch_html,
    write_training_portfolio_batch_markdown as facade_write_training_portfolio_batch_markdown,
    _comparison_review_summary,
)
from minigpt.training_portfolio_batch_artifacts import (
    render_training_portfolio_batch_html,
    render_training_portfolio_batch_markdown,
    write_training_portfolio_batch_outputs as artifact_write_training_portfolio_batch_outputs,
    write_training_portfolio_batch_html as artifact_write_training_portfolio_batch_html,
    write_training_portfolio_batch_markdown as artifact_write_training_portfolio_batch_markdown,
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

    def test_build_batch_plan_passes_pair_baseline_to_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("MiniGPT batch data", encoding="utf-8")
            baseline = root / "baseline" / "checkpoint.pt"
            baseline_tokenizer = root / "baseline" / "tokenizer.json"
            variant_baseline = root / "variant-baseline" / "checkpoint.pt"
            variants = [
                {"name": "small", "pair_candidate_id": "small-candidate"},
                {"name": "context", "pair_baseline_checkpoint": str(variant_baseline), "pair_baseline_id": "variant-base"},
            ]

            plan = build_training_portfolio_batch_plan(
                root,
                [source],
                out_root=root / "batch",
                variants=variants,
                pair_baseline_checkpoint=baseline,
                pair_baseline_tokenizer=baseline_tokenizer,
                pair_baseline_id="global-base",
                pair_candidate_id="global-candidate",
            )

            small = plan["variants"][0]
            context = plan["variants"][1]
            small_pair = small["portfolio_plan"]["pair_config"]
            context_pair = context["portfolio_plan"]["pair_config"]
            small_command = " ".join(small["portfolio_plan"]["steps"][5]["command"])
            context_command = " ".join(context["portfolio_plan"]["steps"][5]["command"])

            self.assertEqual(plan["summary"]["pair_mode_counts"], {"external_baseline": 2})
            self.assertEqual(small["config"]["pair_baseline_checkpoint"], str(baseline))
            self.assertEqual(small_pair["left_checkpoint"], str(baseline))
            self.assertEqual(small_pair["left_tokenizer"], str(baseline_tokenizer))
            self.assertEqual(small_pair["left_id"], "global-base")
            self.assertEqual(small_pair["right_id"], "small-candidate")
            self.assertIn("--left-checkpoint " + str(baseline), small_command)
            self.assertIn("--right-id small-candidate", small_command)
            self.assertEqual(context_pair["left_checkpoint"], str(variant_baseline))
            self.assertEqual(context_pair["left_tokenizer"], str(variant_baseline.parent / "tokenizer.json"))
            self.assertEqual(context_pair["left_id"], "variant-base")
            self.assertEqual(context_pair["right_id"], "global-candidate")
            self.assertIn("--left-checkpoint " + str(variant_baseline), context_command)

    def test_build_batch_plan_passes_standard_suite_to_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("MiniGPT batch data", encoding="utf-8")
            variants = [
                {"name": "standard", "suite_name": "standard-zh"},
                {"name": "file-suite", "suite_path": str(root / "custom-suite.json")},
            ]

            plan = build_training_portfolio_batch_plan(
                root,
                [source],
                out_root=root / "batch",
                variants=variants,
                suite_name="standard-zh",
            )

            standard = plan["variants"][0]["portfolio_plan"]
            file_suite = plan["variants"][1]["portfolio_plan"]
            standard_eval = " ".join(standard["steps"][3]["command"])
            standard_pair = " ".join(standard["steps"][5]["command"])
            file_eval = " ".join(file_suite["steps"][3]["command"])
            self.assertEqual(standard["suite_path"], "builtin:standard-zh")
            self.assertIn("--suite-name standard-zh", standard_eval)
            self.assertIn("--suite-name standard-zh", standard_pair)
            self.assertIn("--suite " + str(root / "custom-suite.json"), file_eval)
            self.assertEqual(file_suite["suite"]["mode"], "file")

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
            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertTrue((root / "batch" / "variants" / "small" / "training_portfolio.json").exists())
            self.assertTrue((root / "batch" / "comparison" / "training_portfolio_comparison.json").exists())
            comparison = json.loads((root / "batch" / "comparison" / "training_portfolio_comparison.json").read_text(encoding="utf-8"))
            self.assertEqual(comparison["portfolio_count"], 2)
            self.assertEqual(comparison["summary"]["planned_count"], 2)
            self.assertEqual(report["comparison_review_summary"]["review_action_count"], comparison["summary"]["review_action_count"])
            self.assertGreaterEqual(report["comparison_review_summary"]["review_action_count"], 2)
            self.assertEqual(report["comparison_review_summary"]["blocker_action_count"], 0)
            self.assertEqual(report["summary"]["pair_mode_counts"], {"same_checkpoint_baseline": 2})
            self.assertEqual(report["variant_results"][0]["pair_mode"], "same_checkpoint_baseline")
            self.assertIn("Review batch comparison actions", " ".join(report["recommendations"]))
            artifact_outputs = artifact_write_training_portfolio_batch_outputs(report, root / "batch-copy")
            self.assertEqual(set(artifact_outputs), {"json", "csv", "markdown", "html"})
            self.assertTrue(Path(artifact_outputs["json"]).exists())
            self.assertTrue(Path(artifact_outputs["csv"]).exists())
            self.assertTrue(Path(artifact_outputs["markdown"]).exists())
            self.assertTrue(Path(artifact_outputs["html"]).exists())

    def test_batch_comparison_review_summary_carries_blockers(self) -> None:
        comparison_report = {
            "summary": {
                "review_action_count": 2,
                "blocker_action_count": 1,
                "maturity_review_count": 1,
                "maturity_review_names": ["candidate"],
                "maturity_coverage_regression_count": 1,
                "maturity_coverage_regression_names": ["candidate"],
            },
            "review_actions": [
                {"portfolio": "candidate", "severity": "blocker", "reason": "best_score_coverage_regressed"},
                {"portfolio": "shadow", "severity": "review", "reason": "dataset_card_review"},
            ],
        }

        summary = _comparison_review_summary(comparison_report)

        self.assertEqual(summary["review_action_count"], 2)
        self.assertEqual(summary["blocker_action_count"], 1)
        self.assertEqual(summary["maturity_coverage_regression_names"], ["candidate"])
        self.assertEqual(summary["blocker_reasons"], ["best_score_coverage_regressed"])
        self.assertEqual(summary["blocker_portfolios"], ["candidate"])

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
            self.assertIn("Pair modes: `same_checkpoint_baseline=1`", markdown)
            self.assertIn("Comparison review actions", markdown)
            self.assertIn("&lt;base&gt;", html)
            self.assertIn("same_checkpoint_baseline", html)
            self.assertIn("Review actions", html)
            self.assertNotIn("<strong><base>", html)

    def test_facade_keeps_artifact_identity(self) -> None:
        self.assertIs(facade_render_training_portfolio_batch_markdown, render_training_portfolio_batch_markdown)
        self.assertIs(facade_render_training_portfolio_batch_html, render_training_portfolio_batch_html)
        self.assertIs(facade_write_training_portfolio_batch_markdown, artifact_write_training_portfolio_batch_markdown)
        self.assertIs(facade_write_training_portfolio_batch_html, artifact_write_training_portfolio_batch_html)
        self.assertIs(write_training_portfolio_batch_outputs, artifact_write_training_portfolio_batch_outputs)


if __name__ == "__main__":
    unittest.main()
