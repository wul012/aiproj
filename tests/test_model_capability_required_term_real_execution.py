from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_real_execution import (
    REQUIRED_TERM_REAL_EXECUTION_STEM,
    build_required_term_real_execution,
    create_required_term_tiny_checkpoint,
    resolve_exit_code,
    write_required_term_real_execution_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.run_model_capability_required_term_real_execution import main as cli_main


class ModelCapabilityRequiredTermRealExecutionTests(unittest.TestCase):
    def test_real_execution_runs_minigpt_generator_and_hits_required_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = create_required_term_tiny_checkpoint(root / "tiny")
            report = build_required_term_real_execution(
                suite_manifest(),
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                device="cpu",
                suite_manifest_path=root / "manifest.json",
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_required_term_real_execution_ready")
        self.assertTrue(report["summary"]["required_term_real_execution_ready"])
        self.assertEqual(report["summary"]["model_quality_claim"], "single_check_real_execution")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["rows"][0]["continuation"], " fixed loss")
        self.assertEqual(report["rows"][0]["hit_terms"], ["fixed", "loss"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_real_execution_fails_when_manifest_selects_wrong_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = create_required_term_tiny_checkpoint(root / "tiny")
            manifest = suite_manifest()
            manifest["rows"][0]["check_id"] = "holdout_scorecard_smoke"
            report = build_required_term_real_execution(
                manifest,
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                device="cpu",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("selected_check_is_required_term_coverage", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_real_execution_fails_when_checkpoint_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = create_required_term_tiny_checkpoint(root / "tiny")
            missing_checkpoint = root / "missing.pt"
            report = build_required_term_real_execution(
                suite_manifest(),
                checkpoint_path=missing_checkpoint,
                tokenizer_path=paths["tokenizer"],
                device="cpu",
            )

        issue_ids = [issue["id"] for issue in report["issues"]]
        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", issue_ids)
        self.assertIn("generation_executed", issue_ids)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            write_json_payload(suite_manifest(), manifest_path)
            paths = create_required_term_tiny_checkpoint(root / "tiny")
            report = build_required_term_real_execution(
                suite_manifest(),
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                device="cpu",
            )
            outputs = write_required_term_real_execution_outputs(report, root / "out")
            cli_main(
                [
                    "--suite-manifest",
                    str(manifest_path),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-pass",
                    "--force",
                ]
            )

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue(outputs["json"].endswith(f"{REQUIRED_TERM_REAL_EXECUTION_STEM}.json"))
            self.assertTrue((root / "cli-out" / f"{REQUIRED_TERM_REAL_EXECUTION_STEM}.json").is_file())


def suite_manifest() -> dict[str, object]:
    return {
        "status": "pass",
        "suite": {
            "suite_ready": True,
            "suite_item_count": 4,
            "execution_mode": "reuse_existing_evidence_paths",
            "promotion_ready": False,
            "model_quality_claim": "manifest_only",
        },
        "rows": [
            {
                "suite_id": "capability-regression-01",
                "check_id": "required_term_coverage",
                "primary_source": "D:/aiproj/src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.py",
                "primary_test": "D:/aiproj/tests/test_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run.py",
                "artifact_hint": "",
                "status": "manifested",
                "boundary": "evidence_lookup_not_model_promotion",
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
