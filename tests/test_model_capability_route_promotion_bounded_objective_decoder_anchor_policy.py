from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy import (
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy,
    locate_decoder_anchor_probe,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_artifacts import (
    render_bounded_objective_decoder_anchor_policy_html,
    render_bounded_objective_decoder_anchor_policy_markdown,
    render_bounded_objective_decoder_anchor_policy_text,
    write_bounded_objective_decoder_anchor_policy_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_probe_artifacts import (
    write_bounded_objective_decoder_anchor_probe_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy import main as cli_main


class BoundedObjectiveDecoderAnchorPolicyTests(unittest.TestCase):
    def test_policy_selects_shortest_successful_anchor_and_blocks_promotion(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy(probe_report())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_ready")
        self.assertTrue(report["summary"]["bounded_objective_decoder_anchor_policy_ready"])
        self.assertEqual(report["summary"]["policy_case_count"], 2)
        self.assertEqual(report["summary"]["uncovered_case_count"], 0)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["policy_rows"][0]["profile_id"], "prefix_f")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "decoder_anchor_policy_only")
        self.assertEqual(resolve_exit_code(report, require_policy_ready=True), 0)

    def test_policy_fails_without_completion_signal(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy(probe_report(completion=False))

        self.assertEqual(report["status"], "fail")
        self.assertIn("completion_signal_present", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_policy_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            probe_outputs = write_bounded_objective_decoder_anchor_probe_outputs(probe_report(), root / "probe")
            self.assertEqual(locate_decoder_anchor_probe(Path(probe_outputs["json"]).parent), Path(probe_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy(probe_report())
            outputs = write_bounded_objective_decoder_anchor_policy_outputs(report, root / "policy")
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
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_JSON_FILENAME))
        self.assertIn("policy_case_count=2", render_bounded_objective_decoder_anchor_policy_text(report))
        self.assertIn("Guardrails", render_bounded_objective_decoder_anchor_policy_markdown(report))
        self.assertIn("Policy Rows", render_bounded_objective_decoder_anchor_policy_html(report))


def probe_report(*, completion: bool = True) -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_decoder_anchor_probe_ready": True,
            "case_count": 2,
            "probe_row_count": 4,
            "anchor_completion_success": completion,
        },
        "probe_rows": [
            probe_row("case-1", "prefix_f", "f", completion, ["fixed", "loss"] if completion else []),
            probe_row("case-1", "prefix_fixed_l", "fixed l", completion, ["loss"] if completion else []),
            probe_row("case-2", "prefix_f", "f", completion, ["fixed", "loss"] if completion else []),
            probe_row("case-2", "prefix_fixed_space", "fixed ", completion, ["loss"] if completion else []),
        ],
    }


def probe_row(case_id: str, profile_id: str, anchor: str, completion: bool, completion_hits: list[str]) -> dict:
    return {
        "case_id": case_id,
        "profile_id": profile_id,
        "anchor": anchor,
        "combined": f"{anchor}ixed loss",
        "completion_pass": completion,
        "new_text_pass": False,
        "completion_hit_terms": completion_hits,
        "new_text_hit_terms": ["loss"] if completion else [],
    }


if __name__ == "__main__":
    unittest.main()
