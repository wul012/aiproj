from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.curriculum_patch_shape_diag import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic,
    locate_curriculum_patch_replay_comparison,
    locate_seed_revision_replay_comparison,
    resolve_exit_code,
)
from minigpt.curriculum_patch_shape_diag_artifacts import (
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_html,
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_markdown,
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_text,
    write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.diagnose_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration import main as cli_main


class CurriculumPatchShapeMigrationDiagnosticTests(unittest.TestCase):
    def test_detects_case_level_shape_migration(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic(
            seed_revision_replay(),
            curriculum_patch_replay(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnosed_profile_sweep_required")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_ready"])
        self.assertEqual(report["summary"]["improved_case_count"], 1)
        self.assertEqual(report["summary"]["regressed_case_count"], 1)
        self.assertEqual(report["summary"]["stable_partial_case_count"], 1)
        self.assertEqual(report["summary"]["any_hit_case_delta"], 0)
        self.assertEqual(report["summary"]["zero_hit_case_delta"], 0)
        self.assertEqual(report["summary"]["loss_missed_after_count"], 3)
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_fails_when_case_sets_do_not_match(self) -> None:
        patch = curriculum_patch_replay()
        patch["replay_rows"] = patch["replay_rows"][:2]
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic(seed_revision_replay(), patch)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_blocked")
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_path = root / "seed" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_REPLAY_COMPARISON_JSON_FILENAME
            patch_path = root / "patch" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(seed_revision_replay(), seed_path)
            write_json_payload(curriculum_patch_replay(), patch_path)
            self.assertEqual(locate_seed_revision_replay_comparison(seed_path.parent), seed_path)
            self.assertEqual(locate_curriculum_patch_replay_comparison(patch_path.parent), patch_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic(
                seed_revision_replay(),
                curriculum_patch_replay(),
                seed_revision_replay_path=seed_path,
                curriculum_patch_replay_path=patch_path,
            )
            outputs = write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_outputs(report, root / "out")
            cli_main(["--seed-revision-replay", str(seed_path.parent), "--curriculum-patch-replay", str(patch_path.parent), "--out-dir", str(root / "cli-out"), "--require-diagnostic-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("improved_case_count=1", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_text(report))
        self.assertIn("Case Migration", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_markdown(report))
        self.assertIn("minimal_surface_regressed_to_zero_hit", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_html(report))


def seed_revision_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready": True,
            "passed_case_count": 0,
            "any_hit_case_count": 2,
            "zero_hit_case_count": 1,
            "objective_contract_recovered": False,
        },
        "replay_rows": [
            row("canonical_direct_completion", ["fixed"], ["loss"], " fixed t"),
            row("minimal_direct_completion", ["fixed"], ["loss"], " fixed t"),
            row("completion_label_surface", [], ["fixed", "loss"], " t t"),
        ],
    }


def curriculum_patch_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_ready": True,
            "passed_case_count": 0,
            "any_hit_case_count": 2,
            "zero_hit_case_count": 1,
            "objective_contract_recovered": False,
        },
        "replay_rows": [
            row("canonical_direct_completion", ["fixed"], ["loss"], " fixed l"),
            row("minimal_direct_completion", [], ["fixed", "loss"], " loswed "),
            row("completion_label_surface", ["fixed"], ["loss"], " fixed l"),
        ],
    }


def row(case_id: str, hit_terms: list[str], missed_terms: list[str], continuation: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "continuation": continuation,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "case_pass": False,
        "any_hit": bool(hit_terms),
    }


if __name__ == "__main__":
    unittest.main()
