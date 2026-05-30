from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_first_token_preference import (
    build_model_capability_required_term_pair_first_token_preference,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_first_token_preference_artifacts import (
    render_model_capability_required_term_pair_first_token_preference_html,
    render_model_capability_required_term_pair_first_token_preference_markdown,
    render_model_capability_required_term_pair_first_token_preference_text,
    write_model_capability_required_term_pair_first_token_preference_outputs,
)


class ModelCapabilityRequiredTermPairFirstTokenPreferenceTests(unittest.TestCase):
    def test_diagnostic_confirms_answer_prefix_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_first_token_preference(
                refresh_fixture(Path(tmp)),
                out_dir=Path(tmp) / "diag",
                generated_at="2026-05-30T23:50:00Z",
                score_func=fake_score_answer_prefix,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "pair_first_token_answer_prefix_drift_confirmed")
            self.assertEqual(report["summary"]["answer_prefix_top_count"], 2)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_reports_expected_top_ranked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_first_token_preference(
                refresh_fixture(Path(tmp)),
                out_dir=Path(tmp) / "diag",
                score_func=fake_score_expected_top,
            )

            self.assertEqual(report["decision"], "pair_first_token_expected_terms_top_ranked")
            self.assertTrue(report["summary"]["expected_all_top"])

    def test_diagnostic_confirms_whitespace_prefix_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_first_token_preference(
                refresh_fixture(Path(tmp)),
                out_dir=Path(tmp) / "diag",
                score_func=fake_score_whitespace_prefix,
            )

            self.assertEqual(report["decision"], "pair_first_token_whitespace_prefix_drift_confirmed")
            self.assertEqual(report["summary"]["whitespace_prefix_top_count"], 2)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_first_token_preference(
                refresh_fixture(root),
                out_dir=root / "diag",
                score_func=fake_score_answer_prefix,
            )
            outputs = write_model_capability_required_term_pair_first_token_preference_outputs(report, root / "diag")
            text = render_model_capability_required_term_pair_first_token_preference_text(report)
            markdown = render_model_capability_required_term_pair_first_token_preference_markdown(report)
            html = render_model_capability_required_term_pair_first_token_preference_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("answer_prefix_top_count=2", text)
            self.assertIn("First-Token Preference", markdown)
            self.assertIn("MiniGPT first-token preference", html)


def refresh_fixture(root: Path) -> dict[str, object]:
    run_dir = root / "run"
    run_dir.mkdir()
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
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
                {"profile_id": "default", "term": "fixed", "continuation_preview": " ansssssssss"},
                {"profile_id": "default", "term": "loss", "continuation_preview": " ansssssssss"},
            ],
        },
    }


def fake_score_answer_prefix(context: dict[str, object]) -> dict[str, object]:
    expected = str(context["expected_term"])[0]
    expected_id = 2 if expected == "f" else 3
    return {
        "expected_first_text": expected,
        "expected_token_id": expected_id,
        "expected_probability": 0.12,
        "top_tokens": [
            {"rank": 1, "token_id": 1, "token_text": "a", "probability": 0.42},
            {"rank": 2, "token_id": expected_id, "token_text": expected, "probability": 0.12},
        ],
    }


def fake_score_expected_top(context: dict[str, object]) -> dict[str, object]:
    expected = str(context["expected_term"])[0]
    expected_id = 2 if expected == "f" else 3
    return {
        "expected_first_text": expected,
        "expected_token_id": expected_id,
        "expected_probability": 0.51,
        "top_tokens": [
            {"rank": 1, "token_id": expected_id, "token_text": expected, "probability": 0.51},
            {"rank": 2, "token_id": 1, "token_text": "a", "probability": 0.12},
        ],
    }


def fake_score_whitespace_prefix(context: dict[str, object]) -> dict[str, object]:
    expected = str(context["expected_term"])[0]
    expected_id = 2 if expected == "f" else 3
    return {
        "expected_first_text": expected,
        "expected_token_id": expected_id,
        "expected_probability": 0.08,
        "top_tokens": [
            {"rank": 1, "token_id": 1, "token_text": " ", "probability": 0.76},
            {"rank": 2, "token_id": expected_id, "token_text": expected, "probability": 0.08},
        ],
    }


if __name__ == "__main__":
    unittest.main()
