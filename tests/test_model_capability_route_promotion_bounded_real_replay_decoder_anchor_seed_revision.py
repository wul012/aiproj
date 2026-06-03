from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import write_model_capability_route_promotion_bounded_real_replay_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision,
    locate_policy_replay,
    locate_prompt_aligned_replay,
    locate_prompt_aligned_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision import main as cli_main


def prompt_aligned_seed_report() -> dict:
    return {
        "status": "pass",
        "summary": {"prompt_aligned_seed_revision_ready": True, "example_count": 1},
        "seed_examples": [
            {
                "example_id": "prompt-seed-1",
                "case_id": "case-1",
                "prompt": "Old prompt\nAnswer:",
                "completion": "fixed loss",
                "text": "Old prompt\nAnswer:fixed loss",
                "required_terms": ["fixed", "loss"],
            }
        ],
    }


def prompt_aligned_replay_report() -> dict:
    return {
        "status": "pass",
        "summary": {"case_count": 2},
        "replay_rows": [
            {"case_id": "case-1", "prompt": "Prompt 1\nAnswer:", "expected_terms": ["fixed", "loss"]},
            {"case_id": "case-2", "prompt": "Prompt 2\nAnswer:", "expected_terms": ["fixed", "loss"]},
        ],
    }


def policy_replay_report(*, success: bool = True) -> dict:
    return {
        "status": "pass",
        "summary": {"decoder_anchor_policy_replay_ready": True, "policy_replay_success": success},
        "replay_rows": [{"case_id": "case-1", "policy_applied": True, "case_pass": success}],
    }


class ModelCapabilityRoutePromotionBoundedRealReplayDecoderAnchorSeedRevisionTests(unittest.TestCase):
    def test_builds_decoder_anchor_seed_revision_examples(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision(
            prompt_aligned_seed_report(),
            prompt_aligned_replay_report(),
            policy_replay_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_ready")
        self.assertTrue(report["summary"]["decoder_anchor_seed_revision_ready"])
        self.assertEqual(report["summary"]["original_example_count"], 1)
        self.assertEqual(report["summary"]["added_example_count"], 8)
        self.assertEqual(report["summary"]["example_count"], 9)
        self.assertEqual(report["summary"]["bridge_example_count"], 6)
        self.assertEqual(report["summary"]["unanchored_direct_example_count"], 2)
        self.assertTrue(any(row["completion"] == "ixed loss" for row in report["seed_examples"]))
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 0)

    def test_fails_when_policy_replay_signal_is_missing(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision(
            prompt_aligned_seed_report(),
            prompt_aligned_replay_report(),
            policy_replay_report(success=False),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("policy_replay_partial_signal_present", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 1)

    def test_outputs_locators_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs(prompt_aligned_seed_report(), root / "seed")
            replay_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(prompt_aligned_replay_report(), root / "replay")
            policy_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_outputs(policy_replay_report(), root / "policy-replay")
            self.assertEqual(locate_prompt_aligned_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            self.assertEqual(locate_prompt_aligned_replay(Path(replay_outputs["json"]).parent), Path(replay_outputs["json"]))
            self.assertEqual(locate_policy_replay(Path(policy_outputs["json"]).parent), Path(policy_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision(
                prompt_aligned_seed_report(),
                prompt_aligned_replay_report(),
                policy_replay_report(),
            )
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs(report, root / "decoder-seed")
            corpus_text = Path(outputs["corpus"]).read_text(encoding="utf-8")
            cli_main(
                [
                    "--prompt-aligned-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--prompt-aligned-replay",
                    str(Path(replay_outputs["json"]).parent),
                    "--policy-replay",
                    str(Path(policy_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-decoder-seed"),
                    "--require-seed-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertIn("seed_ready=True", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_text(report))
        self.assertIn("Seed Examples", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_markdown(report))
        self.assertIn("Bridge", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_html(report))
        self.assertIn("fixed loss", corpus_text)
        self.assertIn("ixed loss", corpus_text)


if __name__ == "__main__":
    unittest.main()
