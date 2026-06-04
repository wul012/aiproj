from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision,
    locate_unassisted_repair_zero_hit_diagnostic,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision_artifacts import (
    render_bounded_objective_unassisted_repair_curriculum_revision_html,
    render_bounded_objective_unassisted_repair_curriculum_revision_markdown,
    render_bounded_objective_unassisted_repair_curriculum_revision_text,
    write_bounded_objective_unassisted_repair_curriculum_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision import main as cli_main


class BoundedObjectiveUnassistedRepairCurriculumRevisionTests(unittest.TestCase):
    def test_builds_revision_from_zero_hit_diagnostic(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision(zero_hit_diagnostic())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_curriculum_revision_ready"])
        self.assertGreaterEqual(report["summary"]["revision_item_count"], 5)
        self.assertEqual(report["summary"]["acceptance_gate_count"], 4)
        self.assertFalse(report["summary"]["decoder_anchor_allowed"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision")
        self.assertEqual(resolve_exit_code(report, require_revision_ready=True), 0)

    def test_revision_fails_without_curriculum_route(self) -> None:
        diagnostic = zero_hit_diagnostic()
        diagnostic["diagnostic"]["proposed_next_artifact"] = "other"
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("diagnostic_routes_curriculum", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagnostic_path = root / "diagnostic" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME
            write_json_payload(zero_hit_diagnostic(), diagnostic_path)
            self.assertEqual(locate_unassisted_repair_zero_hit_diagnostic(diagnostic_path.parent), diagnostic_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision(zero_hit_diagnostic())
            outputs = write_bounded_objective_unassisted_repair_curriculum_revision_outputs(report, root / "out")
            cli_main(
                [
                    "--zero-hit-diagnostic",
                    str(diagnostic_path.parent),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-revision-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_curriculum_revision_ready=True", render_bounded_objective_unassisted_repair_curriculum_revision_text(report))
        self.assertIn("Revision Items", render_bounded_objective_unassisted_repair_curriculum_revision_markdown(report))
        self.assertIn("Revision Items", render_bounded_objective_unassisted_repair_curriculum_revision_html(report))


def zero_hit_diagnostic() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_zero_hit_diagnostic_ready": True,
            "zero_hit_case_count": 3,
            "near_miss_case_count": 1,
            "prompt_in_corpus_count": 3,
        },
        "diagnostic": {
            "ready": True,
            "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision",
        },
        "root_causes": [
            {"cause_id": "objective_replay_zero_required_term_hits", "severity": "high", "evidence": 3},
            {"cause_id": "near_miss_character_substitution", "severity": "high", "evidence": 1},
            {"cause_id": "direct_prompts_present_but_generation_unanchored", "severity": "medium", "evidence": 3},
        ],
        "case_diagnostics": [
            {"case_id": "completion_label_surface", "zero_hit": True, "near_miss_terms": ["loss"]},
        ],
    }


if __name__ == "__main__":
    unittest.main()
