from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import build_pair_readiness_corpus_materialization
from minigpt.model_capability_required_term_pair_readiness_fixed_recovery_contract_patch import (
    FIXED_RECOVERY_ROWS,
    build_fixed_recovery_contract_patch,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_recovery_contract_patch_artifacts import (
    render_fixed_recovery_contract_patch_html,
    render_fixed_recovery_contract_patch_markdown,
    render_fixed_recovery_contract_patch_text,
    write_fixed_recovery_contract_patch_outputs,
)


class FixedRecoveryContractPatchTests(unittest.TestCase):
    def test_patch_adds_fixed_recovery_rows_and_preserves_loss_rows(self) -> None:
        report = build_fixed_recovery_contract_patch(repair_plan=plan_fixture(), base_contract_report=base_contract_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_fixed_recovery_contract_patch_ready")
        self.assertEqual(report["summary"]["added_training_row_count"], len(FIXED_RECOVERY_ROWS))
        self.assertGreaterEqual(report["summary"]["loss_row_count"], 6)
        self.assertNotIn("fixed=|loss=", report["contract"]["training_rows"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_patch_can_be_materialized(self) -> None:
        patch = build_fixed_recovery_contract_patch(repair_plan=plan_fixture(), base_contract_report=base_contract_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            materialized = build_pair_readiness_corpus_materialization(patch, out_dir=tmp, repeat=1)

        self.assertEqual(materialized["status"], "pass")
        self.assertEqual(materialized["decision"], "pair_readiness_corpus_materialized")

    def test_patch_fails_for_wrong_base_contract(self) -> None:
        base = base_contract_fixture()
        base["decision"] = "pair_readiness_split_contract_ready"
        report = build_fixed_recovery_contract_patch(repair_plan=plan_fixture(), base_contract_report=base)

        self.assertEqual(report["status"], "fail")
        self.assertIn("base_contract_decision", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_fixed_recovery_contract_patch(repair_plan=plan_fixture(), base_contract_report=base_contract_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_fixed_recovery_contract_patch_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_fixed_recovery_contract_patch_ready", render_fixed_recovery_contract_patch_text(report))
        self.assertIn("Fixed-Recovery Contract Patch", render_fixed_recovery_contract_patch_markdown(report))
        self.assertIn("MiniGPT fixed-recovery contract patch", render_fixed_recovery_contract_patch_html(report))


def plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_recovery_repair_plan_ready",
        "summary": {"plan_ready": True},
    }


def base_contract_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_structured_template_contract_ready",
        "summary": {"contract_ready": True},
        "contract": {
            "training_rows": [
                "task: complete required term | prompt: fixed= | answer: fixed",
                "task: complete required term | prompt: loss= | answer: loss",
                "case=fixed | prompt=fixed= | expected=fixed | answer=fixed",
                "case=loss | prompt=loss= | expected=loss | answer=loss",
                "fixed direct template -> fixed",
                "loss direct template -> loss",
                "fixed route target term is fixed",
                "loss route target term is loss",
                "when prompt begins fixed= complete fixed",
                "when prompt begins loss= complete loss",
                "required term fixed stays on fixed branch",
                "required term loss stays on loss branch",
                "fixed branch answer uses fixed and avoids loss",
                "loss branch answer uses loss and avoids fixed",
            ],
            "evaluation_probes": [
                {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed"},
                {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss"},
                {"id": "fixed-loss-pair", "prompt": "fixed=|loss=", "expected_term": "fixed+loss"},
            ],
            "heldout_pair_probe": "fixed=|loss=",
            "promotion_requirement": "both direct probes must hit",
        },
    }


if __name__ == "__main__":
    unittest.main()
