from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_repeat import (
    build_model_capability_required_term_pair_loss_alias_newline_suppression_repeat,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_repeat_artifacts import (
    render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_html,
    render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_markdown,
    render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_text,
    write_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasNewlineSuppressionRepeatTests(unittest.TestCase):
    def test_repeat_reports_stable_strict_recovery_across_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = [write_focus_report(root / "focus-a"), write_focus_report(root / "focus-b")]
            report = build_model_capability_required_term_pair_loss_alias_newline_suppression_repeat(
                sources,
                out_dir=root / "repeat",
                generated_at="2026-05-30T21:00:00Z",
                generate_func=fake_generate,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_newline_suppression_stable_strict_recovery")
            self.assertEqual(report["summary"]["source_count"], 2)
            self.assertEqual(report["summary"]["suppressed_strict_full_source_count"], 2)
            self.assertEqual(report["summary"]["baseline_strict_full_source_count"], 0)
            self.assertEqual(report["summary"]["suppressed_strict_gain_count"], 4)
            self.assertTrue(report["summary"]["stable_suppressed_strict_full_coverage"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_repeat_outputs_all_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_focus_report(root / "focus-a")
            report = build_model_capability_required_term_pair_loss_alias_newline_suppression_repeat(
                [source],
                out_dir=root / "repeat",
                generate_func=fake_generate,
            )
            outputs = write_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("newline_suppression_repeat_decision=loss_alias_newline_suppression_repeat_stable_strict_recovery", text)
            self.assertIn("Loss-Alias Newline Suppression Repeat", markdown)
            self.assertIn("MiniGPT loss-alias newline suppression repeat", html)

    def test_repeat_fails_for_missing_source(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_newline_suppression_repeat(
            ["missing-focus-report"],
            out_dir="out",
            generate_func=fake_generate,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source loss-alias focus report does not exist", report["issues"][0])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)


def write_focus_report(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "model_capability_required_term_pair_loss_alias_focus.json"
    path.write_text(json.dumps(focus_report(), ensure_ascii=False), encoding="utf-8")
    return path


def focus_report() -> dict[str, object]:
    return {
        "status": "pass",
        "settings": {"max_new_tokens": 12, "temperature": 0.2, "top_k": 1, "device": "cpu"},
        "seed_reports": [
            {
                "settings": {"generation_seed": 515},
                "training": {"checkpoint_path": "checkpoint.pt", "tokenizer_path": "tokenizer.json"},
                "generation_rows": [
                    generation_row("source-loss", "loss:", True),
                    generation_row("heldout-beta-loss", "beta:", False),
                ],
            }
        ],
    }


def generation_row(case_id: str, prompt: str, is_focus_case: bool) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_type": "source" if case_id == "source-loss" else "heldout",
        "alias_group": "source" if case_id == "source-loss" else "greek",
        "prompt": prompt,
        "expected_term": "loss",
        "is_focus_case": is_focus_case,
        "generation_seed": 515,
        "continuation": "lo\ns\ns",
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
