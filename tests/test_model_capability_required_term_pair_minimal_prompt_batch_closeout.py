from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_minimal_prompt_batch_closeout import (
    build_minimal_prompt_batch_closeout,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_batch_closeout_artifacts import (
    render_minimal_prompt_batch_closeout_html,
    render_minimal_prompt_batch_closeout_markdown,
    render_minimal_prompt_batch_closeout_text,
    write_minimal_prompt_batch_closeout_outputs,
)


class MinimalPromptBatchCloseoutTests(unittest.TestCase):
    def test_closeout_passes_for_three_training_negative_results(self) -> None:
        report = build_minimal_prompt_batch_closeout(
            [training_fixture("fixed-only", ["fixed"]), training_fixture("loss-only", ["loss"]), training_fixture("loss-only", ["loss"])],
            labels=["v696", "v699", "v702"],
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "minimal_prompt_batch_closed_without_pair_full")
        self.assertEqual(report["summary"]["report_count"], 3)
        self.assertEqual(report["summary"]["pair_full_report_count"], 0)
        self.assertEqual(report["summary"]["fixed_only_report_count"], 1)
        self.assertEqual(report["summary"]["loss_only_report_count"], 2)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "not_claimed")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_fails_when_pair_full_candidate_exists(self) -> None:
        report = build_minimal_prompt_batch_closeout(
            [training_fixture("fixed-only", ["fixed"]), training_fixture("pair-full", ["fixed", "loss"], pair_full=True), training_fixture("loss-only", ["loss"])],
            labels=["v696", "candidate", "v702"],
        )

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "minimal_prompt_pair_full_candidate_found")
        self.assertIn("pair_full_candidate_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_closeout_requires_three_reports(self) -> None:
        report = build_minimal_prompt_batch_closeout([training_fixture("fixed-only", ["fixed"])])

        self.assertEqual(report["status"], "fail")
        self.assertIn("too_few_reports", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_minimal_prompt_batch_closeout(
            [training_fixture("fixed-only", ["fixed"]), training_fixture("loss-only", ["loss"]), training_fixture("loss-only", ["loss"])],
            labels=["v696", "v699", "v702"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_minimal_prompt_batch_closeout_outputs(report, Path(tmp) / "closeout")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=minimal_prompt_batch_closed_without_pair_full", render_minimal_prompt_batch_closeout_text(report))
        self.assertIn("Evidence Rows", render_minimal_prompt_batch_closeout_markdown(report))
        self.assertIn("MiniGPT minimal prompt batch closeout", render_minimal_prompt_batch_closeout_html(report))


def training_fixture(branch_class: str, hit_terms: list[str], *, pair_full: bool = False) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "settings": {"corpus_mode": f"fixture-{branch_class}"},
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": pair_full,
        },
        "replay_report": {
            "variant_rows": [{"hit_terms": hit_terms}],
            "case_rows": [
                {"term": "fixed", "profile_id": "default", "generated_preview": "fixed=f"},
                {"term": "loss", "profile_id": "default", "generated_preview": "loss=l"},
            ],
        },
        "interpretation": {"model_quality_claim": "not_claimed"},
    }


if __name__ == "__main__":
    unittest.main()
