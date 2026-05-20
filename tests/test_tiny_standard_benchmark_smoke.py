from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scripts.run_tiny_standard_benchmark_smoke import (  # noqa: E402
    build_capped_prompt_suite_payload,
    build_tiny_corpus,
    render_summary,
)


class TinyStandardBenchmarkSmokeTests(unittest.TestCase):
    def test_capped_standard_suite_keeps_all_cases_with_lower_token_budget(self) -> None:
        payload = build_capped_prompt_suite_payload("standard-zh", 7)

        self.assertEqual(payload["suite_name"], "minigpt-standard-zh-benchmark")
        self.assertEqual(payload["suite_version"], "2-cap7")
        self.assertEqual(len(payload["cases"]), 10)
        self.assertTrue(all(case["max_new_tokens"] == 7 for case in payload["cases"]))
        corpus = build_tiny_corpus(payload)
        self.assertIn("Evidence chain: train, eval suite, generation quality, pair baseline, benchmark scorecard.", corpus)
        self.assertIn(payload["cases"][0]["prompt"], corpus)

    def test_render_summary_prints_model_capability_evidence_fields(self) -> None:
        text = render_summary(
            {
                "status": "pass",
                "decision": "evidence-ready",
                "issue_count": 0,
                "run_dir": "runs/demo",
                "suite_path": "runs/demo-suite.json",
                "artifacts": {"checkpoint_exists": True},
                "training": {"best_val_loss": 1.2, "final_val_loss": 1.4},
                "eval_suite": {
                    "case_count": 10,
                    "coverage_status": "pass",
                    "comparison_status": "pass",
                },
                "generation_quality": {"overall_status": "warn", "total_flags": 3},
                "pair_batch": {
                    "case_count": 10,
                    "generated_difference_count": 0,
                    "same_checkpoint_baseline": True,
                    "comparison_mode": "same_checkpoint_baseline",
                },
                "benchmark_scorecard": {
                    "overall_status": "warn",
                    "overall_score": 66.5,
                    "pair_batch_cases": 10,
                    "pair_same_checkpoint_baseline": True,
                    "pair_comparison_mode": "same_checkpoint_baseline",
                },
                "commands": [{"name": "train", "status": "pass"}, {"name": "pair_batch", "status": "pass"}],
            }
        )

        self.assertIn("status=pass", text)
        self.assertIn("eval_suite_case_count=10", text)
        self.assertIn("generation_quality_total_flags=3", text)
        self.assertIn("pair_batch_case_count=10", text)
        self.assertIn("pair_same_checkpoint_baseline=True", text)
        self.assertIn("scorecard_overall_score=66.5", text)
        self.assertIn("scorecard_pair_comparison_mode=same_checkpoint_baseline", text)
        self.assertIn("command_train=pass", text)
        self.assertIn("command_pair_batch=pass", text)

    def test_tiny_standard_benchmark_smoke_script_runs_real_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "tiny-smoke"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_tiny_standard_benchmark_smoke.py"),
                    "--out-dir",
                    str(out_dir),
                    "--suite-name",
                    "standard-zh",
                    "--case-token-cap",
                    "4",
                    "--max-iters",
                    "1",
                    "--eval-iters",
                    "1",
                    "--batch-size",
                    "2",
                    "--block-size",
                    "8",
                    "--n-embd",
                    "8",
                    "--force",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary_path = out_dir / "tiny_standard_benchmark_smoke_summary.json"
            summary_text_path = out_dir / "tiny_standard_benchmark_smoke_summary.txt"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["decision"], "evidence-ready")
            self.assertEqual(summary["eval_suite"]["case_count"], 10)
            self.assertEqual(summary["eval_suite"]["coverage_status"], "pass")
            self.assertEqual(summary["eval_suite"]["comparison_status"], "pass")
            self.assertTrue(summary["artifacts"]["checkpoint_exists"])
            self.assertTrue(summary["artifacts"]["generation_quality_exists"])
            self.assertTrue(summary["artifacts"]["pair_batch_exists"])
            self.assertTrue(summary["artifacts"]["pair_batch_html_exists"])
            self.assertTrue(summary["artifacts"]["benchmark_scorecard_exists"])
            self.assertEqual(summary["pair_batch"]["case_count"], 10)
            self.assertEqual(summary["pair_batch"]["generated_difference_count"], 0)
            self.assertTrue(summary["pair_batch"]["same_checkpoint_baseline"])
            self.assertEqual(summary["pair_batch"]["comparison_mode"], "same_checkpoint_baseline")
            self.assertEqual(summary["benchmark_scorecard"]["pair_batch_cases"], 10)
            self.assertTrue(summary["benchmark_scorecard"]["pair_same_checkpoint_baseline"])
            self.assertEqual(summary["benchmark_scorecard"]["pair_comparison_mode"], "same_checkpoint_baseline")
            self.assertEqual({item["status"] for item in summary["commands"]}, {"pass"})
            self.assertTrue((out_dir / "run" / "checkpoint.pt").is_file())
            self.assertTrue((out_dir / "run" / "eval_suite" / "eval_suite.json").is_file())
            self.assertTrue((out_dir / "run" / "generation-quality" / "generation_quality.json").is_file())
            self.assertTrue((out_dir / "run" / "pair_batch" / "pair_generation_batch.json").is_file())
            self.assertTrue((out_dir / "run" / "pair_batch" / "pair_generation_batch.html").is_file())
            self.assertTrue((out_dir / "run" / "benchmark-scorecard" / "benchmark_scorecard.json").is_file())
            self.assertIn("pair_same_checkpoint_baseline=True", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("scorecard_overall_status=", summary_text_path.read_text(encoding="utf-8"))
            self.assertIn("summary_json=", completed.stdout)
            self.assertIn("command_pair_batch=pass", completed.stdout)
            self.assertIn("command_benchmark_scorecard=pass", completed.stdout)


if __name__ == "__main__":
    unittest.main()
