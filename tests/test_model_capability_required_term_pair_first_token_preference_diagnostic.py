from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_first_token_preference_diagnostic import (
    build_model_capability_required_term_pair_first_token_preference_diagnostic,
    locate_first_token_preference_refresh_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_first_token_preference_diagnostic_artifacts import (
    render_model_capability_required_term_pair_first_token_preference_diagnostic_html,
    render_model_capability_required_term_pair_first_token_preference_diagnostic_markdown,
    render_model_capability_required_term_pair_first_token_preference_diagnostic_text,
    write_model_capability_required_term_pair_first_token_preference_diagnostic_outputs,
)


class ModelCapabilityRequiredTermPairFirstTokenPreferenceDiagnosticTests(unittest.TestCase):
    def test_diagnostic_confirms_cross_branch_tradeoff(self) -> None:
        report = build_model_capability_required_term_pair_first_token_preference_diagnostic(
            [refresh_report("fixed-only", {"fixed": "fixed=fixed=", "loss": "fixed=los"}), refresh_report("loss-only", {"fixed": "losssss", "loss": "loss=loss"})],
            source_labels=["fixed-route", "loss-route"],
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "first_token_preference_tradeoff_confirmed")
        self.assertTrue(report["summary"]["first_token_conflict_confirmed"])
        self.assertTrue(report["summary"]["mixed_branch_tradeoff_confirmed"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_reports_pair_full_candidate(self) -> None:
        source = refresh_report("pair-full", {"fixed": "fixed=fixed", "loss": "loss=loss"})
        source["summary"]["pair_full_observed"] = True
        report = build_model_capability_required_term_pair_first_token_preference_diagnostic([source, source])

        self.assertEqual(report["decision"], "first_token_preference_has_pair_full_candidate")

    def test_diagnostic_fails_on_missing_checkpoint(self) -> None:
        bad = refresh_report("bad", {"fixed": "fixed", "loss": "loss"})
        bad["summary"]["checkpoint_exists"] = False
        report = build_model_capability_required_term_pair_first_token_preference_diagnostic([bad, bad])

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint is missing", " ".join(report["issues"]))
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_first_token_preference_diagnostic(
                [refresh_report("fixed-only", {"fixed": "fixed", "loss": "fixed"}), refresh_report("loss-only", {"fixed": "loss", "loss": "loss"})]
            )
            outputs = write_model_capability_required_term_pair_first_token_preference_diagnostic_outputs(report, root / "diagnostic")
            text = render_model_capability_required_term_pair_first_token_preference_diagnostic_text(report)
            markdown = render_model_capability_required_term_pair_first_token_preference_diagnostic_markdown(report)
            html = render_model_capability_required_term_pair_first_token_preference_diagnostic_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=first_token_preference_tradeoff_confirmed", text)
            self.assertIn("First-Token Preference Diagnostic", markdown)
            self.assertIn("MiniGPT first-token preference diagnostic", html)

    def test_locator_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_first_token_preference_refresh_report(root),
                root / "model_capability_required_term_pair_coexistence_refresh.json",
            )


def refresh_report(mode: str, continuations: dict[str, str]) -> dict[str, object]:
    rows = []
    for term in ("fixed", "loss"):
        continuation = continuations[term]
        rows.append(
            {
                "profile_id": "default",
                "term": term,
                "prompt": f"{term}=",
                "generated": f"{term}={continuation}",
                "continuation": continuation,
                "continuation_hit": continuation.startswith(term),
                "newline_cleanup_hit": continuation.startswith(term),
            }
        )
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "settings": {"corpus_mode": f"equals_surface_no_pair_id_fixed_retention_{mode}_repair", "seed": 3535},
        "summary": {"training_status": "pass", "checkpoint_exists": True, "pair_full_observed": False},
        "replay_report": {"case_rows": rows},
    }


if __name__ == "__main__":
    unittest.main()
