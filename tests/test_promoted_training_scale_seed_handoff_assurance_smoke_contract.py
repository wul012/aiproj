from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import minigpt.promoted_training_scale_seed_handoff_assurance_smoke_contract as contract


class PromotedSeedHandoffAssuranceSmokeContractTests(unittest.TestCase):
    def test_build_checks_accepts_consistent_contract_and_existing_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_outputs = _write_outputs(root, "summary")
            check_outputs = _write_outputs(root, "check")
            summary = _contract_summary()
            summary_check = _contract_summary_check()

            with _patched_dependencies(summary, summary_outputs, summary_check, check_outputs):
                checks, issues = contract.build_receipt_contract_smoke_checks(
                    handoff_dir=root / "handoff",
                    contract_summary_dir=root / "contract-summary",
                    contract_summary_check_dir=root / "contract-summary-check",
                    base_dir=root,
                )

        self.assertEqual(issues, [])
        self.assertEqual(checks["receipt_contract_schema_version"], 5)
        self.assertEqual(checks["receipt_contract_handoff_ci_boundary_plan_check_handoff_count"], 2)
        self.assertEqual(checks["receipt_contract_handoff_ci_boundary_plan_check_selected_count"], 1)
        self.assertTrue(checks["receipt_contract_handoff_ci_reason_selected_within_handoff"])
        for key in contract.CONTRACT_SMOKE_OUTPUT_KEYS:
            self.assertTrue(checks[key])

    def test_build_checks_reports_upstream_drift_and_missing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_outputs = {kind: str(root / "missing" / f"report.{kind}") for kind in _OUTPUT_KINDS}
            summary = _contract_summary()
            summary.update(
                {
                    "status": "fail",
                    "decision": "stop",
                    "receipt_schema_version": 4,
                    "schema_v4_ready": False,
                    "schema_v5_ready": False,
                    "embedded_receipt_check_sidecar_status": "fail",
                    "issue_count": 2,
                    "ci_boundary_plan_check_scopes": [
                        {"scope": "ignored", "handoff_count": 99, "selected_count": 0},
                        {"scope": "handoff", "handoff_count": "bad", "selected_count": "2"},
                    ],
                    "ci_reason_count_scopes": [
                        {"scope": "ignored", "selected_reasons_within_handoff": True},
                        {"scope": "handoff", "selected_reasons_within_handoff": False},
                    ],
                }
            )
            summary_check = _contract_summary_check()
            summary_check.update({"status": "fail", "decision": "stop", "sidecar_status": "fail", "issue_count": 3})

            with _patched_dependencies(summary, missing_outputs, summary_check, missing_outputs):
                checks, issues = contract.build_receipt_contract_smoke_checks(
                    handoff_dir=root / "handoff",
                    contract_summary_dir=root / "contract-summary",
                    contract_summary_check_dir=root / "contract-summary-check",
                    base_dir=root,
                )

        self.assertEqual(checks["receipt_contract_handoff_ci_boundary_plan_check_handoff_count"], 0)
        self.assertEqual(checks["receipt_contract_handoff_ci_boundary_plan_check_selected_count"], 2)
        self.assertIn("receipt contract summary status must pass", issues)
        self.assertIn("receipt contract selected boundary plan-check count must not exceed handoff count", issues)
        self.assertIn("receipt contract selected CI reason counts must not exceed handoff reason counts", issues)
        self.assertIn("receipt contract summary check must have no issues", issues)
        self.assertIn("receipt_contract_summary_json must be a file", issues)

    def test_missing_scope_collections_use_conservative_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outputs = _write_outputs(root, "report")
            summary = _contract_summary()
            summary["ci_boundary_plan_check_scopes"] = "invalid"
            summary["ci_reason_count_scopes"] = None

            with _patched_dependencies(summary, outputs, _contract_summary_check(), outputs):
                checks, issues = contract.build_receipt_contract_smoke_checks(
                    handoff_dir=root / "handoff",
                    contract_summary_dir=root / "contract-summary",
                    contract_summary_check_dir=root / "contract-summary-check",
                    base_dir=root,
                )

        self.assertEqual(checks["receipt_contract_handoff_ci_boundary_plan_check_handoff_count"], 0)
        self.assertEqual(checks["receipt_contract_handoff_ci_boundary_plan_check_selected_count"], 0)
        self.assertIsNone(checks["receipt_contract_handoff_ci_reason_selected_within_handoff"])
        self.assertEqual(
            issues,
            ["receipt contract selected CI reason counts must not exceed handoff reason counts"],
        )


def _contract_summary() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "continue",
        "receipt_schema_version": 5,
        "schema_v4_ready": True,
        "schema_v5_ready": True,
        "ci_boundary_plan_check_scopes": [{"scope": "handoff", "handoff_count": 2, "selected_count": 1}],
        "ci_reason_count_scopes": [{"scope": "handoff", "selected_reasons_within_handoff": True}],
        "embedded_receipt_check_sidecar_status": "pass",
        "issue_count": 0,
    }


def _contract_summary_check() -> dict[str, object]:
    return {"status": "pass", "decision": "continue", "sidecar_status": "pass", "issue_count": 0}


_OUTPUT_KINDS = ("json", "text", "markdown", "html")


def _write_outputs(root: Path, stem: str) -> dict[str, str]:
    outputs = {}
    for kind in _OUTPUT_KINDS:
        path = root / f"{stem}.{kind}"
        path.write_text("evidence", encoding="utf-8")
        outputs[kind] = str(path)
    return outputs


def _patched_dependencies(
    summary: dict[str, object],
    summary_outputs: dict[str, str],
    summary_check: dict[str, object],
    check_outputs: dict[str, str],
) -> object:
    return patch.multiple(
        contract,
        build_promoted_training_scale_seed_handoff_receipt_contract_summary=lambda _: summary,
        write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs=lambda *_: summary_outputs,
        check_promoted_training_scale_seed_handoff_receipt_contract_summary=lambda _: summary_check,
        write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs=lambda *_: check_outputs,
    )


if __name__ == "__main__":
    unittest.main()
