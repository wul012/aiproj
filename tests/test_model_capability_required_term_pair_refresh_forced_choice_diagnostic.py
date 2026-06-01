from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_refresh_forced_choice_diagnostic import (
    build_model_capability_required_term_pair_refresh_forced_choice_diagnostic,
    locate_refresh_forced_choice_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_refresh_forced_choice_diagnostic_artifacts import (
    render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_html,
    render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_markdown,
    render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_text,
    write_model_capability_required_term_pair_refresh_forced_choice_diagnostic_outputs,
)


class RefreshForcedChoiceDiagnosticTests(unittest.TestCase):
    def test_forced_choice_reports_full_internal_match(self) -> None:
        report = build_model_capability_required_term_pair_refresh_forced_choice_diagnostic(
            [refresh_report("full")],
            source_labels=["full"],
            score_func=fake_scorer({("fixed", "fixed"), ("loss", "loss")}),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "refresh_forced_choice_internal_pair_match")
        self.assertEqual(report["summary"]["forced_choice_full_match_source_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_forced_choice_reports_partial_internal_match(self) -> None:
        report = build_model_capability_required_term_pair_refresh_forced_choice_diagnostic(
            [refresh_report("partial")],
            source_labels=["partial"],
            score_func=fake_scorer({("fixed", "fixed")}),
        )

        self.assertEqual(report["decision"], "refresh_forced_choice_partial_internal_match")
        self.assertEqual(report["summary"]["expected_best_prompt_count"], 1)

    def test_forced_choice_fails_without_checkpoint(self) -> None:
        bad = refresh_report("bad")
        bad["summary"]["checkpoint_exists"] = False
        report = build_model_capability_required_term_pair_refresh_forced_choice_diagnostic([bad])

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint is missing", " ".join(report["issues"]))

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_refresh_forced_choice_diagnostic(
                [refresh_report("full")],
                score_func=fake_scorer({("fixed", "fixed"), ("loss", "loss")}),
            )
            outputs = write_model_capability_required_term_pair_refresh_forced_choice_diagnostic_outputs(report, root / "diagnostic")
            text = render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_text(report)
            markdown = render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_markdown(report)
            html = render_model_capability_required_term_pair_refresh_forced_choice_diagnostic_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=refresh_forced_choice_internal_pair_match", text)
            self.assertIn("Refresh Forced-Choice Diagnostic", markdown)
            self.assertIn("MiniGPT refresh forced-choice diagnostic", html)

    def test_locator_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_refresh_forced_choice_report(root),
                root / "model_capability_required_term_pair_coexistence_refresh.json",
            )


def refresh_report(mode: str) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "settings": {"corpus_mode": f"equals_surface_no_pair_id_fixed_retention_{mode}_repair", "seed": 3535},
        "summary": {"training_status": "pass", "checkpoint_exists": True},
        "training": {"checkpoint_path": "checkpoint.pt", "tokenizer_path": "tokenizer.json"},
    }


def fake_scorer(expected_best: set[tuple[str, str]]):
    def score(context: dict[str, object]) -> dict[str, object]:
        prompt_term = str(context["prompt_term"])
        candidate = str(context["candidate_term"])
        best = (prompt_term, candidate) in expected_best
        return {
            "status": "pass",
            "token_count": 1,
            "candidate_token_ids": [1],
            "total_nll": 0.1 if best else 1.0,
            "avg_nll": 0.1 if best else 1.0,
            "first_token_rank": 1 if best else 2,
            "first_token_logprob": -0.1 if best else -1.0,
        }

    return score


if __name__ == "__main__":
    unittest.main()
