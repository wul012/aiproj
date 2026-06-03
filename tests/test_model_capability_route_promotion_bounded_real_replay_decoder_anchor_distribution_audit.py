from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit,
    locate_decoder_anchor_failure_diagnostic,
    locate_decoder_anchor_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs,
)
from scripts.audit_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution import main as cli_main


def seed_report() -> dict:
    examples = [
        {"case_id": "case-1", "revision_type": "carry_forward_prompt_aligned_seed", "prompt": "p", "completion": "fixed loss", "text": "pfixed loss"},
        {"case_id": "case-1", "revision_type": "carry_forward_prompt_aligned_seed", "prompt": "p", "completion": "fixed loss", "text": "pfixed loss"},
        {"case_id": "case-1", "revision_type": "unanchored_direct_answer", "prompt": "p", "completion": "fixed loss", "text": "pfixed loss"},
        {"case_id": "case-1", "revision_type": "prefix_f_bridge", "prompt": "pf", "completion": "ixed loss", "text": "pfixed loss"},
    ]
    return {"status": "pass", "summary": {"decoder_anchor_seed_revision_ready": True}, "seed_examples": examples}


def diagnostic_report() -> dict:
    return {"status": "pass", "summary": {"case_count": 1, "zero_hit_case_count": 1}}


class ModelCapabilityRoutePromotionBoundedRealReplayDecoderAnchorDistributionAuditTests(unittest.TestCase):
    def test_audit_flags_rebalance_need_from_distribution_and_zero_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("pfixed loss\n", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit(
                seed_report(),
                diagnostic_report(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_needs_rebalance")
        self.assertTrue(report["summary"]["decoder_anchor_distribution_audit_ready"])
        self.assertTrue(report["summary"]["rebalanced_seed_needed"])
        self.assertGreaterEqual(report["summary"]["risk_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_audit_ready=True), 0)

    def test_audit_fails_without_seed_examples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("fixed loss\n", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit(
                {"status": "pass", "seed_examples": []},
                diagnostic_report(),
                corpus_path=corpus,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("seed_examples_present", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_audit_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus.txt"
            corpus.write_text("pfixed loss\n", encoding="utf-8")
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs(seed_report(), root / "seed")
            diagnostic_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic_outputs(diagnostic_report(), root / "diagnostic")
            self.assertEqual(locate_decoder_anchor_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            self.assertEqual(locate_decoder_anchor_failure_diagnostic(Path(diagnostic_outputs["json"]).parent), Path(diagnostic_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit(
                seed_report(),
                diagnostic_report(),
                corpus_path=corpus,
            )
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_outputs(report, root / "audit")
            cli_main(
                [
                    "--decoder-anchor-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--failure-diagnostic",
                    str(Path(diagnostic_outputs["json"]).parent),
                    "--corpus",
                    str(corpus),
                    "--out-dir",
                    str(root / "cli-audit"),
                    "--require-audit-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("rebalanced_seed_needed=True", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_text(report))
        self.assertIn("Buckets", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_markdown(report))
        self.assertIn("Carry share", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_html(report))


if __name__ == "__main__":
    unittest.main()
