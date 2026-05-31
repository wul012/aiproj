from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_refresh_forced_choice import (
    build_model_capability_required_term_pair_refresh_forced_choice,
    locate_pair_refresh_forced_choice_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_refresh_forced_choice_artifacts import (
    render_model_capability_required_term_pair_refresh_forced_choice_html,
    render_model_capability_required_term_pair_refresh_forced_choice_markdown,
    render_model_capability_required_term_pair_refresh_forced_choice_text,
    write_model_capability_required_term_pair_refresh_forced_choice_outputs,
)


class ModelCapabilityRequiredTermPairRefreshForcedChoiceTests(unittest.TestCase):
    def test_forced_choice_detects_collapse_candidate(self) -> None:
        report = build_model_capability_required_term_pair_refresh_forced_choice(
            refresh_report_fixture(),
            out_dir="out",
            generated_at="2026-05-31T04:40:00Z",
            score_func=fake_score({"fixed": "loss", "loss": "loss"}),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_refresh_forced_choice_preference_collapse")
        self.assertEqual(report["summary"]["expected_best_count"], 1)
        self.assertEqual(report["summary"]["collapse_candidate"], "loss")
        self.assertEqual(report["prompt_rows"][0]["best_candidate_term"], "loss")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_forced_choice_reports_internal_match(self) -> None:
        report = build_model_capability_required_term_pair_refresh_forced_choice(
            refresh_report_fixture(),
            out_dir="out",
            score_func=fake_score({"fixed": "fixed", "loss": "loss"}),
        )

        self.assertEqual(report["decision"], "required_term_pair_refresh_forced_choice_internal_match")
        self.assertTrue(report["summary"]["forced_choice_full_match"])

    def test_invalid_source_fails_require_pass(self) -> None:
        report = build_model_capability_required_term_pair_refresh_forced_choice(
            {"training": {}, "replay_report": {"case_rows": []}},
            out_dir="out",
            score_func=fake_score({}),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("refresh report has no training object", report["issues"])
        self.assertIn("refresh report has fewer than two terms to compare", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_refresh_forced_choice(
                refresh_report_fixture(),
                out_dir=root / "forced-choice",
                score_func=fake_score({"fixed": "loss", "loss": "loss"}),
            )
            outputs = write_model_capability_required_term_pair_refresh_forced_choice_outputs(report, root / "forced-choice")
            text = render_model_capability_required_term_pair_refresh_forced_choice_text(report)
            markdown = render_model_capability_required_term_pair_refresh_forced_choice_markdown(report)
            html = render_model_capability_required_term_pair_refresh_forced_choice_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("collapse_candidate=loss", text)
            self.assertIn("Required-Term Pair Refresh Forced-Choice", markdown)
            self.assertIn("MiniGPT refresh forced-choice", html)

    def test_locate_prefers_nested_refresh_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "seed-reports" / "seed-1535"
            nested.mkdir(parents=True)
            source = nested / "model_capability_required_term_pair_coexistence_refresh.json"
            source.write_text("{}", encoding="utf-8")

            self.assertEqual(locate_pair_refresh_forced_choice_source(root), source)


def refresh_report_fixture() -> dict[str, object]:
    return {
        "training": {
            "checkpoint_path": "checkpoint.pt",
            "tokenizer_path": "tokenizer.json",
        },
        "replay_report": {
            "case_rows": [
                {"term": "fixed", "prompt": "fixed="},
                {"term": "loss", "prompt": "loss="},
            ]
        },
    }


def fake_score(best_by_prompt: dict[str, str]):
    def _score(context: dict[str, object]) -> dict[str, object]:
        prompt_term = str(context["prompt_term"])
        candidate = str(context["candidate_term"])
        best = best_by_prompt.get(prompt_term, "")
        avg_nll = 0.1 if candidate == best else 2.0
        return {
            "status": "pass",
            "token_count": len(candidate),
            "candidate_token_ids": [ord(char) for char in candidate],
            "total_nll": avg_nll * len(candidate),
            "avg_nll": avg_nll,
            "first_token_rank": 1 if candidate == best else 2,
            "first_token_logprob": -avg_nll,
        }

    return _score


if __name__ == "__main__":
    unittest.main()
