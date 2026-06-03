from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_benchmark_suite_artifacts import (
    write_model_capability_route_promotion_bounded_benchmark_suite_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic import (
    build_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic,
    locate_benchmark_suite,
    locate_checkpoint_comparison,
    locate_seed_revision,
    locate_training_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_html,
    render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_markdown,
    render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_text,
    write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_outputs,
)
from scripts.diagnose_model_capability_route_promotion_bounded_real_replay_failure_alignment import main as cli_main


def suite_report() -> dict:
    return {
        "status": "pass",
        "benchmark_suite": {
            "cases": [
                {
                    "case_id": "case-1",
                    "prompt_case": {"prompt": "Exact benchmark prompt\nAnswer:", "max_new_tokens": 24},
                    "expected_terms": ["fixed", "loss"],
                }
            ]
        },
    }


def comparison_report() -> dict:
    return {
        "status": "pass",
        "summary": {"promotion_ready": False, "repair_checkpoint_regressed": True, "pass_rate_delta": -0.4},
        "case_rows": [
            {
                "case_id": "case-1",
                "repair_pass": False,
                "repair_continuation": "not aligned",
                "repair_missed_terms": ["fixed", "loss"],
            }
        ],
    }


def seed_revision_report() -> dict:
    return {"status": "pass", "summary": {"bounded_real_replay_repair_seed_revision_ready": True, "example_count": 3}}


def training_revision_report() -> dict:
    return {"status": "pass", "summary": {"bounded_real_replay_repair_training_revision_ready": True, "final_val_loss": 3.9}}


class ModelCapabilityRoutePromotionBoundedRealReplayFailureAlignmentDiagnosticTests(unittest.TestCase):
    def test_diagnoses_prompt_corpus_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("Repair case: fixed loss\n", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic(
                suite_report(),
                comparison_report(),
                seed_revision_report(),
                training_revision_report(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_ready")
        self.assertEqual(report["summary"]["prompt_gap_count"], 1)
        self.assertEqual(report["case_diagnostics"][0]["diagnosis"], "benchmark_prompt_not_represented_in_training_corpus")
        self.assertTrue(any(row["cause_id"] == "benchmark_prompt_training_corpus_gap" for row in report["root_causes"]))
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("Repair case: fixed loss\n", encoding="utf-8")
            suite_outputs = write_model_capability_route_promotion_bounded_benchmark_suite_outputs(suite_report(), root / "suite")
            comparison_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs(comparison_report(), root / "comparison")
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs(seed_revision_report(), root / "seed")
            training_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_training_run_revision_outputs(training_revision_report(), root / "training")
            self.assertEqual(locate_benchmark_suite(Path(suite_outputs["json"]).parent), Path(suite_outputs["json"]))
            self.assertEqual(locate_checkpoint_comparison(Path(comparison_outputs["json"]).parent), Path(comparison_outputs["json"]))
            self.assertEqual(locate_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            self.assertEqual(locate_training_revision(Path(training_outputs["json"]).parent), Path(training_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic(
                suite_report(),
                comparison_report(),
                seed_revision_report(),
                training_revision_report(),
                corpus_path=corpus,
            )
            outputs = write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_outputs(report, root / "diagnostic")
            cli_main(
                [
                    "--benchmark-suite",
                    str(Path(suite_outputs["json"]).parent),
                    "--comparison",
                    str(Path(comparison_outputs["json"]).parent),
                    "--seed-revision",
                    str(Path(seed_outputs["json"]).parent),
                    "--training-revision",
                    str(Path(training_outputs["json"]).parent),
                    "--corpus",
                    str(corpus),
                    "--out-dir",
                    str(root / "cli-diagnostic"),
                    "--require-diagnostic-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("diagnostic_ready=True", render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_text(report))
        self.assertIn("Case Diagnostics", render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_markdown(report))
        self.assertIn("Root Causes", render_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_html(report))


if __name__ == "__main__":
    unittest.main()
