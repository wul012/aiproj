from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_run_evidence import (  # noqa: E402
    build_training_run_evidence,
    render_training_run_evidence_html,
    write_training_run_evidence_outputs,
)


def make_run(root: Path) -> Path:
    run_dir = root / "run"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
    (run_dir / "tokenizer.json").write_text(json.dumps({"type": "char", "itos": ["<unk>", "a"]}), encoding="utf-8")
    (run_dir / "train_config.json").write_text(
        json.dumps(
            {
                "tokenizer": "char",
                "max_iters": 2,
                "batch_size": 2,
                "block_size": 8,
                "learning_rate": 0.001,
                "device_used": "cpu",
                "data_source": {"kind": "data", "path": "data/sample.txt"},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "metrics.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"step": 1, "train_loss": 1.2, "val_loss": 1.4, "last_loss": 1.3}),
                json.dumps({"step": 2, "train_loss": 1.0, "val_loss": 1.1, "last_loss": 1.05}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "history_summary.json").write_text(
        json.dumps({"record_count": 2, "last_step": 2, "best_val_step": 2, "best_val_loss": 1.1, "last_val_loss": 1.1}),
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "data": {
                    "source": {"kind": "data", "path": "data/sample.txt"},
                    "token_count": 100,
                    "train_token_count": 90,
                    "val_token_count": 10,
                    "dataset_quality": {"status": "pass", "short_fingerprint": "abc123def456"},
                },
                "training": {"tokenizer": "char", "device_used": "cpu", "end_step": 2},
                "model": {"parameter_count": 1234},
                "results": {"history_summary": {"best_val_loss": 1.1, "last_val_loss": 1.1}},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "sample.txt").write_text("prompt: MiniGPT\n\nMiniGPT sample output", encoding="utf-8")
    eval_dir = run_dir / "eval_suite"
    eval_dir.mkdir()
    (eval_dir / "eval_suite.json").write_text(
        json.dumps(
            {
                "case_count": 2,
                "avg_continuation_chars": 12.5,
                "avg_unique_chars": 8.5,
                "task_type_counts": {"qa": 1, "summary": 1},
                "difficulty_counts": {"easy": 1, "medium": 1},
                "benchmark": {"suite_name": "demo-suite", "suite_version": "1", "language": "zh-CN"},
            }
        ),
        encoding="utf-8",
    )
    quality_dir = run_dir / "generation_quality"
    quality_dir.mkdir()
    (quality_dir / "generation_quality.json").write_text(
        json.dumps(
            {
                "source_type": "eval_suite",
                "summary": {
                    "overall_status": "pass",
                    "case_count": 2,
                    "pass_count": 2,
                    "warn_count": 0,
                    "fail_count": 0,
                    "avg_continuation_chars": 12.5,
                    "avg_unique_ratio": 0.62,
                    "avg_repeated_ngram_ratio": 0.1,
                    "max_repeat_run": 2,
                    "flag_summary": {"total_flags": 0, "flag_id_counts": {}, "flag_level_counts": {"fail": 0, "warn": 0}},
                },
                "cases": [{"name": "qa", "status": "pass"}, {"name": "summary", "status": "pass"}],
            }
        ),
        encoding="utf-8",
    )
    scorecard_dir = run_dir / "benchmark-scorecard"
    scorecard_dir.mkdir()
    (scorecard_dir / "benchmark_scorecard.json").write_text(
        json.dumps(
            {
                "summary": {
                    "overall_status": "pass",
                    "overall_score": 91.5,
                    "component_count": 6,
                    "rubric_status": "pass",
                    "rubric_avg_score": 94.0,
                    "weakest_rubric_case": "summary",
                    "weakest_rubric_score": 88.0,
                    "weakest_task_type": "summary",
                    "weakest_task_type_score": 88.0,
                    "weakest_difficulty": "medium",
                    "weakest_difficulty_score": 88.0,
                    "generation_quality_dominant_flag": None,
                    "generation_quality_total_flags": 0,
                }
            }
        ),
        encoding="utf-8",
    )
    return run_dir


class TrainingRunEvidenceTests(unittest.TestCase):
    def test_build_training_run_evidence_accepts_real_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))

            report = build_training_run_evidence(run_dir, generated_at="2026-05-17T00:00:00Z")

            self.assertEqual(report["summary"]["status"], "ready")
            self.assertEqual(report["summary"]["readiness_score"], 100)
            self.assertEqual(report["training"]["actual_last_step"], 2)
            self.assertEqual(report["training"]["best_val_loss"], 1.1)
            self.assertEqual(report["data"]["dataset_quality_status"], "pass")
            self.assertEqual(report["evaluation"]["case_count"], 2)
            self.assertEqual(report["evaluation"]["task_type_count"], 2)
            self.assertEqual(report["quality"]["overall_status"], "pass")
            self.assertEqual(report["summary"]["generation_quality_status"], "pass")
            self.assertEqual(report["scorecard"]["overall_status"], "pass")
            self.assertEqual(report["scorecard"]["overall_score"], 91.5)
            self.assertEqual(report["summary"]["benchmark_scorecard_status"], "pass")
            self.assertEqual(report["summary"]["eval_suite_case_count"], 2)
            self.assertTrue(any(item["key"] == "checkpoint" and item["exists"] for item in report["artifacts"]))

    def test_missing_checkpoint_blocks_promotion_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            (run_dir / "checkpoint.pt").unlink()

            report = build_training_run_evidence(run_dir)

            self.assertEqual(report["summary"]["status"], "blocked")
            self.assertGreater(report["summary"]["critical_missing_count"], 0)
            failed = [check["code"] for check in report["checks"] if check["status"] == "fail"]
            self.assertIn("checkpoint_present", failed)

    def test_missing_eval_suite_only_reviews_when_not_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            (run_dir / "eval_suite" / "eval_suite.json").unlink()

            report = build_training_run_evidence(run_dir)

            self.assertEqual(report["summary"]["status"], "review")
            self.assertEqual(report["summary"]["eval_suite_case_count"], 0)
            self.assertTrue(any(check["code"] == "eval_suite_present" and check["status"] == "warn" for check in report["checks"]))

    def test_missing_generation_quality_keeps_run_in_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            (run_dir / "generation_quality" / "generation_quality.json").unlink()

            report = build_training_run_evidence(run_dir)

            self.assertEqual(report["summary"]["status"], "review")
            self.assertFalse(report["summary"]["generation_quality_exists"])
            self.assertTrue(any(check["code"] == "generation_quality_present" and check["status"] == "warn" for check in report["checks"]))

    def test_missing_benchmark_scorecard_keeps_run_in_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            (run_dir / "benchmark-scorecard" / "benchmark_scorecard.json").unlink()

            report = build_training_run_evidence(run_dir)

            self.assertEqual(report["summary"]["status"], "review")
            self.assertFalse(report["summary"]["benchmark_scorecard_exists"])
            self.assertTrue(any(check["code"] == "benchmark_scorecard_present" and check["status"] == "warn" for check in report["checks"]))

    def test_write_outputs_and_render_html_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            report = build_training_run_evidence(run_dir, title="<Evidence>")

            outputs = write_training_run_evidence_outputs(report, Path(tmp) / "out")
            html = render_training_run_evidence_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("training_run_evidence", Path(outputs["json"]).name)
            self.assertIn("## Checks", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("## Evaluation", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("## Generation Quality", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("## Benchmark Scorecard", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("&lt;Evidence&gt;", html)
            self.assertNotIn("<h1><Evidence>", html)


if __name__ == "__main__":
    unittest.main()
