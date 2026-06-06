from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_candidate_promotion_packet import (
    RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME,
    build_randomized_holdout_candidate_promotion_packet,
    locate_randomized_holdout_dry_run,
    locate_randomized_holdout_real_replay,
    locate_randomized_holdout_replay_review,
    locate_randomized_holdout_suite,
    resolve_exit_code,
)
from minigpt.randomized_holdout_candidate_promotion_packet_artifacts import (
    render_randomized_holdout_candidate_promotion_packet_html,
    render_randomized_holdout_candidate_promotion_packet_markdown,
    render_randomized_holdout_candidate_promotion_packet_text,
    write_randomized_holdout_candidate_promotion_packet_outputs,
)
from minigpt.randomized_target_hidden_holdout_dry_run import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME
from minigpt.randomized_target_hidden_holdout_real_replay import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME
from minigpt.randomized_target_hidden_holdout_replay_review import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
from minigpt.randomized_target_hidden_holdout_suite import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from scripts.build_randomized_holdout_candidate_promotion_packet import main as cli_main


class RandomizedHoldoutCandidatePromotionPacketTests(unittest.TestCase):
    def test_clean_chain_builds_candidate_packet_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_inputs(Path(tmp))
            report = build_packet(paths)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_candidate_promotion_packet_ready")
        self.assertEqual(report["failed_count"], 0)
        self.assertTrue(report["summary"]["randomized_holdout_candidate_promotion_packet_ready"])
        self.assertEqual(report["summary"]["candidate_case_count"], 20)
        self.assertEqual(report["summary"]["random_seed"], 914)
        self.assertEqual(report["summary"]["pass_rate"], 1.0)
        self.assertEqual(report["summary"]["clean_randomized_case_count"], 20)
        self.assertTrue(report["summary"]["candidate_packet_authorized"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["model_quality_claim"], "candidate_packet_only")
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_candidate_promotion_packet")
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_promotion_ready=True), 1)

    def test_review_without_candidate_packet_authorization_blocks_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_inputs(root)
            review = replay_review()
            review["summary"]["approved_for_candidate_promotion_packet"] = False
            write_json_payload(review, paths["review"])
            report = build_packet(paths)

        self.assertEqual(report["status"], "fail")
        self.assertIn("candidate_packet_authorized", [issue["id"] for issue in report["issues"]])
        self.assertFalse(report["summary"]["randomized_holdout_candidate_promotion_packet_ready"])
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True), 1)

    def test_negative_control_passed_blocks_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_inputs(root)
            dry = dry_run()
            dry["summary"]["negative_control_passed"] = True
            dry["summary"]["negative_passed_case_count"] = 1
            write_json_payload(dry, paths["dry"])
            report = build_packet(paths)

        self.assertEqual(report["status"], "fail")
        self.assertIn("negative_control_rejected", [issue["id"] for issue in report["issues"]])

    def test_seed_mismatch_blocks_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_inputs(root)
            real = real_replay()
            real["summary"]["source_random_seed"] = 999
            write_json_payload(real, paths["real"])
            report = build_packet(paths)

        self.assertEqual(report["status"], "fail")
        self.assertIn("random_seed_consistent", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_inputs(root)
            self.assertEqual(locate_randomized_holdout_replay_review(paths["review"].parent), paths["review"])
            self.assertEqual(locate_randomized_holdout_real_replay(paths["real"].parent), paths["real"])
            self.assertEqual(locate_randomized_holdout_dry_run(paths["dry"].parent), paths["dry"])
            self.assertEqual(locate_randomized_holdout_suite(paths["suite"].parent), paths["suite"])
            report = build_packet(paths)
            outputs = write_randomized_holdout_candidate_promotion_packet_outputs(report, root / "out")
            cli_main(
                [
                    "--replay-review",
                    str(paths["review"].parent),
                    "--real-replay",
                    str(paths["real"].parent),
                    "--dry-run",
                    str(paths["dry"].parent),
                    "--holdout-suite",
                    str(paths["suite"].parent),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-packet-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_CANDIDATE_PROMOTION_PACKET_JSON_FILENAME))
        self.assertIn("randomized_holdout_candidate_promotion_packet_ready=True", render_randomized_holdout_candidate_promotion_packet_text(report))
        self.assertIn("Evidence Manifest", render_randomized_holdout_candidate_promotion_packet_markdown(report))
        self.assertIn("candidate promotion packet", render_randomized_holdout_candidate_promotion_packet_html(report))


def write_inputs(root: Path) -> dict[str, Path]:
    paths = {
        "review": root / "review" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
        "real": root / "real" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME,
        "dry": root / "dry" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME,
        "suite": root / "suite" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME,
    }
    write_json_payload(replay_review(), paths["review"])
    write_json_payload(real_replay(), paths["real"])
    write_json_payload(dry_run(), paths["dry"])
    write_json_payload(holdout_suite(), paths["suite"])
    return paths


def build_packet(paths: dict[str, Path]) -> dict[str, object]:
    from minigpt.randomized_holdout_candidate_promotion_packet import read_json_report

    return build_randomized_holdout_candidate_promotion_packet(
        read_json_report(paths["review"]),
        read_json_report(paths["real"]),
        read_json_report(paths["dry"]),
        read_json_report(paths["suite"]),
        replay_review_path=paths["review"],
        real_replay_path=paths["real"],
        dry_run_path=paths["dry"],
        holdout_suite_path=paths["suite"],
    )


def replay_review() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "randomized_target_hidden_holdout_replay_review_clean_signal_candidate_packet_required",
        "summary": {
            "randomized_target_hidden_holdout_replay_review_ready": True,
            "source_randomized_holdout_model_quality_ready": True,
            "case_count": 20,
            "passed_case_count": 20,
            "pass_rate": 1.0,
            "source_random_seed": 914,
            "source_randomized_case_factor": 2.0,
            "target_leakage_case_count": 0,
            "target_hidden_case_count": 20,
            "task_hint_case_count": 0,
            "unique_prompt_count": 20,
            "randomized_prompt_count": 20,
            "clean_randomized_case_count": 20,
            "approved_for_candidate_promotion_packet": True,
            "approved_for_promotion": False,
            "promotion_ready": False,
            "model_quality_claim": "randomized_target_hidden_holdout_clean_signal_reviewed",
            "next_step": "build_randomized_holdout_candidate_promotion_packet",
            "failed_check_count": 0,
        },
    }


