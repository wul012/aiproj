from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_probe import (
    build_model_capability_required_term_pair_loss_alias_newline_suppression_probe,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_probe_artifacts import (
    render_model_capability_required_term_pair_loss_alias_newline_suppression_html,
    render_model_capability_required_term_pair_loss_alias_newline_suppression_markdown,
    render_model_capability_required_term_pair_loss_alias_newline_suppression_text,
    write_model_capability_required_term_pair_loss_alias_newline_suppression_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasNewlineSuppressionProbeTests(unittest.TestCase):
    def test_newline_suppression_probe_recovers_strict_hits(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_newline_suppression_probe(
            focus_report(),
            out_dir="out",
            source_path="focus.json",
            generated_at="2026-05-30T20:00:00Z",
            generate_func=fake_generate,
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_loss_alias_newline_suppression_strict_recovery")
        self.assertEqual(report["summary"]["newline_suppression_decision"], "loss_alias_newline_suppression_strict_full_recovery")
        self.assertEqual(report["summary"]["baseline_strict_hit_count"], 0)
        self.assertEqual(report["summary"]["suppressed_strict_hit_count"], 2)
        self.assertTrue(report["summary"]["suppressed_strict_full_coverage"])
        self.assertEqual(report["summary"]["suppressed_strict_gain_count"], 2)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_newline_suppression_outputs_all_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_newline_suppression_probe(
                focus_report(),
                out_dir=root / "probe",
                generate_func=fake_generate,
            )
            outputs = write_model_capability_required_term_pair_loss_alias_newline_suppression_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_newline_suppression_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_newline_suppression_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_newline_suppression_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("newline_suppression_decision=loss_alias_newline_suppression_strict_full_recovery", text)
            self.assertIn("Loss-Alias Newline Suppression Probe", markdown)
            self.assertIn("MiniGPT loss-alias newline suppression", html)

    def test_newline_suppression_fails_without_generation_rows(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_newline_suppression_probe(
            {"status": "pass", "seed_reports": [{"generation_rows": []}]},
            out_dir="out",
            generate_func=fake_generate,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source loss-alias focus report has no generation rows", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)


def focus_report() -> dict[str, object]:
    return {
        "status": "pass",
        "settings": {"max_new_tokens": 12, "temperature": 0.2, "top_k": 1, "device": "cpu"},
        "seed_reports": [
            {
                "settings": {"generation_seed": 515},
                "training": {"checkpoint_path": "checkpoint.pt", "tokenizer_path": "tokenizer.json"},
                "generation_rows": [
                    generation_row("source-loss", "loss:", "lo\ns\ns", True),
                    generation_row("heldout-beta-loss", "beta:", "lo\ns\ns", False),
                ],
            }
        ],
    }


def generation_row(case_id: str, prompt: str, continuation: str, is_focus_case: bool) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_type": "source" if case_id == "source-loss" else "heldout",
        "alias_group": "source" if case_id == "source-loss" else "greek",
        "prompt": prompt,
        "expected_term": "loss",
        "is_focus_case": is_focus_case,
        "generation_seed": 515,
        "continuation": continuation,
        "continuation_hit": False,
        "strict_hit": False,
        "newline_cleanup_hit": True,
        "normalized_hit": True,
    }


def fake_generate(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    if request.get("exclude_token_texts"):
        return {"generated": prompt + "loss", "continuation": "loss", "excluded_token_count": 1}
    return {"generated": prompt + "lo\ns\ns", "continuation": "lo\ns\ns", "excluded_token_count": 0}
