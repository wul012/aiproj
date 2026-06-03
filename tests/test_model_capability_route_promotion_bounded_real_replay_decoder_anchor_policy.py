from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy,
    locate_decoder_anchor_probe,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy import main as cli_main


def probe_report(*, completion: bool = True) -> dict:
    return {
        "status": "pass",
        "summary": {"decoder_anchor_probe_ready": True, "case_count": 2, "probe_row_count": 3},
        "probe_rows": [
            {
                "case_id": "case-1",
                "profile_id": "prefix_fixed_space",
                "anchor": "fixed ",
                "completion_pass": completion,
                "new_text_pass": True,
                "completion_hit_terms": ["loss"] if completion else [],
                "new_text_hit_terms": ["fixed", "loss"] if completion else [],
            },
            {
                "case_id": "case-1",
                "profile_id": "prefix_fixed_l",
                "anchor": "fixed l",
                "completion_pass": completion,
                "new_text_pass": True,
                "completion_hit_terms": ["loss"] if completion else [],
                "new_text_hit_terms": ["fixed", "loss"] if completion else [],
            },
            {
                "case_id": "case-2",
                "profile_id": "prefix_f",
                "anchor": "f",
                "completion_pass": False,
                "new_text_pass": False,
                "completion_hit_terms": [],
                "new_text_hit_terms": [],
            },
        ],
    }


class ModelCapabilityRoutePromotionBoundedRealReplayDecoderAnchorPolicyTests(unittest.TestCase):
    def test_policy_selects_shortest_successful_anchor_and_marks_partial_coverage(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy(probe_report())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_ready_with_partial_coverage")
        self.assertTrue(report["summary"]["decoder_anchor_policy_ready"])
        self.assertEqual(report["summary"]["policy_case_count"], 1)
        self.assertEqual(report["summary"]["uncovered_case_count"], 1)
        self.assertEqual(report["policy_rows"][0]["profile_id"], "prefix_fixed_space")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_policy_ready=True), 0)

    def test_policy_fails_without_completion_signal(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy(probe_report(completion=False))

        self.assertEqual(report["status"], "fail")
        self.assertIn("completion_signal_present", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_policy_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            probe_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_outputs(probe_report(), root / "probe")
            self.assertEqual(locate_decoder_anchor_probe(Path(probe_outputs["json"]).parent), Path(probe_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy(probe_report())
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_outputs(report, root / "policy")
            cli_main(
                [
                    "--decoder-anchor-probe",
                    str(Path(probe_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-policy"),
                    "--require-policy-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("policy_case_count=1", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_text(report))
        self.assertIn("Guardrails", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_markdown(report))
        self.assertIn("Policy Rows", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_html(report))


if __name__ == "__main__":
    unittest.main()
