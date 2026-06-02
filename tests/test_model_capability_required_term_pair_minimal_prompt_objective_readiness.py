from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_minimal_prompt_objective_readiness import (
    build_minimal_prompt_objective_readiness,
    locate_minimal_prompt_objective_readiness_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_objective_readiness_artifacts import (
    render_minimal_prompt_objective_readiness_html,
    render_minimal_prompt_objective_readiness_markdown,
    render_minimal_prompt_objective_readiness_text,
    write_minimal_prompt_objective_readiness_outputs,
)


class MinimalPromptObjectiveReadinessTests(unittest.TestCase):
    def test_readiness_passes_when_surface_branch_is_closed(self) -> None:
        report = build_minimal_prompt_objective_readiness(closeout_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "minimal_prompt_surface_objective_ready_for_corpus_contract")
        self.assertTrue(report["summary"]["objective_ready"])
        self.assertEqual(report["summary"]["recommended_corpus_mode"], "minimal_prompt_equals_surface_objective")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_readiness_fails_when_previous_branch_allows_promotion(self) -> None:
        closeout = closeout_fixture()
        closeout["summary"]["promotion_allowed"] = True
        report = build_minimal_prompt_objective_readiness(closeout)

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_blocked", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_readiness_fails_when_next_route_is_not_minimal_prompt(self) -> None:
        closeout = closeout_fixture()
        closeout["summary"]["recommended_next_route"] = "more_contextual_surface_variants"
        report = build_minimal_prompt_objective_readiness(closeout)

        self.assertEqual(report["status"], "fail")
        self.assertIn("minimal_prompt_route_selected", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_minimal_prompt_objective_readiness(closeout_fixture())
            outputs = write_minimal_prompt_objective_readiness_outputs(report, Path(tmp) / "readiness")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("objective_ready=True", render_minimal_prompt_objective_readiness_text(report))
        self.assertIn("Minimal Prompt Objective Readiness", render_minimal_prompt_objective_readiness_markdown(report))
        self.assertIn("MiniGPT minimal prompt objective readiness", render_minimal_prompt_objective_readiness_html(report))

    def test_locate_accepts_file_or_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "example"
            root.mkdir()
            path = root / "model_capability_required_term_pair_surface_branch_closeout.json"

            self.assertEqual(locate_minimal_prompt_objective_readiness_source(path), path)
            self.assertEqual(
                locate_minimal_prompt_objective_readiness_source(path.parent),
                path,
            )


def closeout_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_surface_branch_closed_as_contextual_decode_aid",
        "summary": {
            "contextual_decode_aid_ready": True,
            "promotion_allowed": False,
            "recommended_next_route": "minimal_prompt_surface_objective",
        },
        "interpretation": {
            "model_quality_claim": "contextual_decode_aid_closed_branch",
            "next_action": "run final verification, then treat minimal-prompt capability as a new objective if needed",
        },
    }


if __name__ == "__main__":
    unittest.main()
