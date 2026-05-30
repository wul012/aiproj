from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_decode_cleanup import (
    build_model_capability_required_term_pair_loss_alias_decode_cleanup,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_decode_cleanup_artifacts import (
    render_model_capability_required_term_pair_loss_alias_decode_cleanup_html,
    render_model_capability_required_term_pair_loss_alias_decode_cleanup_markdown,
    render_model_capability_required_term_pair_loss_alias_decode_cleanup_text,
    write_model_capability_required_term_pair_loss_alias_decode_cleanup_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasDecodeCleanupTests(unittest.TestCase):
    def test_decode_cleanup_reports_remove_newlines_full_recovery(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_decode_cleanup(
            focus_report(),
            out_dir="out",
            source_path="focus.json",
            generated_at="2026-05-30T19:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_loss_alias_remove_newlines_cleanup_recovers_full")
        self.assertEqual(report["summary"]["decode_cleanup_decision"], "loss_alias_decode_cleanup_remove_newlines_full")
        self.assertEqual(report["summary"]["raw_hit_count"], 0)
        self.assertEqual(report["summary"]["remove_newlines_hit_count"], 2)
        self.assertEqual(report["summary"]["minimal_recovery_strategy"], "remove_newlines")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_decode_cleanup_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_decode_cleanup(
                focus_report(),
                out_dir=root / "cleanup",
            )
            outputs = write_model_capability_required_term_pair_loss_alias_decode_cleanup_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_decode_cleanup_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_decode_cleanup_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_decode_cleanup_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decode_cleanup_decision=loss_alias_decode_cleanup_remove_newlines_full", text)
            self.assertIn("Loss-Alias Decode Cleanup", markdown)
            self.assertIn("MiniGPT loss-alias decode cleanup", html)

    def test_decode_cleanup_fails_without_seed_reports(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_decode_cleanup(
            {"status": "pass", "seed_reports": []},
            out_dir="out",
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source loss-alias focus report has no seed reports", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)


def focus_report() -> dict[str, object]:
    return {
        "status": "pass",
        "seed_reports": [
            {
                "settings": {"generation_seed": 515},
                "generation_rows": [
                    generation_row("source-loss", "lo\ns\ns"),
                    generation_row("heldout-beta-loss", " los\ns"),
                ],
            }
        ],
    }


def generation_row(case_id: str, continuation: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_type": "source" if case_id == "source-loss" else "heldout",
        "alias_group": "source" if case_id == "source-loss" else "greek",
        "expected_term": "loss",
        "continuation": continuation,
        "continuation_hit": False,
        "normalized_hit": True,
        "normalization_gain": True,
    }
