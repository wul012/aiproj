from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic,
    locate_unassisted_repair_replay_comparison,
    locate_unassisted_repair_seed,
    locate_unassisted_repair_training_run,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic_artifacts import (
    render_bounded_objective_unassisted_repair_zero_hit_diagnostic_html,
    render_bounded_objective_unassisted_repair_zero_hit_diagnostic_markdown,
    render_bounded_objective_unassisted_repair_zero_hit_diagnostic_text,
    write_bounded_objective_unassisted_repair_zero_hit_diagnostic_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.diagnose_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit import main as cli_main


class BoundedObjectiveUnassistedRepairZeroHitDiagnosticTests(unittest.TestCase):
    def test_diagnoses_unassisted_zero_hit_with_loss_fragment_near_miss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("Complete the objective response.\nanswer: fixed loss\n", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic(
                unassisted_replay_comparison(),
                unassisted_seed(),
                unassisted_training_run(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_zero_hit_diagnostic_ready"])
        self.assertFalse(report["summary"]["decoder_anchor_used"])
        self.assertEqual(report["summary"]["zero_hit_case_count"], 1)
        self.assertEqual(report["summary"]["near_miss_case_count"], 1)
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision")
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_diagnostic_fails_when_unassisted_training_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("fixed loss\n", encoding="utf-8")
            training = unassisted_training_run()
            training["summary"]["bounded_objective_unassisted_repair_training_ready"] = False
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic(
                unassisted_replay_comparison(),
                unassisted_seed(),
                training,
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("training_run_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("Complete the objective response.\nanswer: fixed loss\n", encoding="utf-8")
            replay_path = root / "replay" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_REPLAY_COMPARISON_JSON_FILENAME
            seed_path = root / "seed" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME
            training_path = root / "training" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_TRAINING_RUN_JSON_FILENAME
            write_json_payload(unassisted_replay_comparison(), replay_path)
            write_json_payload(unassisted_seed(), seed_path)
            write_json_payload(unassisted_training_run(), training_path)
            self.assertEqual(locate_unassisted_repair_replay_comparison(replay_path.parent), replay_path)
            self.assertEqual(locate_unassisted_repair_seed(seed_path.parent), seed_path)
            self.assertEqual(locate_unassisted_repair_training_run(training_path.parent), training_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic(
                unassisted_replay_comparison(),
                unassisted_seed(),
                unassisted_training_run(),
                corpus_path=corpus,
            )
            outputs = write_bounded_objective_unassisted_repair_zero_hit_diagnostic_outputs(report, root / "out")
            cli_main(
                [
                    "--replay-comparison",
                    str(replay_path.parent),
                    "--unassisted-repair-seed",
                    str(seed_path.parent),
                    "--training-run",
                    str(training_path.parent),
                    "--corpus",
                    str(corpus),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-diagnostic-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_zero_hit_diagnostic_ready=True", render_bounded_objective_unassisted_repair_zero_hit_diagnostic_text(report))
        self.assertIn("Root Causes", render_bounded_objective_unassisted_repair_zero_hit_diagnostic_markdown(report))
        self.assertIn("Root Causes", render_bounded_objective_unassisted_repair_zero_hit_diagnostic_html(report))


def unassisted_replay_comparison() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "zero_hit_case_count": 1,
        },
        "replay_rows": [
            {
                "case_id": "completion_label_surface",
                "prompt": "Complete the objective response.\nanswer:",
                "continuation": " los\n\nan",
                "required_terms": ["fixed", "loss"],
                "hit_terms": [],
                "missed_terms": ["fixed", "loss"],
                "case_pass": False,
                "any_hit": False,
            }
        ],
    }


def unassisted_seed() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_ready": True,
            "example_count": 24,
            "direct_example_count": 24,
            "neutral_prompt_example_count": 12,
            "decoder_anchor_example_count": 0,
        },
    }


def unassisted_training_run() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_training_ready": True,
            "final_train_loss": 2.125,
            "final_val_loss": 2.23,
            "train_loss_delta": -1.344,
        },
    }


if __name__ == "__main__":
    unittest.main()
