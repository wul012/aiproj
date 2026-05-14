from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_portfolio import (  # noqa: E402
    build_training_portfolio_plan,
    render_training_portfolio_html,
    run_training_portfolio_plan,
    write_training_portfolio_outputs,
)


class TrainingPortfolioTests(unittest.TestCase):
    def test_build_training_portfolio_plan_orders_real_pipeline_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("人工智能训练数据", encoding="utf-8")

            plan = build_training_portfolio_plan(
                root,
                [source],
                out_root=root / "portfolio",
                run_name="tiny-run",
                dataset_name="demo",
                dataset_version="v67",
                request_log_path=root / "requests.jsonl",
                max_iters=3,
                eval_interval=1,
                eval_iters=1,
            )

            self.assertEqual(plan["schema_version"], 1)
            self.assertEqual([step["key"] for step in plan["steps"]], [
                "prepare_dataset",
                "train",
                "eval_suite",
                "generation_quality",
                "benchmark_scorecard",
                "dataset_card",
                "registry",
                "maturity_summary",
                "request_history_summary",
                "maturity_narrative",
            ])
            self.assertIn("checkpoint.pt", plan["artifacts"]["checkpoint"])
            self.assertIn("dataset_card.json", plan["artifacts"]["dataset_card"])
            self.assertIn("--request-history-summary", plan["steps"][-1]["command"])
            train_command = " ".join(plan["steps"][1]["command"])
            self.assertIn("--max-iters 3", train_command)
            self.assertIn("--eval-iters 1", train_command)

    def test_dry_run_report_marks_artifacts_as_planned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("MiniGPT data", encoding="utf-8")
            plan = build_training_portfolio_plan(root, [source], out_root=root / "portfolio")

            report = run_training_portfolio_plan(plan, execute=False, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["execution"]["status"], "planned")
            self.assertEqual(report["execution"]["completed_steps"], 0)
            self.assertGreater(report["execution"]["artifact_count"], 0)
            self.assertEqual(report["execution"]["available_artifact_count"], 0)
            self.assertIn("Run the pipeline with --execute", report["recommendations"][0])

    def test_execute_plan_records_success_and_stdout_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = {
                "schema_version": 1,
                "title": "demo",
                "project_root": str(root),
                "out_root": str(root),
                "run_name": "demo",
                "dataset_name": "demo",
                "dataset_version": "v1",
                "artifacts": {"marker": "marker.txt"},
                "steps": [
                    {
                        "key": "write_marker",
                        "title": "Write marker",
                        "command": [
                            sys.executable,
                            "-c",
                            "from pathlib import Path; Path('marker.txt').write_text('ok', encoding='utf-8'); print('marker ok')",
                        ],
                        "expected_outputs": ["marker.txt"],
                    }
                ],
            }

            report = run_training_portfolio_plan(plan, execute=True)

            self.assertEqual(report["execution"]["status"], "completed")
            self.assertEqual(report["execution"]["completed_steps"], 1)
            self.assertEqual(report["execution"]["available_artifact_count"], 1)
            self.assertIn("marker ok", report["step_results"][0]["stdout_tail"])

    def test_write_outputs_and_html_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.txt"
            source.write_text("MiniGPT data", encoding="utf-8")
            plan = build_training_portfolio_plan(root, [source], out_root=root / "portfolio", title="<Portfolio>")
            report = run_training_portfolio_plan(plan, execute=False)

            outputs = write_training_portfolio_outputs(report, root / "out")
            html = render_training_portfolio_html(report)

            self.assertEqual(set(outputs), {"json", "markdown", "html"})
            self.assertIn("training_portfolio", Path(outputs["json"]).name)
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["schema_version"], 1)
            self.assertIn("Pipeline Steps", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("&lt;Portfolio&gt;", html)
            self.assertNotIn("<h1><Portfolio>", html)


if __name__ == "__main__":
    unittest.main()
