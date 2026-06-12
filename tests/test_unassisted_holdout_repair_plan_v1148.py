from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.decoder_anchor_holdout_comparison_v1147 import write_decoder_anchor_holdout_comparison_v1147_outputs
from minigpt.unassisted_holdout_repair_plan_v1148 import (
    UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM,
    build_unassisted_holdout_repair_plan_v1148,
    locate_v1147_comparison,
    resolve_exit_code,
    write_unassisted_holdout_repair_plan_v1148_outputs,
)
from scripts.build_unassisted_holdout_repair_plan_v1148 import main as cli_main


class UnassistedHoldoutRepairPlanV1148Tests(unittest.TestCase):
    def test_plan_is_ready_from_v1147_loss_only_gap(self) -> None:
        report = build_unassisted_holdout_repair_plan_v1148(v1147_comparison())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "unassisted_holdout_repair_plan_ready")
        self.assertTrue(report["summary"]["unassisted_holdout_repair_plan_ready"])
        self.assertEqual(report["summary"]["work_item_count"], 6)
        self.assertEqual(report["summary"]["acceptance_gate_count"], 5)
        self.assertEqual(report["summary"]["seed_blueprint_count"], 9)
        self.assertTrue(report["summary"]["new_training_allowed"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "materialize_unassisted_holdout_repair_seed_corpus")
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 0)

    def test_plan_fails_when_v1147_next_step_is_wrong(self) -> None:
        source = v1147_comparison()
        source["summary"]["next_step"] = "unexpected"
        report = build_unassisted_holdout_repair_plan_v1148(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("v1147_next_step_matches_plan", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 1)

    def test_plan_fails_when_full_pair_is_already_recovered(self) -> None:
        source = v1147_comparison()
        source["summary"]["unassisted_full_pair_count"] = 2
        report = build_unassisted_holdout_repair_plan_v1148(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("unassisted_pair_absent", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_outputs = write_decoder_anchor_holdout_comparison_v1147_outputs(v1147_comparison(), root / "comparison")
            self.assertEqual(locate_v1147_comparison(Path(comparison_outputs["json"]).parent), Path(comparison_outputs["json"]))
            report = build_unassisted_holdout_repair_plan_v1148(v1147_comparison())
            outputs = write_unassisted_holdout_repair_plan_v1148_outputs(report, root / "plan")
            cli_main(
                [
                    "--comparison",
                    str(Path(comparison_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-plan"),
                    "--require-plan-ready",
                    "--force",
                ]
            )

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html", "seed_blueprint_json", "seed_blueprint_text"})
            self.assertTrue(outputs["json"].endswith(f"{UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM}.json"))
            self.assertTrue((root / "cli-plan" / f"{UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM}.json").is_file())
            self.assertTrue((root / "cli-plan" / "unassisted_holdout_repair_seed_blueprint.txt").is_file())


def v1147_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "decoder_anchor_holdout_comparison_ready": True,
            "anchor_fragment_hit_count": 5,
            "unassisted_any_term_hit_count": 3,
            "unassisted_fixed_hit_count": 0,
            "unassisted_loss_hit_count": 3,
            "unassisted_full_pair_count": 0,
            "promotion_ready": False,
            "next_step": "build_unassisted_holdout_repair_plan",
        },
        "rows": [
            {"case_id": "answer-colon-pair", "unassisted_prompt": "answer:", "unassisted_hit_terms": []},
            {"case_id": "answer-space-pair", "unassisted_prompt": "answer: ", "unassisted_hit_terms": ["loss"]},
            {"case_id": "completion-colon-pair", "unassisted_prompt": "completion:", "unassisted_hit_terms": []},
            {"case_id": "finish-space-pair", "unassisted_prompt": "finish: ", "unassisted_hit_terms": ["loss"]},
            {"case_id": "compact-signal-answer-pair", "unassisted_prompt": "state compact signal\nanswer:", "unassisted_hit_terms": ["loss"]},
        ],
    }


if __name__ == "__main__":
    unittest.main()
