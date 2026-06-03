from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_benchmark_suite_artifacts import (
    write_model_capability_route_promotion_bounded_benchmark_suite_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import (
    build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision,
    locate_benchmark_suite,
    locate_failure_alignment_diagnostic,
    locate_repair_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_html,
    render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_markdown,
    render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import main as cli_main


def suite_report() -> dict:
    return {
        "status": "pass",
        "benchmark_suite": {
            "cases": [
                {"case_id": "case-1", "prompt_case": {"prompt": "Prompt 1\nAnswer:"}, "expected_terms": ["fixed", "loss"]},
                {"case_id": "case-2", "prompt_case": {"prompt": "Prompt 2\nAnswer:"}, "expected_terms": ["fixed", "loss"]},
            ]
        },
    }


def diagnostic_report() -> dict:
    return {"status": "pass", "summary": {"bounded_real_replay_failure_alignment_diagnostic_ready": True, "prompt_gap_count": 2}}


def seed_revision_report() -> dict:
    return {
        "status": "pass",
        "summary": {"bounded_real_replay_repair_seed_revision_ready": True, "example_count": 1},
        "seed_examples": [{"example_id": "seed-1", "case_id": "case-1", "prompt": "old", "completion": "fixed loss", "text": "oldfixed loss"}],
    }


class ModelCapabilityRoutePromotionBoundedRealReplayPromptAlignedSeedRevisionTests(unittest.TestCase):
    def test_builds_exact_prompt_seed_examples(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision(
            suite_report(),
            diagnostic_report(),
            seed_revision_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_ready")
        self.assertTrue(report["summary"]["prompt_aligned_seed_revision_ready"])
        self.assertEqual(report["summary"]["exact_prompt_answer_count"], 2)
        self.assertEqual(report["summary"]["added_example_count"], 4)
        self.assertTrue(any("Prompt 1" in row["text"] for row in report["seed_examples"]))
        self.assertEqual(resolve_exit_code(report, require_prompt_aligned_seed_ready=True), 0)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_outputs = write_model_capability_route_promotion_bounded_benchmark_suite_outputs(suite_report(), root / "suite")
            diagnostic_outputs = write_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_outputs(diagnostic_report(), root / "diagnostic")
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs(seed_revision_report(), root / "seed")
            self.assertEqual(locate_benchmark_suite(Path(suite_outputs["json"]).parent), Path(suite_outputs["json"]))
            self.assertEqual(locate_failure_alignment_diagnostic(Path(diagnostic_outputs["json"]).parent), Path(diagnostic_outputs["json"]))
            self.assertEqual(locate_repair_seed_revision(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision(suite_report(), diagnostic_report(), seed_revision_report())
            outputs = write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs(report, root / "prompt-seed")
            cli_main(
                [
                    "--benchmark-suite",
                    str(Path(suite_outputs["json"]).parent),
                    "--diagnostic",
                    str(Path(diagnostic_outputs["json"]).parent),
                    "--repair-seed-revision",
                    str(Path(seed_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-prompt-seed"),
                    "--require-prompt-aligned-seed-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertIn("prompt_aligned_seed_ready=True", render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_text(report))
        self.assertIn("Seed Examples", render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_markdown(report))
        self.assertIn("Exact prompts", render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_html(report))


if __name__ == "__main__":
    unittest.main()
