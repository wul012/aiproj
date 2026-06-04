from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay_artifacts import (
    write_bounded_objective_decoder_anchor_policy_replay_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review import (
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review,
    locate_decoder_anchor_policy_replay,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review_artifacts import (
    render_bounded_objective_decoder_anchor_policy_review_html,
    render_bounded_objective_decoder_anchor_policy_review_markdown,
    render_bounded_objective_decoder_anchor_policy_review_text,
    write_bounded_objective_decoder_anchor_policy_review_outputs,
)
from scripts.review_model_capability_route_promotion_bounded_objective_decoder_anchor_policy import main as cli_main


class BoundedObjectiveDecoderAnchorPolicyReviewTests(unittest.TestCase):
    def test_review_closes_assisted_anchor_path_when_new_text_still_fails(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review(policy_replay())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "close_bounded_objective_decoder_anchor_policy_as_capability_path")
        self.assertTrue(report["summary"]["bounded_objective_decoder_anchor_policy_review_ready"])
        self.assertTrue(report["summary"]["assisted_anchor_path_closed"])
        self.assertEqual(report["summary"]["selected_track"], "unassisted_objective_repair")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_branch_closed=True), 0)

    def test_review_detects_unassisted_recovery_for_holdout_review(self) -> None:
        replay = policy_replay()
        replay["summary"]["new_text_pass_count"] = 1
        report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review(replay)

        self.assertEqual(report["decision"], "review_bounded_objective_unassisted_recovery_before_promotion")
        self.assertFalse(report["summary"]["assisted_anchor_path_closed"])
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_branch_closed=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_outputs = write_bounded_objective_decoder_anchor_policy_replay_outputs(policy_replay(), root / "policy-replay")
            self.assertEqual(locate_decoder_anchor_policy_replay(Path(replay_outputs["json"]).parent), Path(replay_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review(policy_replay())
            outputs = write_bounded_objective_decoder_anchor_policy_review_outputs(report, root / "review")
            cli_main(
                [
                    "--policy-replay",
                    str(Path(replay_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-branch-closed",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REVIEW_JSON_FILENAME))
        self.assertIn("assisted_anchor_path_closed=True", render_bounded_objective_decoder_anchor_policy_review_text(report))
        self.assertIn("Recommendations", render_bounded_objective_decoder_anchor_policy_review_markdown(report))
        self.assertIn("Recommendations", render_bounded_objective_decoder_anchor_policy_review_html(report))


def policy_replay() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_decoder_anchor_policy_replay_ready": True,
            "case_count": 3,
            "policy_applied_case_count": 3,
            "policy_applied_pass_count": 3,
            "new_text_pass_count": 0,
            "policy_replay_success": True,
            "promotion_ready": False,
        },
        "replay_rows": [
            {"case_id": "case-1", "continuation": "ixed loss", "case_pass": True, "new_text_pass": False},
            {"case_id": "case-2", "continuation": "ixed loss", "case_pass": True, "new_text_pass": False},
            {"case_id": "case-3", "continuation": "ixed loss", "case_pass": True, "new_text_pass": False},
        ],
    }


if __name__ == "__main__":
    unittest.main()
