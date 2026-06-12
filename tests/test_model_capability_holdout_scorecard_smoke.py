from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_holdout_scorecard_smoke import (
    HOLDOUT_SCORECARD_SMOKE_STEM,
    build_holdout_scorecard_smoke,
    create_holdout_scorecard_tiny_checkpoint,
    resolve_exit_code,
    write_holdout_scorecard_smoke_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.run_model_capability_holdout_scorecard_smoke_v1144 import main as cli_main


class ModelCapabilityHoldoutScorecardSmokeTests(unittest.TestCase):
    def test_smoke_runs_real_generations_and_builds_nested_scorecard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = create_holdout_scorecard_tiny_checkpoint(root / "tiny")
            report = build_holdout_scorecard_smoke(
                suite_manifest(),
                required_term_report(),
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                work_dir=root / "run",
                device="cpu",
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_holdout_scorecard_smoke_ready")
        self.assertTrue(report["summary"]["holdout_scorecard_smoke_ready"])
        self.assertEqual(report["summary"]["case_count"], 5)
        self.assertEqual(report["summary"]["passed_case_count"], 5)
        self.assertEqual(report["summary"]["scorecard_overall_status"], "pass")
        self.assertEqual(report["summary"]["model_quality_claim"], "holdout_scorecard_smoke_real_execution")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertTrue(all(row["continuation"] == " fixed loss" for row in report["rows"]))
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_smoke_fails_when_manifest_selects_wrong_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = create_holdout_scorecard_tiny_checkpoint(root / "tiny")
            manifest = suite_manifest()
            manifest["rows"][0]["check_id"] = "required_term_coverage"
            report = build_holdout_scorecard_smoke(
                manifest,
                required_term_report(),
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                work_dir=root / "run",
                device="cpu",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("selected_check_is_holdout_scorecard_smoke", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_smoke_fails_when_required_term_prerequisite_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = create_holdout_scorecard_tiny_checkpoint(root / "tiny")
            source = required_term_report()
            source["summary"]["required_term_real_execution_ready"] = False
            report = build_holdout_scorecard_smoke(
                suite_manifest(),
                source,
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                work_dir=root / "run",
                device="cpu",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("required_term_real_execution_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            required_path = root / "required.json"
            write_json_payload(suite_manifest(), manifest_path)
            write_json_payload(required_term_report(), required_path)
            paths = create_holdout_scorecard_tiny_checkpoint(root / "tiny")
            report = build_holdout_scorecard_smoke(
                suite_manifest(),
                required_term_report(),
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                work_dir=root / "run",
                device="cpu",
            )
            outputs = write_holdout_scorecard_smoke_outputs(report, root / "out")
            cli_main(
                [
                    "--suite-manifest",
                    str(manifest_path),
                    "--required-term-real-execution",
                    str(required_path),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-pass",
                    "--force",
                ]
            )

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue(outputs["json"].endswith(f"{HOLDOUT_SCORECARD_SMOKE_STEM}.json"))
            self.assertTrue((root / "cli-out" / f"{HOLDOUT_SCORECARD_SMOKE_STEM}.json").is_file())
            self.assertTrue((root / "cli-out" / "real-holdout-scorecard-run" / "scorecard" / "benchmark_scorecard.json").is_file())


def suite_manifest() -> dict[str, object]:
    return {
        "status": "pass",
        "suite": {"suite_ready": True, "suite_item_count": 4, "execution_mode": "reuse_existing_evidence_paths"},
        "rows": [
            {
                "suite_id": "capability-regression-04",
                "check_id": "holdout_scorecard_smoke",
                "primary_source": "D:/aiproj/src/minigpt/benchmark_scorecard.py",
                "primary_test": "D:/aiproj/tests/test_benchmark_scorecard.py",
                "artifact_hint": "D:/aiproj/f/1100/解释/receipt-index-review-v1100/receipt_index_review.json",
                "status": "manifested",
                "boundary": "evidence_lookup_not_model_promotion",
            }
        ],
    }


def required_term_report() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "required_term_real_execution_ready": True,
            "model_quality_claim": "single_check_real_execution",
            "promotion_ready": False,
        },
    }


if __name__ == "__main__":
    unittest.main()
