from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_segment_audit import (
    build_model_capability_required_term_pair_loss_alias_segment_audit,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_segment_audit_artifacts import (
    render_model_capability_required_term_pair_loss_alias_segment_audit_html,
    render_model_capability_required_term_pair_loss_alias_segment_audit_markdown,
    render_model_capability_required_term_pair_loss_alias_segment_audit_text,
    write_model_capability_required_term_pair_loss_alias_segment_audit_outputs,
)
from minigpt.tokenizer import CharTokenizer


class ModelCapabilityRequiredTermPairLossAliasSegmentAuditTests(unittest.TestCase):
    def test_segment_audit_classifies_newline_split_loss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_loss_alias_segment_audit(
                focus_report(Path(tmp)),
                out_dir="out",
                source_path="focus.json",
                generated_at="2026-05-30T18:00:00Z",
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_newline_segment_boundary")
            self.assertEqual(report["summary"]["segment_audit_decision"], "loss_alias_segment_newline_split")
            self.assertEqual(report["summary"]["normalization_gain_count"], 1)
            self.assertEqual(report["summary"]["newline_gain_count"], 1)
            self.assertEqual(report["summary"]["tokenizer_loaded_count"], 1)
            self.assertEqual(report["case_rows"][0]["separator_kind"], "newline")
            self.assertTrue(report["case_rows"][0]["tokenizer_loaded"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_segment_audit_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_segment_audit(
                focus_report(root),
                out_dir=root / "audit",
            )
            outputs = write_model_capability_required_term_pair_loss_alias_segment_audit_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_segment_audit_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_segment_audit_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_segment_audit_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("segment_audit_decision=loss_alias_segment_newline_split", text)
            self.assertIn("Loss-Alias Segment Audit", markdown)
            self.assertIn("MiniGPT loss-alias segment audit", html)

    def test_segment_audit_fails_without_seed_reports(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_segment_audit(
            {"status": "pass", "seed_reports": []},
            out_dir="out",
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source loss-alias focus report has no seed reports", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)


def focus_report(root: Path) -> dict[str, object]:
    tokenizer_path = root / "tokenizer.json"
    CharTokenizer.train("loss\n").save(tokenizer_path)
    return {
        "status": "pass",
        "out_dir": str(root),
        "seed_reports": [
            {
                "settings": {"generation_seed": 515},
                "training": {"tokenizer_path": str(tokenizer_path)},
                "generation_rows": [
                    {
                        "case_id": "source-loss",
                        "case_type": "source",
                        "alias_group": "source",
                        "expected_term": "loss",
                        "continuation": "lo\ns\ns",
                        "continuation_hit": False,
                        "normalized_hit": True,
                        "normalization_gain": True,
                    }
                ],
            }
        ],
    }
