from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison import (
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic import (
    BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic,
    locate_objective_replay_comparison,
    locate_objective_seed,
    locate_objective_training_run,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic_artifacts import (
    render_bounded_objective_replay_zero_hit_diagnostic_html,
    render_bounded_objective_replay_zero_hit_diagnostic_markdown,
    render_bounded_objective_replay_zero_hit_diagnostic_text,
    write_bounded_objective_replay_zero_hit_diagnostic_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_seed import BOUNDED_OBJECTIVE_SEED_JSON_FILENAME
from minigpt.model_capability_route_promotion_bounded_objective_training_run import BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from scripts.diagnose_model_capability_route_promotion_bounded_objective_replay_zero_hit import main as cli_main


class BoundedObjectiveReplayZeroHitDiagnosticTests(unittest.TestCase):
    def test_diagnoses_near_miss_zero_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("Answer with exactly two tokens: fixed loss\nanswer: fixed loss\n", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic(
                replay_comparison(),
                objective_seed(),
                training_run(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic_ready")
        self.assertTrue(report["summary"]["bounded_objective_zero_hit_diagnostic_ready"])
        self.assertEqual(report["summary"]["zero_hit_case_count"], 1)
        self.assertEqual(report["summary"]["near_miss_case_count"], 1)
        self.assertIn("near_miss_character_substitution", [row["cause_id"] for row in report["root_causes"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_diagnostic_fails_when_objective_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.txt"
            corpus.write_text("fixed loss\n", encoding="utf-8")
            replay = replay_comparison()
            replay["summary"]["objective_contract_recovered"] = True
            report = build_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic(
                replay,
                objective_seed(),
                training_run(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("objective_not_recovered", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("Answer with exactly two tokens: fixed loss\nanswer: fixed loss\n", encoding="utf-8")
            replay_path = root / "replay" / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME
            seed_path = root / "seed" / BOUNDED_OBJECTIVE_SEED_JSON_FILENAME
            training_path = root / "training" / BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME
            write_json_payload(replay_comparison(), replay_path)
            write_json_payload(objective_seed(), seed_path)
            write_json_payload(training_run(), training_path)
            self.assertEqual(locate_objective_replay_comparison(replay_path.parent), replay_path)
            self.assertEqual(locate_objective_seed(seed_path.parent), seed_path)
            self.assertEqual(locate_objective_training_run(training_path.parent), training_path)
            report = build_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic(
                replay_comparison(),
                objective_seed(),
                training_run(),
                corpus_path=corpus,
            )
            outputs = write_bounded_objective_replay_zero_hit_diagnostic_outputs(report, root / "out")
            cli_main(
                [
                    "--replay-comparison",
                    str(replay_path.parent),
                    "--objective-seed",
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
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("bounded_objective_zero_hit_diagnostic_ready=True", render_bounded_objective_replay_zero_hit_diagnostic_text(report))
        self.assertIn("Root Causes", render_bounded_objective_replay_zero_hit_diagnostic_markdown(report))
        self.assertIn("Root Causes", render_bounded_objective_replay_zero_hit_diagnostic_html(report))


def replay_comparison() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "zero_hit_case_count": 1,
        },
        "replay_rows": [
            {
                "case_id": "canonical_direct_completion",
                "prompt": "Answer with exactly two tokens: fixed loss\nanswer:",
                "continuation": " wixed w",
                "required_terms": ["fixed", "loss"],
                "hit_terms": [],
                "missed_terms": ["fixed", "loss"],
                "case_pass": False,
                "any_hit": False,
            }
        ],
    }


def objective_seed() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_seed_ready": True,
            "direct_example_count": 18,
            "example_count": 18,
        },
    }


def training_run() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_training_ready": True,
            "final_train_loss": 1.4,
            "final_val_loss": 1.7,
            "train_loss_delta": -1.5,
        },
    }


if __name__ == "__main__":
    unittest.main()
