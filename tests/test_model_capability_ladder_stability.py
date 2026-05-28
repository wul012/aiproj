from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.model_capability_ladder_stability import (
    build_model_capability_ladder_stability_report,
    parse_seed_list,
    summarize_stability,
)
from minigpt.model_capability_ladder_stability_artifacts import (
    render_model_capability_ladder_stability_markdown,
    render_model_capability_ladder_stability_text,
    write_model_capability_ladder_stability_outputs,
)
from scripts.run_model_capability_ladder_stability import resolve_exit_code, single_thread_env


class ModelCapabilityLadderStabilityTests(unittest.TestCase):
    def test_stability_summarizes_repeated_loss_only_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_ladder_stability_report(
                [
                    _ladder(seed=1337, loss_delta=-0.0031, score_delta=0.0, flag_delta=0.0),
                    _ladder(seed=2026, loss_delta=-0.0012, score_delta=0.0, flag_delta=0.0),
                ],
                out_dir=Path(tmp) / "stability",
                run_config={"seeds": [1337, 2026]},
                generated_at="2026-05-28T00:00:00Z",
            )
            stability = report["stability_summary"]
            text = render_model_capability_ladder_stability_text(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "capability_stability_ready")
            self.assertEqual(stability["decision"], "repeated_loss_improvement_without_eval_improvement")
            self.assertEqual(stability["loss_improvement_seed_count"], 2)
            self.assertEqual(stability["eval_improvement_seed_count"], 0)
            self.assertTrue(stability["all_successful_seeds_loss_improved"])
            self.assertFalse(stability["any_successful_seed_eval_improved"])
            self.assertEqual(stability["mean_best_val_loss_delta"], -0.0022)
            self.assertIn("stability_decision=repeated_loss_improvement_without_eval_improvement", text)
            self.assertIn("seed=value=2026", text)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_stability_records_some_eval_improvement(self) -> None:
        summary = summarize_stability(
            [
                {"status": "pass", "best_val_loss_delta": -0.2, "score_delta": 0.0, "generation_flags_delta": 0.0},
                {"status": "pass", "best_val_loss_delta": -0.1, "score_delta": 1.0, "generation_flags_delta": 0.0},
            ]
        )

        self.assertEqual(summary["decision"], "repeated_loss_with_some_eval_improvement")
        self.assertEqual(summary["eval_improvement_seed_count"], 1)
        self.assertTrue(summary["any_successful_seed_eval_improved"])

    def test_stability_fails_when_seed_count_or_delta_missing(self) -> None:
        report = build_model_capability_ladder_stability_report(
            [_ladder(seed=1337, loss_delta=None, score_delta=0.0, flag_delta=0.0, status="fail")],
            out_dir="demo",
            run_config={},
            generated_at="2026-05-28T00:00:00Z",
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("at least two seed ladders are required", report["issues"])
        self.assertIn("seed-1337 ladder status is fail", report["issues"])
        self.assertIn("seed-1337 best_val_loss_delta is missing", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_stability_writes_all_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_ladder_stability_report(
                [
                    _ladder(seed=1337, loss_delta=-0.2, score_delta=0.0, flag_delta=0.0),
                    _ladder(seed=2026, loss_delta=0.1, score_delta=0.0, flag_delta=0.0),
                ],
                out_dir=Path(tmp) / "stability",
                run_config={"seeds": [1337, 2026]},
                generated_at="2026-05-28T00:00:00Z",
            )

            outputs = write_model_capability_ladder_stability_outputs(report, Path(tmp) / "stability")
            markdown = render_model_capability_ladder_stability_markdown(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["seed_count"], 2)
            self.assertIn("seed", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT Model Capability Ladder Stability", markdown)
            self.assertIn("Mean loss delta", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_parse_seed_list_validates_unique_values(self) -> None:
        self.assertEqual(parse_seed_list("1337, 2026"), [1337, 2026])
        self.assertEqual(parse_seed_list([2, 1]), [2, 1])
        with self.assertRaises(ValueError):
            parse_seed_list("")
        with self.assertRaises(ValueError):
            parse_seed_list("1,1")

    def test_stability_runner_caps_cpu_thread_env(self) -> None:
        env = single_thread_env()

        self.assertEqual(env["OMP_NUM_THREADS"], "1")
        self.assertEqual(env["MKL_NUM_THREADS"], "1")
        self.assertEqual(env["OPENBLAS_NUM_THREADS"], "1")
        self.assertEqual(env["NUMEXPR_NUM_THREADS"], "1")


def _ladder(
    *,
    seed: int,
    loss_delta: float | None,
    score_delta: float,
    flag_delta: float,
    status: str = "pass",
) -> dict[str, object]:
    return {
        "status": status,
        "decision": "capability_ladder_ready" if status == "pass" else "fix_capability_ladder",
        "report_path": f"seed-{seed}/model_capability_ladder.json",
        "rung_count": 3,
        "successful_rung_count": 3 if status == "pass" else 0,
        "max_iters_values": [1, 2, 4],
        "run_config": {"seed": seed},
        "trend_summary": {
            "decision": "loss_improved_without_eval_improvement",
            "first_max_iters": 1,
            "last_max_iters": 4,
            "best_loss_max_iters": 4,
            "best_score_max_iters": 1,
            "best_val_loss_delta_first_to_last": loss_delta,
            "score_delta_first_to_last": score_delta,
            "generation_flags_delta_first_to_last": flag_delta,
        },
    }


if __name__ == "__main__":
    unittest.main()
