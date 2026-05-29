from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.model_capability_token_budget_stability import (
    build_model_capability_token_budget_stability_report,
    summarize_token_budget_stability,
)
from minigpt.model_capability_token_budget_stability_artifacts import (
    render_model_capability_token_budget_stability_markdown,
    render_model_capability_token_budget_stability_text,
    write_model_capability_token_budget_stability_outputs,
)
from scripts.run_model_capability_token_budget_stability import resolve_exit_code, single_thread_env


class ModelCapabilityTokenBudgetStabilityTests(unittest.TestCase):
    def test_stability_summarizes_repeated_token_relief_without_score_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_token_budget_stability_report(
                [
                    _probe(seed=1337, token_delta=-9.0, persistent_delta=-9.0, score_delta=0.0, pass_delta=0.0),
                    _probe(seed=2026, token_delta=-7.0, persistent_delta=-7.0, score_delta=0.0, pass_delta=0.0),
                ],
                out_dir=Path(tmp) / "stability",
                run_config={"seeds": [1337, 2026], "command_failure_count": 0},
                generated_at="2026-05-29T00:00:00Z",
            )
            stability = report["stability_summary"]
            text = render_model_capability_token_budget_stability_text(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "token_budget_stability_ready")
            self.assertEqual(stability["decision"], "repeated_token_budget_relief_without_score_progress")
            self.assertEqual(stability["token_relief_seed_count"], 2)
            self.assertEqual(stability["score_or_pass_progress_seed_count"], 0)
            self.assertTrue(stability["all_successful_seeds_token_relief"])
            self.assertFalse(stability["any_successful_seed_score_or_pass_progress"])
            self.assertEqual(stability["mean_token_budget_or_shape_limit_delta"], -8.0)
            self.assertIn("stability_decision=repeated_token_budget_relief_without_score_progress", text)
            self.assertIn("seed=value=2026", text)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_stability_records_some_score_or_pass_progress(self) -> None:
        summary = summarize_token_budget_stability(
            [
                _row(seed=1337, token_delta=-9.0, persistent_delta=-9.0, score_delta=0.0, pass_delta=0.0),
                _row(seed=2026, token_delta=-7.0, persistent_delta=-6.0, score_delta=1.0, pass_delta=1.0),
            ]
        )

        self.assertEqual(summary["decision"], "repeated_token_budget_relief_with_some_score_progress")
        self.assertEqual(summary["score_or_pass_progress_seed_count"], 1)
        self.assertTrue(summary["any_successful_seed_score_or_pass_progress"])

    def test_stability_fails_when_seed_count_or_delta_missing(self) -> None:
        report = build_model_capability_token_budget_stability_report(
            [
                _probe(
                    seed=1337,
                    token_delta=None,
                    persistent_delta=-1.0,
                    score_delta=0.0,
                    pass_delta=0.0,
                    status="fail",
                )
            ],
            out_dir="demo",
            run_config={"command_failure_count": 1},
            generated_at="2026-05-29T00:00:00Z",
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("at least two token budget probe seeds are required", report["issues"])
        self.assertIn("one or more token budget probe commands failed", report["issues"])
        self.assertIn("seed-1337 token budget probe status is fail", report["issues"])
        self.assertIn("seed-1337 token_budget_or_shape_limit_delta is missing", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_stability_writes_all_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_token_budget_stability_report(
                [
                    _probe(seed=1337, token_delta=-9.0, persistent_delta=-9.0, score_delta=0.0, pass_delta=0.0),
                    _probe(seed=2026, token_delta=0.0, persistent_delta=0.0, score_delta=0.0, pass_delta=0.0),
                ],
                out_dir=Path(tmp) / "stability",
                run_config={"seeds": [1337, 2026], "command_failure_count": 0},
                generated_at="2026-05-29T00:00:00Z",
            )

            outputs = write_model_capability_token_budget_stability_outputs(report, Path(tmp) / "stability")
            markdown = render_model_capability_token_budget_stability_markdown(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["seed_count"], 2)
            self.assertIn("seed", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT Model Capability Token Budget Stability", markdown)
            self.assertIn("Mean token stall delta", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_stability_runner_caps_cpu_thread_env(self) -> None:
        env = single_thread_env()

        self.assertEqual(env["OMP_NUM_THREADS"], "1")
        self.assertEqual(env["MKL_NUM_THREADS"], "1")
        self.assertEqual(env["OPENBLAS_NUM_THREADS"], "1")
        self.assertEqual(env["NUMEXPR_NUM_THREADS"], "1")


def _probe(
    *,
    seed: int,
    token_delta: float | None,
    persistent_delta: float,
    score_delta: float,
    pass_delta: float,
    status: str = "pass",
) -> dict[str, object]:
    return {
        "status": status,
        "decision": "token_budget_probe_ready" if status == "pass" else "fix_token_budget_probe",
        "report_path": f"seed-{seed}/model_capability_token_budget_probe.json",
        "token_budget_count": 2,
        "run_config": {"seed": seed},
        "summary": {
            "decision": "longer_token_budget_reduces_eval_stall",
            "baseline_token_cap": 4,
            "largest_token_cap": 12,
            "token_budget_or_shape_limit_delta": token_delta,
            "persistent_fail_count_delta": persistent_delta,
            "score_improved_count_delta": score_delta,
            "pass_transition_count_delta": pass_delta,
            "avg_score_delta_change": 0.0,
        },
    }


def _row(
    *,
    seed: int,
    token_delta: float,
    persistent_delta: float,
    score_delta: float,
    pass_delta: float,
) -> dict[str, object]:
    return {
        "seed": seed,
        "status": "pass",
        "token_budget_or_shape_limit_delta": token_delta,
        "persistent_fail_count_delta": persistent_delta,
        "score_improved_count_delta": score_delta,
        "pass_transition_count_delta": pass_delta,
        "avg_score_delta_change": 0.0,
    }


if __name__ == "__main__":
    unittest.main()
