from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import write_model_capability_route_promotion_bounded_real_replay_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic,
    locate_decoder_anchor_comparison,
    locate_decoder_anchor_replay,
    locate_decoder_anchor_seed_revision,
    locate_decoder_anchor_training_run,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run_outputs,
)
from scripts.diagnose_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure import main as cli_main


def replay_report() -> dict:
    prompt = "Prompt\nAnswer:"
    return {
        "status": "pass",
        "summary": {"case_count": 1, "passed_case_count": 0, "failed_case_count": 1, "pass_rate": 0.0, "model_route_quality_ready": False},
        "replay_rows": [
            {
                "case_id": "case-1",
                "prompt": prompt,
                "continuation": "f i x e",
                "expected_terms": ["fixed", "loss"],
                "hit_terms": [],
                "missed_terms": ["fixed", "loss"],
                "case_pass": False,
            }
        ],
    }


def comparison_report() -> dict:
    return {
        "status": "pass",
        "summary": {
            "promotion_ready": False,
            "decoder_anchor_checkpoint_regressed_from_baseline": True,
            "decoder_vs_baseline_pass_rate_delta": -0.4,
            "decoder_vs_prompt_pass_rate_delta": 0.0,
        },
    }


def seed_report() -> dict:
    prompt = "Prompt\nAnswer:"
    return {
        "status": "pass",
        "summary": {
            "decoder_anchor_seed_revision_ready": True,
            "bridge_example_count": 3,
            "unanchored_direct_example_count": 1,
        },
        "seed_examples": [{"text": f"{prompt}fixed loss", "prompt": prompt, "completion": "fixed loss"}],
    }


def training_report() -> dict:
    return {
        "status": "pass",
        "summary": {"decoder_anchor_training_ready": True, "final_val_loss": 4.2},
    }


class ModelCapabilityRoutePromotionBoundedRealReplayDecoderAnchorFailureDiagnosticTests(unittest.TestCase):
    def test_diagnoses_zero_hit_fragmentation_after_decoder_anchor_training(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("Prompt\nAnswer:fixed loss\n", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic(
                replay_report(),
                comparison_report(),
                seed_report(),
                training_report(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_ready")
        self.assertTrue(report["summary"]["decoder_anchor_failure_diagnostic_ready"])
        self.assertEqual(report["summary"]["zero_hit_case_count"], 1)
        self.assertEqual(report["summary"]["prompt_in_corpus_count"], 1)
        self.assertIn("decoder_anchor_examples_present_but_replay_zero_hit", [row["cause_id"] for row in report["root_causes"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_diagnostic_fails_when_comparison_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("Prompt\nAnswer:fixed loss\n", encoding="utf-8")
            bad_comparison = comparison_report()
            bad_comparison["status"] = "fail"
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic(
                replay_report(),
                bad_comparison,
                seed_report(),
                training_report(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("decoder_anchor_comparison_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("Prompt\nAnswer:fixed loss\n", encoding="utf-8")
            replay_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(replay_report(), root / "replay")
            comparison_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_outputs(comparison_report(), root / "comparison")
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs(seed_report(), root / "seed")
            training_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run_outputs(training_report(), root / "training")
            self.assertEqual(locate_decoder_anchor_replay(Path(replay_outputs["json"]).parent), Path(replay_outputs["json"]))
            self.assertEqual(locate_decoder_anchor_comparison(Path(comparison_outputs["json"]).parent), Path(comparison_outputs["json"]))
            self.assertEqual(locate_decoder_anchor_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            self.assertEqual(locate_decoder_anchor_training_run(Path(training_outputs["json"]).parent), Path(training_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic(
                replay_report(),
                comparison_report(),
                seed_report(),
                training_report(),
                corpus_path=corpus,
            )
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_outputs(report, root / "diagnostic")
            cli_main(
                [
                    "--decoder-anchor-replay",
                    str(Path(replay_outputs["json"]).parent),
                    "--comparison",
                    str(Path(comparison_outputs["json"]).parent),
                    "--decoder-anchor-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--training-run",
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
        self.assertIn("zero_hit_case_count=1", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_text(report))
        self.assertIn("Root Causes", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_markdown(report))
        self.assertIn("Zero hit", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_html(report))


if __name__ == "__main__":
    unittest.main()
