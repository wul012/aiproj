from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision,
    locate_decoder_anchor_distribution_audit,
    locate_decoder_anchor_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision import main as cli_main


class RebalancedSeedRevisionTests(unittest.TestCase):
    def test_rebalances_carry_forward_and_direct_answer_shares(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision(
            seed_report(),
            audit_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_ready")
        self.assertTrue(report["summary"]["decoder_anchor_rebalanced_seed_revision_ready"])
        self.assertEqual(report["summary"]["source_example_count"], 14)
        self.assertEqual(report["summary"]["example_count"], 16)
        self.assertEqual(report["summary"]["dropped_carry_forward_count"], 2)
        self.assertEqual(report["summary"]["added_direct_answer_count"], 4)
        self.assertEqual(report["summary"]["carry_forward_share"], 0.25)
        self.assertEqual(report["summary"]["direct_answer_share"], 0.375)
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 0)

    def test_fails_when_audit_did_not_request_rebalance(self) -> None:
        audit = audit_report()
        audit["summary"]["rebalanced_seed_needed"] = False
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision(seed_report(), audit)

        self.assertEqual(report["status"], "fail")
        self.assertIn("distribution_audit_requires_rebalance", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs(seed_report(), root / "seed")
            audit_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_outputs(audit_report(), root / "audit")
            self.assertEqual(locate_decoder_anchor_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            self.assertEqual(locate_decoder_anchor_distribution_audit(Path(audit_outputs["json"]).parent), Path(audit_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision(seed_report(), audit_report())
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_outputs(report, root / "rebalanced")
            cli_main(
                [
                    "--decoder-anchor-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--distribution-audit",
                    str(Path(audit_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-rebalanced"),
                    "--require-seed-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertIn("direct_answer_share=0.375", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_text(report))
        self.assertIn("Rebalance Rows", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_markdown(report))
        self.assertIn("Direct share", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_html(report))


def seed_report() -> dict:
    examples = []
    for case_id in ["case-a", "case-b"]:
        for index in range(3):
            examples.append(example(case_id, f"carry-{index}", "carry_forward_prompt_aligned_seed", "p", "fixed loss"))
        examples.append(example(case_id, "direct", "unanchored_direct_answer", "p", "fixed loss"))
        examples.append(example(case_id, "bridge-f", "prefix_f_bridge", "pf", "ixed loss"))
        examples.append(example(case_id, "bridge-fixed", "prefix_fixed_space_bridge", "pfixed ", "loss"))
        examples.append(example(case_id, "bridge-l", "prefix_fixed_l_bridge", "pfixed l", "oss"))
    return {"status": "pass", "summary": {"decoder_anchor_seed_revision_ready": True}, "seed_examples": examples}


def audit_report() -> dict:
    return {
        "status": "pass",
        "summary": {"decoder_anchor_distribution_audit_ready": True, "rebalanced_seed_needed": True, "risk_count": 3},
        "bucket_rows": [
            {"bucket": "carry_forward", "count": 6, "share": 0.4286},
            {"bucket": "direct_answer", "count": 2, "share": 0.1429},
            {"bucket": "decoder_bridge", "count": 6, "share": 0.4286},
        ],
    }


def example(case_id: str, suffix: str, revision_type: str, prompt: str, completion: str) -> dict:
    return {
        "example_id": f"{case_id}-{suffix}",
        "case_id": case_id,
        "revision_type": revision_type,
        "prompt": prompt,
        "completion": completion,
        "text": f"{prompt}{completion}",
        "required_terms": ["fixed", "loss"],
        "guardrail": "test",
    }


if __name__ == "__main__":
    unittest.main()
