from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.model_capability_ladder import (
    build_model_capability_ladder_report,
    parse_max_iters_list,
    summarize_ladder_trend,
)
from minigpt.model_capability_ladder_artifacts import (
    render_model_capability_ladder_markdown,
    render_model_capability_ladder_text,
    write_model_capability_ladder_outputs,
)
from scripts.run_model_capability_ladder import resolve_exit_code, single_thread_env


class ModelCapabilityLadderTests(unittest.TestCase):
    def test_ladder_summarizes_loss_and_score_trend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_ladder_report(
                [
                    _summary(Path(tmp), max_iters=1, best_loss=5.2, final_loss=5.3, score=80.0, flags=2),
                    _summary(Path(tmp), max_iters=4, best_loss=4.8, final_loss=4.9, score=81.5, flags=1),
                ],
                out_dir=Path(tmp) / "ladder",
                run_config={"suite_name": "standard-zh", "max_iters_values": [1, 4]},
                generated_at="2026-05-28T00:00:00Z",
            )
            trend = report["trend_summary"]
            text = render_model_capability_ladder_text(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "capability_ladder_ready")
            self.assertEqual(report["rung_count"], 2)
            self.assertEqual(trend["decision"], "training_signal_and_eval_signal_improved")
            self.assertEqual(trend["best_loss_max_iters"], 4)
            self.assertEqual(trend["best_score_max_iters"], 4)
            self.assertEqual(trend["best_val_loss_delta_first_to_last"], -0.4)
            self.assertEqual(trend["score_delta_first_to_last"], 1.5)
            self.assertEqual(trend["generation_flags_delta_first_to_last"], -1.0)
            self.assertTrue(trend["best_val_loss_monotonic_non_increasing"])
            self.assertTrue(trend["score_monotonic_non_decreasing"])
            self.assertIn("best_val_loss_delta=-0.4", text)
            self.assertIn("rung=max_iters=4", text)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_ladder_flags_failed_or_incomplete_rungs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_ladder_report(
                [_summary(Path(tmp), max_iters=1, best_loss=None, final_loss=None, score=80.0, flags=2, status="fail")],
                out_dir=Path(tmp) / "ladder",
                run_config={},
                generated_at="2026-05-28T00:00:00Z",
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("at least two ladder rungs are required", report["issues"])
            self.assertIn("max-iters-1 status is fail", report["issues"])
            self.assertIn("max-iters-1 best_val_loss is missing", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_ladder_writes_all_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_ladder_report(
                [
                    _summary(root, max_iters=1, best_loss=5.2, final_loss=5.3, score=80.0, flags=2),
                    _summary(root, max_iters=2, best_loss=5.0, final_loss=5.1, score=80.0, flags=2),
                ],
                out_dir=root / "ladder",
                run_config={"suite_name": "standard-zh"},
                generated_at="2026-05-28T00:00:00Z",
            )

            outputs = write_model_capability_ladder_outputs(report, root / "ladder")
            markdown = render_model_capability_ladder_markdown(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["rung_count"], 2)
            self.assertIn("max_iters", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT Model Capability Ladder", markdown)
            self.assertIn("Loss delta", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_parse_max_iters_list_validates_unique_positive_values(self) -> None:
        self.assertEqual(parse_max_iters_list("4, 1,2"), [1, 2, 4])
        self.assertEqual(parse_max_iters_list([3, 1]), [1, 3])
        with self.assertRaises(ValueError):
            parse_max_iters_list("")
        with self.assertRaises(ValueError):
            parse_max_iters_list("1,1")
        with self.assertRaises(ValueError):
            parse_max_iters_list("0,2")

    def test_trend_can_report_loss_only_improvement(self) -> None:
        trend = summarize_ladder_trend(
            [
                {"status": "pass", "max_iters": 1, "best_val_loss": 5.3, "scorecard_overall_score": 80.0, "generation_quality_total_flags": 0},
                {"status": "pass", "max_iters": 4, "best_val_loss": 5.1, "scorecard_overall_score": 80.0, "generation_quality_total_flags": 0},
            ]
        )

        self.assertEqual(trend["decision"], "loss_improved_without_eval_improvement")
        self.assertEqual(trend["best_val_loss_delta_first_to_last"], -0.2)
        self.assertEqual(trend["score_delta_first_to_last"], 0.0)

    def test_ladder_runner_caps_cpu_thread_env(self) -> None:
        env = single_thread_env()

        self.assertEqual(env["OMP_NUM_THREADS"], "1")
        self.assertEqual(env["MKL_NUM_THREADS"], "1")
        self.assertEqual(env["OPENBLAS_NUM_THREADS"], "1")
        self.assertEqual(env["NUMEXPR_NUM_THREADS"], "1")


def _summary(
    root: Path,
    *,
    max_iters: int,
    best_loss: float | None,
    final_loss: float | None,
    score: float,
    flags: int,
    status: str = "pass",
) -> dict[str, object]:
    run_dir = root / f"run-{max_iters}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "checkpoint.pt").write_text("checkpoint", encoding="utf-8")
    return {
        "status": status,
        "decision": "evidence-ready" if status == "pass" else "fix-smoke-chain",
        "out_dir": str(run_dir.parent),
        "run_dir": str(run_dir),
        "summary_path": str(run_dir.parent / "tiny_standard_benchmark_smoke_summary.json"),
        "max_iters": max_iters,
        "artifacts": {"checkpoint_exists": status == "pass"},
        "training": {"best_val_loss": best_loss, "final_val_loss": final_loss},
        "eval_suite": {"case_count": 10},
        "generation_quality": {"overall_status": "pass", "total_flags": flags},
        "pair_batch": {"same_checkpoint_baseline": True},
        "benchmark_scorecard": {"overall_status": "pass", "overall_score": score},
        "commands": [{"name": "train", "status": status}],
    }


if __name__ == "__main__":
    unittest.main()
