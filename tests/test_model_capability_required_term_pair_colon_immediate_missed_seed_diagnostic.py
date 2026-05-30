from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic import (
    build_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_artifacts import (
    render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_html,
    render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_markdown,
    render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_text,
    write_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_outputs,
)


class ModelCapabilityRequiredTermPairColonImmediateMissedSeedDiagnosticTests(unittest.TestCase):
    def test_diagnostic_detects_missed_after_top_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic(
                stability_report(tmp),
                out_dir=Path(tmp) / "diagnostic",
                generated_at="2026-05-31T00:20:00Z",
                score_func=fake_all_expected_top,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_colon_immediate_missed_after_top_token")
            self.assertEqual(report["summary"]["missed_expected_top_count"], 1)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_detects_first_token_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic(
                stability_report(tmp),
                out_dir=Path(tmp) / "diagnostic",
                score_func=fake_loss_not_expected_top,
            )

            self.assertEqual(report["decision"], "required_term_pair_colon_immediate_first_token_gap")
            self.assertEqual(report["summary"]["missed_first_token_gap_count"], 1)

    def test_diagnostic_fails_when_seed_reports_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = stability_report(tmp)
            payload["seed_reports"] = []
            report = build_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic(
                payload,
                out_dir=Path(tmp) / "diagnostic",
                score_func=fake_all_expected_top,
            )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic(
                stability_report(tmp),
                out_dir=root / "diagnostic",
                score_func=fake_all_expected_top,
            )
            outputs = write_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_outputs(
                report,
                root / "diagnostic",
            )
            text = render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_text(report)
            markdown = render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_markdown(report)
            html = render_model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("missed_seed_count=1", text)
            self.assertIn("Missed-Seed Diagnostic", markdown)
            self.assertIn("MiniGPT colon-immediate missed-seed diagnostic", html)
            self.assertTrue(
                (
                    root
                    / "diagnostic"
                    / "first-token-reports"
                    / "seed-535"
                    / "model_capability_required_term_pair_first_token_preference.json"
                ).is_file()
            )


def stability_report(tmp: str) -> dict[str, object]:
    root = Path(tmp)
    return {
        "status": "pass",
        "seed_rows": [
            {
                "seed": 535,
                "status": "pass",
                "decision": "required_term_pair_coexistence_refresh_pair_full_observed",
                "pair_full_observed": True,
                "continuation_hit_count": 2,
                "out_dir": str(root / "seed-535"),
            },
            {
                "seed": 1535,
                "status": "pass",
                "decision": "required_term_pair_coexistence_refresh_no_pair_full",
                "pair_full_observed": False,
                "continuation_hit_count": 0,
                "out_dir": str(root / "seed-1535"),
            },
        ],
        "seed_reports": [
            refresh_report(root, 535),
            refresh_report(root, 1535),
        ],
    }


def refresh_report(root: Path, seed: int) -> dict[str, object]:
    run_dir = root / f"seed-{seed}" / "run"
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "out_dir": str(root / f"seed-{seed}"),
        "settings": {"seed": seed},
        "training": {
            "checkpoint_path": str(checkpoint),
            "tokenizer_path": str(tokenizer),
        },
        "replay_report": {
            "terms": [
                {"term": "fixed", "scaffold_prompt": "fixed:"},
                {"term": "loss", "scaffold_prompt": "loss:"},
            ],
            "case_rows": [
                {"term": "fixed", "profile_id": "default", "continuation_preview": "fixed"},
                {"term": "loss", "profile_id": "default", "continuation_preview": "other"},
            ],
        },
    }


def fake_all_expected_top(context: dict[str, object]) -> dict[str, object]:
    expected = str(context["expected_term"])[0]
    token_id = ord(expected)
    return {
        "expected_first_text": expected,
        "expected_token_id": token_id,
        "expected_probability": 0.9,
        "top_tokens": [{"rank": 1, "token_id": token_id, "token_text": expected, "probability": 0.9}],
    }


def fake_loss_not_expected_top(context: dict[str, object]) -> dict[str, object]:
    expected = str(context["expected_term"])[0]
    token_id = ord(expected)
    if str(context["expected_term"]) == "loss":
        return {
            "expected_first_text": expected,
            "expected_token_id": token_id,
            "expected_probability": 0.2,
            "top_tokens": [
                {"rank": 1, "token_id": ord("x"), "token_text": "x", "probability": 0.5},
                {"rank": 2, "token_id": token_id, "token_text": expected, "probability": 0.2},
            ],
        }
    return fake_all_expected_top(context)


if __name__ == "__main__":
    unittest.main()
