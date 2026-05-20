from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scripts.run_tiny_scorecard_comparison_smoke import build_run_config, decision_summary, render_summary  # noqa: E402


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
                    "decision_min_rubric_score": 65.5,
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
                    "blocker_category_counts": {},
                    "dominant_blocker_category": None,
                    "review_category_counts": {},
                    "dominant_review_category": None,
                    "remediation_plan_count": 0,
                    "remediation_blocker_count": 0,
                    "remediation_review_count": 0,
                    "dominant_remediation_kind": None,
                    "dominant_remediation_category": None,
                    "dominant_remediation_action": None,
                    "first_threshold_blocked_candidate": None,
                    "first_threshold_rubric_score": None,
                    "first_threshold_min_rubric_score": None,
                    "first_threshold_margin": None,
                    "threshold_blocked_candidate_count": 0,
                    "threshold_blocked_candidate_names": [],
                    "threshold_closest_candidate": None,
                    "threshold_closest_margin": None,
                    "threshold_largest_gap_candidate": None,
                    "threshold_largest_gap_margin": None,
                    "review_candidate_names": [],
                    "first_blocker": None,
                    "first_review_item": None,
                    "remediation_count": 0,
                    "first_remediation_category": None,
                    "first_remediation_action_code": None,
                    "first_remediation_severity": None,
                    "first_remediation_owner_scope": None,
                    "first_remediation_action": None,
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
        self.assertIn("config_decision_min_rubric_score=65.5", text)
        self.assertIn("comparison_scorecard_count=2", text)
        self.assertIn("comparison_case_delta_count=20", text)
        self.assertIn("decision_status=promote", text)
        self.assertIn("decision_candidate_evaluation_count=2", text)
        self.assertIn("decision_review_candidates=", text)
        self.assertIn("decision_first_review_item=None", text)
        self.assertIn("decision_dominant_blocker_category=None", text)
        self.assertIn("decision_blocker_category_counts=", text)
        self.assertIn("decision_remediation_plan_count=0", text)
        self.assertIn("decision_dominant_remediation_category=None", text)
        self.assertIn("decision_first_threshold_candidate=None", text)
        self.assertIn("decision_first_threshold_margin=None", text)
        self.assertIn("decision_threshold_blocked_count=0", text)
        self.assertIn("decision_threshold_blocked_candidates=", text)
        self.assertIn("decision_threshold_closest_candidate=None", text)
        self.assertIn("decision_threshold_largest_gap_candidate=None", text)
        self.assertIn("decision_remediation_count=0", text)
        self.assertIn("decision_first_remediation_category=None", text)
        self.assertIn("decision_first_remediation_action_code=None", text)
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
                    "--decision-min-rubric-score",
                    "60",
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
            self.assertEqual(summary["run_config"]["decision_min_rubric_score"], 60.0)
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
                self.assertEqual(summary["scorecard_decision"]["first_threshold_blocked_candidate"], "tiny-candidate")
                self.assertEqual(summary["scorecard_decision"]["first_threshold_min_rubric_score"], 60.0)
                self.assertLess(summary["scorecard_decision"]["first_threshold_margin"], 0)
                self.assertEqual(summary["scorecard_decision"]["threshold_blocked_candidate_count"], 1)
                self.assertEqual(summary["scorecard_decision"]["threshold_blocked_candidate_names"], ["tiny-candidate"])
                self.assertEqual(summary["scorecard_decision"]["threshold_closest_candidate"], "tiny-candidate")
                self.assertEqual(summary["scorecard_decision"]["threshold_largest_gap_candidate"], "tiny-candidate")
                self.assertEqual(summary["scorecard_decision"]["dominant_blocker_category"], "threshold")
                self.assertEqual(summary["scorecard_decision"]["blocker_category_counts"], {"threshold": 1})
                self.assertEqual(summary["scorecard_decision"]["remediation_count"], 1)
                self.assertEqual(summary["scorecard_decision"]["first_remediation_category"], "threshold")
                self.assertEqual(summary["scorecard_decision"]["first_remediation_action_code"], "raise_candidate_rubric_or_change_policy")
                self.assertEqual(summary["scorecard_decision"]["first_remediation_severity"], "blocker")
                self.assertEqual(summary["scorecard_decision"]["first_remediation_owner_scope"], "model-eval")
                self.assertIn("explicit policy change", summary["scorecard_decision"]["first_remediation_action"])
                self.assertEqual(summary["scorecard_decision"]["remediation_plan_count"], 1)
                self.assertEqual(summary["scorecard_decision"]["remediation_blocker_count"], 1)
                self.assertEqual(summary["scorecard_decision"]["dominant_remediation_category"], "threshold")
            self.assertIsInstance(summary["scorecard_decision"]["review_candidate_names"], list)
            self.assertTrue(summary["scorecard_decision"]["first_recommendation"])
            self.assertEqual(summary["interpretation"]["model_quality_claim"], "not_claimed")
            self.assertTrue(summary["baseline_smoke"]["pair_same_checkpoint_baseline"])
            self.assertTrue(summary["candidate_smoke"]["pair_same_checkpoint_baseline"])
            self.assertTrue(summary["artifacts"]["comparison_json_exists"])
            self.assertTrue(summary["artifacts"]["comparison_html_exists"])
            self.assertTrue(summary["artifacts"]["decision_json_exists"])
            self.assertTrue(summary["artifacts"]["decision_remediation_csv_exists"])
            self.assertTrue(summary["artifacts"]["decision_html_exists"])
            self.assertTrue((out_dir / "baseline" / "run" / "benchmark-scorecard" / "benchmark_scorecard.json").is_file())
            self.assertTrue((out_dir / "candidate" / "run" / "benchmark-scorecard" / "benchmark_scorecard.json").is_file())
            self.assertTrue((out_dir / "scorecard-comparison" / "benchmark_scorecard_comparison.json").is_file())
            self.assertTrue((out_dir / "scorecard-decision" / "benchmark_scorecard_decision.json").is_file())
            self.assertTrue((out_dir / "scorecard-decision" / "benchmark_scorecard_decision_remediation.csv").is_file())
            self.assertIn(
                "raise_candidate_rubric_or_change_policy",
                (out_dir / "scorecard-decision" / "benchmark_scorecard_decision_remediation.csv").read_text(encoding="utf-8"),
            )
            self.assertIn("decision_first_recommendation=", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_review_candidates=", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("config_budget_mode=candidate_more_iters", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("config_decision_min_rubric_score=60.0", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_first_threshold_candidate=tiny-candidate", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_first_threshold_min=60.0", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_threshold_blocked_count=1", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_threshold_closest_candidate=tiny-candidate", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_dominant_blocker_category=threshold", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_blocker_category_counts=threshold:1", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_remediation_count=1", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_first_remediation_category=threshold", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_first_remediation_action_code=raise_candidate_rubric_or_change_policy", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_first_remediation_severity=blocker", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_remediation_plan_count=1", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("decision_dominant_remediation_category=threshold", summary_text_path.read_text(encoding="utf-8"))
            candidate_command = next(item for item in summary["commands"] if item["name"] == "candidate_smoke")
            self.assertIn("--max-iters 2", candidate_command["command_text"])
            decision_command = next(item for item in summary["commands"] if item["name"] == "scorecard_decision")
            self.assertIn("--min-rubric-score 60.0", decision_command["command_text"])
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
            decision_min_rubric_score = 80.0

        config = build_run_config(Args())

        self.assertEqual(config["baseline_max_iters"], 4)
        self.assertEqual(config["candidate_max_iters"], 4)
        self.assertEqual(config["max_iters_delta"], 0)
        self.assertEqual(config["budget_mode"], "matched_iters")
        self.assertEqual(config["decision_min_rubric_score"], 80.0)

    def test_build_run_config_rejects_invalid_decision_threshold(self) -> None:
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
            decision_min_rubric_score = 101.0

        with self.assertRaisesRegex(ValueError, "--decision-min-rubric-score"):
            build_run_config(Args())

    def test_decision_summary_exposes_first_threshold_block(self) -> None:
        summary = decision_summary(
            {
                "decision_status": "blocked",
                "recommended_action": "keep_baseline_or_fix_candidate",
                "min_rubric_score": 70.0,
                "selected_run": None,
                "summary": {
                    "candidate_count": 0,
                    "clean_candidate_count": 0,
                    "review_candidate_count": 0,
                    "blocked_candidate_count": 1,
                },
                "candidate_evaluations": [
                    {
                        "name": "tiny-baseline",
                        "is_baseline": True,
                        "rubric_avg_score": 82.0,
                        "blockers": ["baseline run is not a promotion candidate"],
                        "review_items": [],
                    },
                    {
                        "name": "tiny-candidate",
                        "is_baseline": False,
                        "rubric_avg_score": 65.25,
                        "blockers": ["rubric_avg_score below 70.0"],
                        "review_items": [],
                    },
                    {
                        "name": "tiny-candidate-far",
                        "is_baseline": False,
                        "rubric_avg_score": 42.0,
                        "blockers": ["rubric_avg_score below 70.0"],
                        "review_items": [],
                    },
                ],
                "recommendations": ["Keep the baseline."],
            }
        )

        self.assertEqual(summary["first_threshold_blocked_candidate"], "tiny-candidate")
        self.assertEqual(summary["first_threshold_blocker"], "rubric_avg_score below 70.0")
        self.assertEqual(summary["first_threshold_rubric_score"], 65.25)
        self.assertEqual(summary["first_threshold_min_rubric_score"], 70.0)
        self.assertEqual(summary["first_threshold_margin"], -4.75)
        self.assertEqual(summary["threshold_blocked_candidate_count"], 2)
        self.assertEqual(summary["threshold_blocked_candidate_names"], ["tiny-candidate", "tiny-candidate-far"])
        self.assertEqual(summary["threshold_closest_candidate"], "tiny-candidate")
        self.assertEqual(summary["threshold_closest_margin"], -4.75)
        self.assertEqual(summary["threshold_largest_gap_candidate"], "tiny-candidate-far")
        self.assertEqual(summary["threshold_largest_gap_margin"], -28.0)


if __name__ == "__main__":
    unittest.main()
