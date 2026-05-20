from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scripts.run_tiny_scorecard_comparison_smoke import build_run_config, render_summary  # noqa: E402


class TinyScorecardComparisonSmokeTests(unittest.TestCase):
    def test_render_summary_keeps_comparison_and_boundary_fields(self) -> None:
        text = render_summary(
            {
                "status": "pass",
                "decision": "comparison-evidence-ready",
                "issue_count": 0,
                "run_config": {
                    "suite_name": "standard-zh",
                    "case_token_cap": 3,
                    "baseline_max_iters": 1,
                    "candidate_max_iters": 2,
                    "max_iters_delta": 1,
                    "budget_mode": "candidate_more_iters",
                },
                "baseline_smoke": {
                    "scorecard_overall_status": "pass",
                    "scorecard_overall_score": 88.5,
                    "pair_same_checkpoint_baseline": True,
                },
                "candidate_smoke": {
                    "scorecard_overall_status": "warn",
                    "scorecard_overall_score": 78.25,
                    "pair_same_checkpoint_baseline": True,
                },
                "scorecard_comparison": {
                    "scorecard_count": 2,
                    "baseline_name": "tiny-baseline",
                    "best_by_overall_score": "tiny-baseline",
                    "improved_overall_count": 0,
                    "regressed_overall_count": 1,
                    "case_delta_count": 20,
                    "non_comparison_ready_count": 0,
                },
                "scorecard_decision": {
                    "decision_status": "promote",
                    "recommended_action": "promote_selected_scorecard",
                    "selected_name": "tiny-candidate",
                    "candidate_evaluation_count": 2,
                    "blocked_candidate_count": 0,
                    "blocked_candidate_names": [],
                    "review_candidate_names": [],
                    "first_blocker": None,
                    "first_review_item": None,
                    "first_recommendation": "Promote the selected scorecard only as benchmark evidence.",
                },
                "interpretation": {"model_quality_claim": "not_claimed"},
                "commands": [
                    {"name": "baseline_smoke", "status": "pass"},
                    {"name": "scorecard_comparison", "status": "pass"},
                    {"name": "scorecard_decision", "status": "pass"},
                ],
            }
        )

        self.assertIn("status=pass", text)
        self.assertIn("config_baseline_max_iters=1", text)
        self.assertIn("config_candidate_max_iters=2", text)
        self.assertIn("config_budget_mode=candidate_more_iters", text)
        self.assertIn("comparison_scorecard_count=2", text)
        self.assertIn("comparison_case_delta_count=20", text)
        self.assertIn("decision_status=promote", text)
        self.assertIn("decision_candidate_evaluation_count=2", text)
        self.assertIn("decision_review_candidates=", text)
        self.assertIn("decision_first_review_item=None", text)
        self.assertIn("decision_first_recommendation=Promote the selected scorecard only as benchmark evidence.", text)
        self.assertIn("model_quality_claim=not_claimed", text)
        self.assertIn("command_scorecard_comparison=pass", text)
        self.assertIn("command_scorecard_decision=pass", text)

    def test_tiny_scorecard_comparison_smoke_runs_real_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "comparison-smoke"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_tiny_scorecard_comparison_smoke.py"),
                    "--out-dir",
                    str(out_dir),
                    "--suite-name",
                    "standard-zh",
                    "--case-token-cap",
                    "3",
                    "--max-iters",
                    "1",
                    "--baseline-max-iters",
                    "1",
                    "--candidate-max-iters",
                    "2",
                    "--eval-iters",
                    "1",
                    "--batch-size",
                    "2",
                    "--block-size",
                    "8",
                    "--n-embd",
                    "8",
                    "--baseline-seed",
                    "1337",
                    "--candidate-seed",
                    "2026",
                    "--force",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary_path = out_dir / "tiny_scorecard_comparison_smoke_summary.json"
            summary_text_path = out_dir / "tiny_scorecard_comparison_smoke_summary.txt"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["decision"], "comparison-evidence-ready")
            self.assertEqual(summary["run_config"]["baseline_max_iters"], 1)
            self.assertEqual(summary["run_config"]["candidate_max_iters"], 2)
            self.assertEqual(summary["run_config"]["max_iters_delta"], 1)
            self.assertEqual(summary["run_config"]["budget_mode"], "candidate_more_iters")
            self.assertEqual(summary["scorecard_comparison"]["scorecard_count"], 2)
            self.assertEqual(summary["scorecard_comparison"]["baseline_name"], "tiny-baseline")
            self.assertEqual(summary["scorecard_comparison"]["case_delta_count"], 20)
            self.assertEqual(summary["scorecard_comparison"]["non_comparison_ready_count"], 0)
            self.assertIn(summary["scorecard_decision"]["decision_status"], {"promote", "review", "blocked"})
            self.assertTrue(summary["scorecard_decision"]["recommended_action"])
            self.assertEqual(summary["scorecard_decision"]["candidate_evaluation_count"], 2)
            self.assertIsInstance(summary["scorecard_decision"]["blocked_candidate_names"], list)
            if summary["scorecard_decision"]["decision_status"] == "blocked":
                self.assertTrue(summary["scorecard_decision"]["blocked_candidate_names"])
                self.assertTrue(summary["scorecard_decision"]["first_blocker"])
            self.assertIsInstance(summary["scorecard_decision"]["review_candidate_names"], list)
            self.assertTrue(summary["scorecard_decision"]["first_recommendation"])
            self.assertEqual(summary["interpretation"]["model_quality_claim"], "not_claimed")
            self.assertTrue(summary["baseline_smoke"]["pair_same_checkpoint_baseline"])
            self.assertTrue(summary["candidate_smoke"]["pair_same_checkpoint_baseline"])
            self.assertTrue(summary["artifacts"]["comparison_json_exists"])
            self.assertTrue(summary["artifacts"]["comparison_html_exists"])
            self.assertTrue(summary["artifacts"]["decision_json_exists"])
            self.assertTrue(summary["artifacts"]["decision_html_exists"])
            self.assertTrue((out_dir / "baseline" / "run" / "benchmark-scorecard" / "benchmark_scorecard.json").is_file())
            self.assertTrue((out_dir / "candidate" / "run" / "benchmark-scorecard" / "benchmark_scorecard.json").is_file())
            self.assertTrue((out_dir / "scorecard-comparison" / "benchmark_scorecard_comparison.json").is_file())
            self.assertTrue((out_dir / "scorecard-decision" / "benchmark_scorecard_decision.json").is_file())
            self.assertIn("decision_first_recommendation=", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_review_candidates=", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("config_budget_mode=candidate_more_iters", summary_text_path.read_text(encoding="utf-8"))
            candidate_command = next(item for item in summary["commands"] if item["name"] == "candidate_smoke")
            self.assertIn("--max-iters 2", candidate_command["command_text"])
            self.assertIn("model_quality_claim=not_claimed", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("command_scorecard_comparison=pass", completed.stdout)
            self.assertIn("command_scorecard_decision=pass", completed.stdout)

    def test_build_run_config_defaults_to_matched_budget(self) -> None:
        class Args:
            suite_name = "standard-zh"
            case_token_cap = 3
            max_iters = 4
            baseline_max_iters = None
            candidate_max_iters = None
            eval_iters = 1
            batch_size = 2
            block_size = 8
            n_layer = 1
            n_head = 1
            n_embd = 8
            baseline_seed = 1337
            candidate_seed = 2026

        config = build_run_config(Args())

        self.assertEqual(config["baseline_max_iters"], 4)
        self.assertEqual(config["candidate_max_iters"], 4)
        self.assertEqual(config["max_iters_delta"], 0)
        self.assertEqual(config["budget_mode"], "matched_iters")


if __name__ == "__main__":
    unittest.main()
