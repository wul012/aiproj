from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector import (
    build_objective_or_decoding_alternative_selector,
    locate_objective_or_decoding_alternative_selector_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector_artifacts import (
    render_objective_or_decoding_alternative_selector_html,
    render_objective_or_decoding_alternative_selector_markdown,
    render_objective_or_decoding_alternative_selector_text,
    write_objective_or_decoding_alternative_selector_outputs,
)


class ObjectiveOrDecodingAlternativeSelectorTests(unittest.TestCase):
    def test_selects_objective_route_after_closeout(self) -> None:
        report = build_objective_or_decoding_alternative_selector(closeout_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_or_decoding_alternative_selected")
        self.assertTrue(report["summary"]["selector_ready"])
        self.assertEqual(report["summary"]["selected_route"], "objective_level_contrast")
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_objective_level_contrast_plan")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_fails_when_closeout_recommends_different_route(self) -> None:
        closeout = closeout_fixture()
        closeout["closeout"]["recommended_next_route"] = "more_near_exact_rows"
        report = build_objective_or_decoding_alternative_selector(closeout)

        self.assertEqual(report["status"], "fail")
        self.assertIn("recommended_alternative_plan", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_route_scores_keep_decoding_as_diagnostic(self) -> None:
        report = build_objective_or_decoding_alternative_selector(closeout_fixture())
        rows = {row["route"]: row for row in report["route_rows"]}

        self.assertGreater(rows["objective_level_contrast"]["score"], rows["decode_side_constraint_probe"]["score"])
        self.assertIn("diagnostic only", rows["decode_side_constraint_probe"]["risk_control"])
        self.assertFalse(rows["fresh_seed_stability"]["selected"])

    def test_locator_accepts_directory_and_outputs_render(self) -> None:
        report = build_objective_or_decoding_alternative_selector(closeout_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_objective_or_decoding_alternative_selector_source(root).name,
                "model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.json",
            )
            outputs = write_objective_or_decoding_alternative_selector_outputs(report, root / "selector")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("selected_route=objective_level_contrast", render_objective_or_decoding_alternative_selector_text(report))
        self.assertIn("Objective-Or-Decoding Alternative Selector", render_objective_or_decoding_alternative_selector_markdown(report))
        self.assertIn("MiniGPT objective-or-decoding alternative selector", render_objective_or_decoding_alternative_selector_html(report))


def closeout_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_exact_surface_repair_route_closed",
        "summary": {"closeout_ready": True},
        "closeout": {
            "closed_route": "near_exact_surface_bridge_rows",
            "closed_reason": "independent replay deltas stayed at zero",
            "recommended_next_route": "objective_or_decoding_alternative_plan",
            "candidate_routes": [
                {"route": "objective_level_contrast", "why": "change objective", "risk": "may overfit"},
                {"route": "decode_side_constraint_probe", "why": "diagnose decoding", "risk": "can mask weakness"},
                {"route": "fresh_seed_stability", "why": "check seed", "risk": "costs training"},
            ],
            "evidence": {"improved_surface_ids": []},
        },
    }


if __name__ == "__main__":
    unittest.main()