def real_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "randomized_target_hidden_holdout_real_replay_passed_review_required",
        "summary": {
            "randomized_target_hidden_holdout_real_replay_ready": True,
            "case_count": 20,
            "source_random_seed": 914,
            "source_randomized_case_factor": 2.0,
            "source_unique_prompt_count": 20,
            "executed_case_count": 20,
            "passed_case_count": 20,
            "failed_case_count": 0,
            "any_hit_case_count": 20,
            "zero_hit_case_count": 0,
            "pass_rate": 1.0,
            "holdout_model_quality_ready": True,
            "randomized_holdout_model_quality_ready": True,
            "promotion_ready": False,
            "model_quality_claim": "randomized_target_hidden_holdout_replay_only",
            "next_step": "review_randomized_target_hidden_holdout_replay_result",
            "failed_check_count": 0,
        },
    }


def dry_run() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "randomized_target_hidden_holdout_dry_run_passed",
        "summary": {
            "randomized_target_hidden_holdout_dry_run_ready": True,
            "case_count": 20,
            "source_random_seed": 914,
            "source_randomized_case_factor": 2.0,
            "source_unique_prompt_count": 20,
            "positive_passed_case_count": 20,
            "negative_passed_case_count": 0,
            "negative_control_passed": False,
            "promotion_ready": False,
            "model_quality_claim": "dry_run_only",
            "next_step": "run_randomized_target_hidden_holdout_real_replay",
            "failed_check_count": 0,
        },
    }


def holdout_suite() -> dict[str, object]:
    cases = [{"case_id": f"randomized-target-hidden-{index:02d}"} for index in range(1, 21)]
    return {
        "status": "pass",
        "decision": "randomized_target_hidden_holdout_suite_ready",
        "summary": {
            "randomized_target_hidden_holdout_suite_ready": True,
            "source_case_count": 10,
            "candidate_case_count": 20,
            "random_seed": 914,
            "randomized_case_factor": 2.0,
            "tokenizer_covered_case_count": 20,
            "target_hidden_case_count": 20,
            "task_hint_case_count": 0,
            "unique_prompt_count": 20,
            "promotion_ready": False,
            "model_quality_claim": "suite_construction_only",
            "next_step": "dry_run_randomized_target_hidden_holdout",
            "failed_check_count": 0,
        },
        "benchmark_suite": {"cases": cases},
    }


if __name__ == "__main__":
    unittest.main()
