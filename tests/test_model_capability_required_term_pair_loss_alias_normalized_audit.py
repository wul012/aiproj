from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_normalized_audit import (
    build_model_capability_required_term_pair_loss_alias_normalized_audit,
    normalize_for_required_term,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_normalized_audit_artifacts import (
    render_model_capability_required_term_pair_loss_alias_normalized_audit_html,
    render_model_capability_required_term_pair_loss_alias_normalized_audit_markdown,
    render_model_capability_required_term_pair_loss_alias_normalized_audit_text,
    write_model_capability_required_term_pair_loss_alias_normalized_audit_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasNormalizedAuditTests(unittest.TestCase):
    def test_normalized_audit_reports_hidden_full_signal_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_normalized_audit(
                focus_fixture(),
                out_dir=root / "audit",
                source_path=root / "focus.json",
                generated_at="2026-05-30T17:00:00Z",
            )
            outputs = write_model_capability_required_term_pair_loss_alias_normalized_audit_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_normalized_audit_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_normalized_audit_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_normalized_audit_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_normalized_full_signal")
            self.assertEqual(report["summary"]["strict_hit_count"], 0)
            self.assertEqual(report["summary"]["normalized_hit_count"], 2)
            self.assertEqual(report["summary"]["normalization_gain_count"], 2)
            self.assertIn("normalized_full_coverage=True", text)
            self.assertIn("Normalized Audit", markdown)
            self.assertIn("MiniGPT loss-alias normalized audit", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_normalized_audit_no_hidden_signal(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_normalized_audit(
            {"status": "pass", "seed_reports": [seed_report("----", "....")]},
            out_dir=Path("out"),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_loss_alias_normalized_no_signal")
        self.assertEqual(report["summary"]["normalization_gain_count"], 0)

    def test_normalized_audit_fails_without_generation_rows(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_normalized_audit(
            {"status": "pass", "seed_reports": []},
            out_dir=Path("out"),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source loss-alias focus report has no generation rows", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_normalize_for_required_term_removes_formatting(self) -> None:
        self.assertEqual(normalize_for_required_term("lo s\ns!"), "loss")


def focus_fixture() -> dict[str, object]:
    return {"status": "pass", "seed_reports": [seed_report("los\ns\ns", "lo s\ns")]}


def seed_report(source_continuation: str, beta_continuation: str) -> dict[str, object]:
    return {
        "status": "pass",
        "settings": {"generation_seed": 515},
        "generation_rows": [
            generation_row("source-loss", "loss:", True, source_continuation),
            generation_row("heldout-beta-loss", "beta:", True, beta_continuation),
        ],
    }


def generation_row(case_id: str, prompt: str, is_focus: bool, continuation: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_type": "source" if case_id == "source-loss" else "heldout",
        "prompt": prompt,
        "expected_term": "loss",
        "is_focus_case": is_focus,
        "continuation": continuation,
        "continuation_hit": False,
        "continuation_preview": continuation.replace("\n", "\\n"),
    }
