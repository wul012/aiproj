from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic,
    locate_seed_revision,
    locate_seed_revision_replay_comparison,
    locate_seed_revision_training_run,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_artifacts import (
    render_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_html,
    render_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_markdown,
    render_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_text,
    write_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.diagnose_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit import main as cli_main


class BoundedObjectiveUnassistedRepairSeedRevisionPartialHitDiagnosticTests(unittest.TestCase):
    def test_diagnoses_fixed_only_partial_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("answer: fixed loss\ncompletion: fixed loss\n", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic(
                replay_comparison(),
                seed_revision(),
                training_run(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready"])
        self.assertEqual(report["summary"]["partial_hit_case_count"], 2)
        self.assertEqual(report["summary"]["zero_hit_case_count"], 1)
        self.assertEqual(report["summary"]["hit_terms"], ["fixed"])
        self.assertEqual(report["summary"]["missed_terms"], ["fixed", "loss"])
        self.assertIn("loss_term_not_stabilized", [row["cause_id"] for row in report["root_causes"]])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch")
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_diagnostic_fails_without_partial_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("fixed loss\n", encoding="utf-8")
            replay = replay_comparison()
            for row in replay["replay_rows"]:
                row["hit_terms"] = []
                row["missed_terms"] = ["fixed", "loss"]
                row["any_hit"] = False
            replay["summary"]["any_hit_case_count"] = 0
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic(
                replay,
                seed_revision(),
                training_run(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("partial_hit_present", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("answer: fixed loss\ncompletion: fixed loss\n", encoding="utf-8")
            replay_path = root / "replay" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_REPLAY_COMPARISON_JSON_FILENAME
            seed_path = root / "seed" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME
            training_path = root / "training" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_JSON_FILENAME
            write_json_payload(replay_comparison(), replay_path)
            write_json_payload(seed_revision(), seed_path)
            write_json_payload(training_run(), training_path)
            self.assertEqual(locate_seed_revision_replay_comparison(replay_path.parent), replay_path)
            self.assertEqual(locate_seed_revision(seed_path.parent), seed_path)
            self.assertEqual(locate_seed_revision_training_run(training_path.parent), training_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic(
                replay_comparison(),
                seed_revision(),
                training_run(),
                corpus_path=corpus,
            )
            outputs = write_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_outputs(report, root / "out")
            cli_main(
                [
                    "--replay-comparison",
                    str(replay_path.parent),
                    "--seed-revision",
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
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("partial_hit_case_count=2", render_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_text(report))
        self.assertIn("Root Causes", render_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_markdown(report))
        self.assertIn("Root Causes", render_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_html(report))


def replay_comparison() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "passed_case_count": 0,
            "any_hit_case_count": 2,
            "zero_hit_case_count": 1,
        },
        "replay_rows": [
            {
                "case_id": "canonical_direct_completion",
                "prompt": "answer:",
                "continuation": " fixed t",
                "required_terms": ["fixed", "loss"],
                "hit_terms": ["fixed"],
                "missed_terms": ["loss"],
                "case_pass": False,
                "any_hit": True,
            },
            {
                "case_id": "minimal_direct_completion",
                "prompt": "answer:",
                "continuation": " fixed t",
                "required_terms": ["fixed", "loss"],
                "hit_terms": ["fixed"],
                "missed_terms": ["loss"],
                "case_pass": False,
                "any_hit": True,
            },
            {
                "case_id": "completion_label_surface",
                "prompt": "completion:",
                "continuation": " ler: lo",
                "required_terms": ["fixed", "loss"],
                "hit_terms": [],
                "missed_terms": ["fixed", "loss"],
                "case_pass": False,
                "any_hit": False,
            },
        ],
    }


def seed_revision() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_ready": True,
            "example_count": 24,
            "neutral_prompt_example_count": 18,
            "decoder_anchor_example_count": 0,
        },
    }


def training_run() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_training_ready": True,
            "final_train_loss": 2.127,
            "final_val_loss": 2.299,
            "train_loss_delta": -1.356,
        },
    }


if __name__ == "__main__":
    unittest.main()
