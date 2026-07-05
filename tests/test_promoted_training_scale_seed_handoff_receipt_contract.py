from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (  # noqa: E402
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_html,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_text,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_context import (  # noqa: E402
    contract_issues,
)
from tests.test_promoted_training_scale_seed_handoff_receipt_suite_design import (  # noqa: E402
    SuiteDesignHandoffSidecars,
    write_suite_design_handoff_with_sidecars,
)
from tests.test_promoted_training_scale_seed_handoff import (  # noqa: E402
    HANDOFF_CI_REASON_COUNTS,
    SELECTED_CI_REASON_COUNTS,
    write_seed_tree,
)


class PromotedTrainingScaleSeedHandoffReceiptContractTests(unittest.TestCase):
    def test_contract_summary_flattens_current_schema_suite_design_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_suite_design_handoff_with_sidecars(Path(tmp))

            summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(paths["handoff"])
            text = render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary)
            markdown = render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(summary)
            html = render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(summary)

            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["receipt_schema_version"], 5)
            self.assertTrue(summary["schema_v3_ready"])
            self.assertTrue(summary["schema_v4_ready"])
            self.assertTrue(summary["schema_v5_ready"])
            self.assertEqual(summary["embedded_receipt_check_sidecar_status"], "pass")
            self.assertEqual(
                {
                    item["scope"]: (item["count"], item["names"], item["count_matches_names"])
                    for item in summary["suite_design_scopes"]
                },
                {
                    "selected": (0, [], True),
                    "handoff": (2, ["beta-suite", "standard"], True),
                    "comparison_ready": (0, [], True),
                },
            )
            self.assertIn("receipt_contract_handoff_suite_design_count=2", text)
            self.assertIn("receipt_contract_schema_v4_ready=True", text)
            self.assertIn("receipt_contract_schema_v5_ready=True", text)
            self.assertEqual(summary["failed_contract_check_count"], 0)
            self.assertEqual(summary["contract_check_status_counts"], {"pass": 14, "fail": 0})
            type_summary = {item["check_type"]: item for item in summary["contract_check_type_summary"]}
            self.assertEqual(type_summary["schema_readiness"]["count"], 3)
            self.assertEqual(type_summary["schema_readiness"]["failed_count"], 0)
            self.assertEqual(type_summary["schema_readiness"]["required_count"], 3)
            self.assertIn("receipt.schema_v4_ready", type_summary["schema_readiness"]["targets"])
            self.assertIn("receipt.schema_v5_ready", type_summary["schema_readiness"]["targets"])
            self.assertEqual(type_summary["status_equals"]["count"], 2)
            self.assertEqual(type_summary["count_consistency"]["count"], 3)
            self.assertEqual(type_summary["selected_within_handoff"]["count"], 3)
            self.assertEqual(type_summary["reason_counts_within_handoff"]["count"], 3)
            self.assertIn("receipt_contract_failed_check_count=0", text)
            self.assertIn("receipt_contract_check_type_summary=", text)
            self.assertIn("schema_v4_ready", {item["id"] for item in summary["contract_checks"]})
            self.assertIn("schema_v5_ready", {item["id"] for item in summary["contract_checks"]})
            schema_check = next(item for item in summary["contract_checks"] if item["id"] == "schema_v4_ready")
            self.assertEqual(schema_check["check_type"], "schema_readiness")
            self.assertEqual(schema_check["target"], "receipt.schema_v4_ready")
            self.assertEqual(schema_check["status_domain"], ["pass", "fail"])
            self.assertTrue(schema_check["required"])
            self.assertEqual(schema_check["expected_kind"], "bool")
            self.assertEqual(schema_check["actual_kind"], "bool")
            self.assertIn("| handoff | 2 | beta-suite, standard | True |", markdown)
            self.assertIn(
                "| schema_v4_ready | schema_readiness | receipt.schema_v4_ready | receipt | pass | True | True |",
                markdown,
            )
            self.assertIn(
                "| schema_v5_ready | schema_readiness | receipt.schema_v5_ready | receipt | pass | True | True |",
                markdown,
            )
            self.assertIn("| schema_readiness | pass | 3 | 3 | 0 | 3 |", markdown)
            self.assertIn("| reason_counts_within_handoff | pass | 3 | 3 | 0 | 3 |", markdown)
            self.assertIn("<td>handoff</td>", html)
            self.assertIn("<td>schema_readiness</td>", html)
            self.assertIn("CI Reason-Count Scopes", html)
            self.assertIn("Contract Check Type Summary", html)
            self.assertIn("<td>schema_v4_ready</td>", html)
            self.assertIn("<td>schema_v5_ready</td>", html)

    def test_contract_summary_flattens_schema_v4_boundary_plan_check_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_boundary_plan_handoff_with_sidecars(Path(tmp))

            summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(paths["handoff"])
            text = render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary)
            markdown = render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(summary)
            html = render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(summary)

            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["receipt_schema_version"], 5)
            self.assertTrue(summary["schema_v4_ready"])
            self.assertTrue(summary["schema_v5_ready"])
            self.assertEqual(
                {
                    item["scope"]: (
                        item["handoff_count"],
                        item["selected_count"],
                        item["selected_within_handoff"],
                    )
                    for item in summary["ci_boundary_plan_check_scopes"]
                },
                {
                    "selected": (0, 0, True),
                    "handoff": (1, 0, True),
                    "comparison_ready": (0, 0, True),
                },
            )
            self.assertIn("receipt_contract_handoff_ci_boundary_plan_check_handoff_count=1", text)
            self.assertIn("ci_boundary_plan_check_handoff_selected_within_handoff", text)
            self.assertIn("| handoff | 1 | 0 | True |", markdown)
            self.assertIn("ci_boundary_plan_check.handoff.selected_within_handoff", markdown)
            self.assertIn("CI Boundary Plan-Check Scopes", html)

    def test_contract_summary_checks_ci_reason_counts_within_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_reason_count_handoff_with_sidecars(Path(tmp))

            summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(paths["handoff"])
            text = render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary)
            markdown = render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(summary)
            html = render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(summary)

            self.assertEqual(summary["status"], "pass")
            by_scope = {item["scope"]: item for item in summary["ci_reason_count_scopes"]}
            self.assertEqual(by_scope["handoff"]["handoff_reason_counts"], HANDOFF_CI_REASON_COUNTS)
            self.assertEqual(by_scope["handoff"]["selected_reason_counts"], SELECTED_CI_REASON_COUNTS)
            self.assertTrue(by_scope["handoff"]["selected_reasons_within_handoff"])
            self.assertEqual(by_scope["handoff"]["missing_reasons"], [])
            self.assertIn(
                'receipt_contract_handoff_ci_reason_selected_counts={"archived_path_portability_check_not_ready": 1}',
                text,
            )
            self.assertIn(
                "| handoff | {\"archived_path_portability_check_not_ready\": 1, "
                "\"workflow-order-regressed\": 1} | {\"archived_path_portability_check_not_ready\": 1} | "
                "True | none |",
                markdown,
            )
            self.assertIn("ci_reason_counts.handoff.selected_reasons_within_handoff", markdown)
            self.assertIn("CI Reason-Count Scopes", html)

    def test_contract_summary_rejects_selected_reason_missing_from_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_reason_count_handoff_with_sidecars(
                Path(tmp),
                handoff_ci_reason_counts={"workflow-order-regressed": 2},
                selected_ci_reason_counts={"missing-ci-step": 1},
            )

            summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(paths["handoff"])

            self.assertEqual(summary["status"], "fail")
            by_scope = {item["scope"]: item for item in summary["ci_reason_count_scopes"]}
            self.assertFalse(by_scope["handoff"]["selected_reasons_within_handoff"])
            self.assertEqual(by_scope["handoff"]["missing_reasons"], ["missing-ci-step"])
            failed = [
                item for item in summary["contract_checks"]
                if item["id"] == "ci_reason_counts_handoff_selected_within_handoff"
            ][0]
            self.assertEqual(failed["status"], "fail")
            self.assertTrue(
                any("handoff CI regression selected reasons exceed handoff reasons" in issue for issue in summary["issues"])
            )

    def test_contract_issues_keep_legacy_schema_v4_reason_counts_compatible_when_consistent(self) -> None:
        assurance = {
            "status": "pass",
            "decision": "continue",
            "embedded_receipt_check_receipt_schema_version": 4,
            "embedded_receipt_check_sidecar_status": "pass",
        }
        reason_scopes = [
            {
                "scope": "handoff",
                "selected_reasons_within_handoff": True,
            }
        ]

        issues = contract_issues(assurance, [], [], reason_scopes)

        self.assertFalse(
            any("receipt schema version must be >= 5 for CI reason-count contract" in issue for issue in issues)
        )

    def test_contract_issues_require_schema_v5_when_legacy_reason_count_contract_fails(self) -> None:
        assurance = {
            "status": "pass",
            "decision": "continue",
            "embedded_receipt_check_receipt_schema_version": 4,
            "embedded_receipt_check_sidecar_status": "pass",
        }
        reason_scopes = [
            {
                "scope": "handoff",
                "missing_reasons": ["missing-ci-step"],
                "selected_reasons_within_handoff": False,
            }
        ]

        issues = contract_issues(assurance, [], [], reason_scopes)

        self.assertTrue(
            any("receipt schema version must be >= 5 for CI reason-count contract" in issue for issue in issues)
        )
        self.assertTrue(
            any("handoff CI regression selected reasons exceed handoff reasons" in issue for issue in issues)
        )

    def test_contract_summary_rejects_tampered_suite_design_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_suite_design_handoff_with_sidecars(Path(tmp))
            check_path = paths["receipt_check"] / "promoted_training_scale_seed_handoff_automation_receipt_check.json"
            payload = json.loads(check_path.read_text(encoding="utf-8"))
            payload["handoff_batch_maturity_suite_design_regression_names"] = ["beta-suite"]
            check_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(paths["handoff"])

            self.assertEqual(summary["status"], "fail")
            self.assertEqual(summary["assurance_status"], "fail")
            self.assertGreaterEqual(summary["failed_contract_check_count"], 1)
            self.assertTrue(any(item["status"] == "fail" for item in summary["contract_checks"]))
            type_summary = {item["check_type"]: item for item in summary["contract_check_type_summary"]}
            self.assertEqual(type_summary["status_equals"]["status"], "fail")
            self.assertGreaterEqual(type_summary["status_equals"]["failed_count"], 1)
            failed = next(item for item in summary["contract_checks"] if item["status"] == "fail")
            self.assertIn(failed["check_type"], {"status_equals", "count_consistency"})
            self.assertEqual(failed["status_domain"], ["pass", "fail"])
            self.assertTrue(any("handoff assurance must pass" in issue for issue in summary["issues"]))
            self.assertTrue(
                any(
                    "receipt_check_outputs.json.handoff_batch_maturity_suite_design_regression_names"
                    in issue
                    for issue in summary["issues"]
                )
            )

    def test_cli_writes_contract_summary_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            out_dir = root / "contract-summary"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_receipt_contract.py"),
                    str(paths["handoff"]),
                    "--out-dir",
                    str(out_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            summary = json.loads(
                (out_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(summary["status"], "pass")
            self.assertIn("receipt_contract_status=pass", completed.stdout)
            self.assertIn("receipt_contract_html=", completed.stdout)
            self.assertTrue((out_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.txt").is_file())
            self.assertTrue((out_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.md").is_file())
            self.assertTrue((out_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.html").is_file())


def write_boundary_plan_handoff_with_sidecars(root: Path) -> SuiteDesignHandoffSidecars:
    seed = write_seed_tree(
        root,
        suite_name="standard-zh",
        include_handoff_suite_guard=True,
        include_handoff_clean_batch_review=True,
        handoff_ci_regression_count=2,
    )
    handoff_dir = root / "handoff"
    receipt_check_dir = root / "receipt-check"
    embedded_check_dir = root / "embedded-check"
    assurance_dir = root / "assurance"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
            str(seed),
            "--out-dir",
            str(handoff_dir),
            "--require-clean-batch-review",
            "--receipt-check-out-dir",
            str(receipt_check_dir),
            "--embedded-receipt-check-out-dir",
            str(embedded_check_dir),
            "--assurance-out-dir",
            str(assurance_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        "handoff": handoff_dir,
        "receipt_check": receipt_check_dir,
        "embedded_check": embedded_check_dir,
        "assurance": assurance_dir,
        "stdout": completed.stdout,
    }


def write_reason_count_handoff_with_sidecars(
    root: Path,
    *,
    handoff_ci_reason_counts: dict[str, int] | None = None,
    selected_ci_reason_counts: dict[str, int] | None = None,
) -> SuiteDesignHandoffSidecars:
    seed = write_seed_tree(
        root,
        suite_name="standard-zh",
        include_handoff_suite_guard=True,
        include_handoff_clean_batch_review=True,
        handoff_ci_regression_count=2,
        selected_handoff_ci_regression_count=1,
        handoff_ci_reason_counts=handoff_ci_reason_counts or HANDOFF_CI_REASON_COUNTS,
        selected_ci_reason_counts=selected_ci_reason_counts or SELECTED_CI_REASON_COUNTS,
    )
    handoff_dir = root / "handoff"
    receipt_check_dir = root / "receipt-check"
    embedded_check_dir = root / "embedded-check"
    assurance_dir = root / "assurance"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
            str(seed),
            "--out-dir",
            str(handoff_dir),
            "--receipt-check-out-dir",
            str(receipt_check_dir),
            "--embedded-receipt-check-out-dir",
            str(embedded_check_dir),
            "--assurance-out-dir",
            str(assurance_dir),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        "handoff": handoff_dir,
        "receipt_check": receipt_check_dir,
        "embedded_check": embedded_check_dir,
        "assurance": assurance_dir,
        "stdout": completed.stdout,
    }


if __name__ == "__main__":
    unittest.main()
