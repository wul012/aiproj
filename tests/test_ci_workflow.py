from __future__ import annotations

import contextlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests._bootstrap import ROOT

import minigpt.ci_workflow_hygiene as ci_workflow_hygiene
import minigpt.ci_workflow_hygiene_policy as ci_workflow_hygiene_policy
from minigpt.ci_workflow_hygiene import (
    build_ci_workflow_hygiene_report,
    render_ci_workflow_hygiene_html,
    render_ci_workflow_hygiene_markdown,
    write_ci_workflow_hygiene_outputs,
)
from minigpt.ci_workflow_hygiene_artifacts import (
    render_ci_workflow_hygiene_html as artifact_render_ci_workflow_hygiene_html,
    write_ci_workflow_hygiene_outputs as artifact_write_ci_workflow_hygiene_outputs,
)
from scripts.check_ci_workflow_hygiene import main as cli_main

CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED_SUMMARY_GATES = (
    "tiny_scorecard_plan_digest_gate",
    "baseline_candidate_threshold_boundary_gate_check",
    "baseline_candidate_threshold_boundary_gate_plan_check",
    "archived_path_portability_check",
    "promoted_seed_receipt_contract_failure_smoke",
    "promoted_seed_receipt_contract_failure_smoke_plan_check",
    "release_readiness_drift_contract_smoke",
    "project_docs_readability",
    "static_analysis",
    "type_analysis",
    "file_size_ratchet",
    "aiproj_track_closeout",
    "normalization_guard",
)

COVERAGE_ORDER_SENSITIVE_GATES = tuple(
    gate
    for gate in REQUIRED_SUMMARY_GATES
    if gate
    not in {
        "project_docs_readability",
        "static_analysis",
        "type_analysis",
        "file_size_ratchet",
        "aiproj_track_closeout",
    }
)

CURRENT_WORKFLOW_REQUIRED_CHECK_IDS = (
    "execution:main_branch_push_scope",
    "execution:no_tag_push_trigger",
    "execution:pip_dependency_cache",
    "execution:pip_cache_manifest",
    "execution:same_ref_concurrency_group",
    "execution:cancel_superseded_runs",
    "order:promoted_seed_handoff_assurance_smoke_before_coverage",
    "order:tiny_scorecard_inline_check_smoke_before_coverage",
    "command:tiny_scorecard_summary_check_sidecar",
    "command:ci_tiny_scorecard_plan_digest_check",
    "command:baseline_candidate_threshold_boundary_gate_check",
    "command:baseline_candidate_threshold_boundary_gate_plan_check",
    "command:archived_path_portability_check",
    "command:promoted_seed_receipt_contract_failure_smoke",
    "command:promoted_seed_receipt_contract_failure_smoke_plan_check",
    "command:release_readiness_drift_contract_smoke",
    "command:project_docs_readability_gate",
    "command:static_analysis_gate",
    "command:type_analysis_gate",
    "command:model_capability_honest_measurement_gate",
    "command:artifact_schema_guard",
    "command:file_size_ratchet",
    "command:aiproj_track_closeout",
    "command:normalization_guard",
    "order:ci_tiny_scorecard_plan_check_after_smoke",
    "order:ci_tiny_scorecard_plan_check_before_coverage",
    "order:baseline_candidate_threshold_boundary_gate_check_after_plan_digest",
    "order:baseline_candidate_threshold_boundary_gate_check_before_coverage",
    "order:baseline_candidate_threshold_boundary_gate_plan_check_after_gate_check",
    "order:baseline_candidate_threshold_boundary_gate_plan_check_before_coverage",
    "order:archived_path_portability_check_before_receipt_smoke",
    "order:archived_path_portability_check_before_coverage",
    "order:promoted_seed_receipt_contract_failure_smoke_after_assurance",
    "order:promoted_seed_receipt_contract_failure_smoke_before_coverage",
    "order:promoted_seed_receipt_contract_failure_smoke_plan_check_after_smoke",
    "order:promoted_seed_receipt_contract_failure_smoke_plan_check_before_coverage",
    "order:release_readiness_drift_contract_smoke_before_coverage",
    "order:project_docs_readability_after_source_encoding",
    "order:project_docs_readability_before_ci_hygiene",
    "order:project_docs_readability_before_coverage",
    "order:static_analysis_after_ci_hygiene",
    "order:static_analysis_before_coverage",
    "order:type_analysis_after_static_analysis",
    "order:type_analysis_before_coverage",
    "order:model_capability_honest_measurement_after_type_analysis",
    "order:model_capability_honest_measurement_before_coverage",
    "order:artifact_schema_guard_after_honest_measurement",
    "order:artifact_schema_guard_before_coverage",
    "order:file_size_ratchet_after_artifact_schema_guard",
    "order:file_size_ratchet_before_coverage",
    "order:aiproj_track_closeout_after_file_size_ratchet",
    "order:aiproj_track_closeout_before_coverage",
    "order:normalization_guard_before_coverage",
)

COVERAGE_ORDER_FAILURE_IDS = {
    "order:promoted_seed_handoff_assurance_smoke_before_coverage",
    "order:tiny_scorecard_inline_check_smoke_before_coverage",
    "order:ci_tiny_scorecard_plan_check_before_coverage",
    "order:baseline_candidate_threshold_boundary_gate_check_before_coverage",
    "order:baseline_candidate_threshold_boundary_gate_plan_check_before_coverage",
    "order:archived_path_portability_check_before_coverage",
    "order:promoted_seed_receipt_contract_failure_smoke_before_coverage",
    "order:promoted_seed_receipt_contract_failure_smoke_plan_check_before_coverage",
    "order:release_readiness_drift_contract_smoke_before_coverage",
    "order:normalization_guard_before_coverage",
}


class CIWorkflowTests(unittest.TestCase):
    def test_ci_uses_node24_native_action_versions(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions/checkout@v6", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertNotIn("actions/checkout@v4", workflow)
        self.assertNotIn("actions/setup-python@v5", workflow)
        self.assertNotIn("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24", workflow)

    def test_ci_workflow_hygiene_report_passes_current_workflow(self) -> None:
        report = build_ci_workflow_hygiene_report(CI_WORKFLOW, project_root=ROOT, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["decision"], "continue_with_node24_native_ci")
        self.assertEqual(report["summary"]["node24_native_action_count"], 2)
        self.assertEqual(report["summary"]["forbidden_env_count"], 0)
        self.assertEqual(report["summary"]["missing_step_count"], 0)
        self.assertEqual(report["summary"]["order_violation_count"], 0)
        self.assertEqual(report["summary"]["execution_policy_violation_count"], 0)
        self.assertTrue(report["summary"]["main_branch_push_scope_ready"])
        self.assertTrue(report["summary"]["tag_push_suppressed"])
        self.assertTrue(report["summary"]["pip_dependency_cache_ready"])
        self.assertTrue(report["summary"]["concurrency_cancel_ready"])
        self.assertTrue(report["summary"]["ci_execution_economy_ready"])
        for gate in REQUIRED_SUMMARY_GATES:
            _assert_summary_gate_state(self, report["summary"], gate)
        self.assertEqual(report["summary"]["python_version"], "3.11")
        self.assertIn("actions/checkout", {item["repository"] for item in report["actions"]})
        self.assertTrue(all(item["status"] == "pass" for item in report["checks"]))
        check_ids = _check_ids(report)
        for check_id in CURRENT_WORKFLOW_REQUIRED_CHECK_IDS:
            with self.subTest(check_id=check_id):
                self.assertIn(check_id, check_ids)
        for order_check in (item for item in report["checks"] if item["category"] == "required_order"):
            self.assertIn("before_line=", order_check["actual"])
            self.assertIn("after_line=", order_check["actual"])
            self.assertIn("line", order_check["detail"])

    def test_ci_workflow_hygiene_report_fails_old_runtime_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "ci.yml"
            workflow.write_text(
                "\n".join(
                    [
                        "name: ci",
                        "env:",
                        '  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"',
                        "jobs:",
                        "  test:",
                        "    steps:",
                        "      - uses: actions/checkout@v4",
                        "      - uses: actions/setup-python@v5",
                        "        with:",
                        '          python-version: "3.12"',
                        "      - name: Unit tests",
                        "        run: python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(
                workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z"
            )

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["decision"], "fix_ci_workflow_hygiene")
            self.assertGreaterEqual(report["summary"]["failed_check_count"], 4)
            self.assertEqual(report["summary"]["node24_native_action_count"], 0)
            self.assertEqual(report["summary"]["forbidden_env_count"], 1)
            self.assertEqual(report["summary"]["missing_step_count"], 20)
            self.assertEqual(report["summary"]["required_step_count"], 22)
            for gate in REQUIRED_SUMMARY_GATES:
                with self.subTest(gate=gate):
                    self.assertFalse(report["summary"][f"{gate}_ready"])
            self.assertIn("Upgrade required GitHub actions", " ".join(report["recommendations"]))

    def test_ci_workflow_hygiene_rejects_duplicate_tag_runs_and_missing_cache(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        inefficient = workflow.replace(
            "    branches:\n      - main\n",
            "    branches:\n      - main\n    tags:\n      - 'v*'\n",
        ).replace('          cache: "pip"\n          cache-dependency-path: requirements.txt\n', "")

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "ci.yml"
            path.write_text(inefficient, encoding="utf-8")
            report = build_ci_workflow_hygiene_report(path, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["summary"]["status"], "fail")
        self.assertFalse(report["summary"]["tag_push_suppressed"])
        self.assertFalse(report["summary"]["pip_dependency_cache_ready"])
        self.assertFalse(report["summary"]["ci_execution_economy_ready"])
        self.assertGreaterEqual(report["summary"]["execution_policy_violation_count"], 3)
        self.assertIn("execution:no_tag_push_trigger", _check_ids(report))
        self.assertIn("avoid duplicate CI work", " ".join(report["recommendations"]))

    def test_ci_workflow_hygiene_accepts_semver_and_bare_major_action_tags(self) -> None:
        with TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "ci.yml"
            workflow.write_text(
                "\n".join(
                    [
                        "name: ci",
                        "jobs:",
                        "  test:",
                        "    steps:",
                        "      - uses: actions/checkout@v6.0.0",
                        "      - uses: actions/setup-python@6",
                        "        with:",
                        '          python-version: "3.11"',
                        "      - name: Source encoding and syntax check",
                        "        run: python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-ci",
                        "      - name: Project docs readability check",
                        "        run: python -B scripts/check_project_docs_readability.py --out-dir runs/project-docs-readability-ci --require-pass --force",
                        "      - name: CI workflow hygiene check",
                        "        run: python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-ci",
                        "      - name: Static analysis gate",
                        "        run: python -B scripts/check_static_analysis.py --out-dir runs/static-analysis-ci",
                        "      - name: Scoped type analysis gate",
                        "        run: python -B scripts/check_type_analysis.py --out-dir runs/type-analysis-ci",
                        "      - name: Model capability honest measurement gate",
                        "        run: python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement-ci",
                        "      - name: Artifact schema guard",
                        "        run: python -B scripts/check_artifact_schema_guard.py --out-dir runs/artifact-schema-guard-ci",
                        "      - name: File size ratchet",
                        "        run: python -B scripts/check_file_size_ratchet.py --out-dir runs/file-size-ratchet-ci",
                        "      - name: aiproj production excellence closeout",
                        "        run: python -B scripts/check_aiproj_track_closeout.py --out-dir runs/aiproj-track-closeout-ci",
                        "      - name: Archived path portability check",
                        "        run: python -B scripts/check_archived_path_portability.py --out-dir runs/archived-path-portability-ci",
                        "      - name: Promoted seed handoff assurance smoke",
                        "        run: python -B scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke-ci",
                        "      - name: Promoted seed receipt contract failure smoke",
                        "        run: python -B scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py --out-dir runs/promoted-seed-receipt-contract-failure-smoke-ci --force",
                        "      - name: Promoted seed receipt contract failure smoke plan check",
                        "        run: python -B scripts/check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py runs/promoted-seed-receipt-contract-failure-smoke-ci --out-dir runs/ci-promoted-seed-receipt-contract-failure-smoke-plan-check-ci",
                        "      - name: Tiny scorecard comparison inline check smoke",
                        "        run: python -B scripts/run_ci_tiny_scorecard_comparison_smoke.py --out-dir runs/tiny-scorecard-comparison-smoke-ci --summary-check-out-dir runs/tiny-scorecard-comparison-smoke-check-ci",
                        "      - name: CI tiny scorecard plan digest check",
                        "        run: python -B scripts/check_ci_tiny_scorecard_plan.py runs/tiny-scorecard-comparison-smoke-ci --out-dir runs/ci-tiny-scorecard-plan-check-ci",
                        "      - name: Baseline candidate threshold boundary gate check",
                        "        run: python -B scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py --out-dir runs/baseline-candidate-threshold-boundary-gate-check-ci --force",
                        "      - name: Baseline candidate threshold boundary gate plan check",
                        "        run: python -B scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py runs/baseline-candidate-threshold-boundary-gate-check-ci --out-dir runs/ci-baseline-candidate-threshold-boundary-gate-plan-check-ci",
                        "      - name: Release readiness drift contract smoke",
                        "        run: python -B scripts/check_release_readiness_drift_contract_smoke.py --out-dir runs/release-readiness-drift-contract-smoke-ci",
                        "      - name: Normalization guard",
                        "        run: python -B scripts/check_normalization_guard.py",
                        "      - name: Unit tests",
                        "        run: python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(
                workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z"
            )

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["node24_native_action_count"], 2)
            self.assertEqual(
                {item["version"]: item["node24_native"] for item in report["actions"]},
                {"v6.0.0": True, "6": True},
            )
            self.assertIn("Action version must be upgraded", " ".join(item["detail"] for item in report["checks"]))

    def test_ci_workflow_hygiene_requires_assurance_smoke_before_coverage(self) -> None:
        with TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "ci.yml"
            workflow.write_text(
                "\n".join(
                    [
                        "name: ci",
                        "jobs:",
                        "  test:",
                        "    steps:",
                        "      - uses: actions/checkout@v6",
                        "      - uses: actions/setup-python@v6",
                        "        with:",
                        '          python-version: "3.11"',
                        "      - name: Source encoding and syntax check",
                        "        run: python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-ci",
                        "      - name: Project docs readability check",
                        "        run: python -B scripts/check_project_docs_readability.py --out-dir runs/project-docs-readability-ci --require-pass --force",
                        "      - name: CI workflow hygiene check",
                        "        run: python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-ci",
                        "      - name: Static analysis gate",
                        "        run: python -B scripts/check_static_analysis.py --out-dir runs/static-analysis-ci",
                        "      - name: Scoped type analysis gate",
                        "        run: python -B scripts/check_type_analysis.py --out-dir runs/type-analysis-ci",
                        "      - name: Model capability honest measurement gate",
                        "        run: python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement-ci",
                        "      - name: Artifact schema guard",
                        "        run: python -B scripts/check_artifact_schema_guard.py --out-dir runs/artifact-schema-guard-ci",
                        "      - name: File size ratchet",
                        "        run: python -B scripts/check_file_size_ratchet.py --out-dir runs/file-size-ratchet-ci",
                        "      - name: aiproj production excellence closeout",
                        "        run: python -B scripts/check_aiproj_track_closeout.py --out-dir runs/aiproj-track-closeout-ci",
                        "      - name: Unit tests",
                        "        run: python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98",
                        "      - name: Archived path portability check",
                        "        run: python -B scripts/check_archived_path_portability.py --out-dir runs/archived-path-portability-ci",
                        "      - name: Promoted seed handoff assurance smoke",
                        "        run: python -B scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke-ci",
                        "      - name: Promoted seed receipt contract failure smoke",
                        "        run: python -B scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py --out-dir runs/promoted-seed-receipt-contract-failure-smoke-ci --force",
                        "      - name: Promoted seed receipt contract failure smoke plan check",
                        "        run: python -B scripts/check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py runs/promoted-seed-receipt-contract-failure-smoke-ci --out-dir runs/ci-promoted-seed-receipt-contract-failure-smoke-plan-check-ci",
                        "      - name: Tiny scorecard comparison inline check smoke",
                        "        run: python -B scripts/run_ci_tiny_scorecard_comparison_smoke.py --out-dir runs/tiny-scorecard-comparison-smoke-ci --summary-check-out-dir runs/tiny-scorecard-comparison-smoke-check-ci",
                        "      - name: CI tiny scorecard plan digest check",
                        "        run: python -B scripts/check_ci_tiny_scorecard_plan.py runs/tiny-scorecard-comparison-smoke-ci --out-dir runs/ci-tiny-scorecard-plan-check-ci",
                        "      - name: Baseline candidate threshold boundary gate check",
                        "        run: python -B scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py --out-dir runs/baseline-candidate-threshold-boundary-gate-check-ci --force",
                        "      - name: Baseline candidate threshold boundary gate plan check",
                        "        run: python -B scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py runs/baseline-candidate-threshold-boundary-gate-check-ci --out-dir runs/ci-baseline-candidate-threshold-boundary-gate-plan-check-ci",
                        "      - name: Release readiness drift contract smoke",
                        "        run: python -B scripts/check_release_readiness_drift_contract_smoke.py --out-dir runs/release-readiness-drift-contract-smoke-ci",
                        "      - name: Normalization guard",
                        "        run: python -B scripts/check_normalization_guard.py",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(
                workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z"
            )

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["missing_step_count"], 0)
            self.assertEqual(report["summary"]["order_violation_count"], 10)
            for gate in COVERAGE_ORDER_SENSITIVE_GATES:
                _assert_summary_gate_state(self, report["summary"], gate, order_ready=False, ready=False)
            _assert_summary_gate_state(self, report["summary"], "project_docs_readability")
            self.assertEqual(COVERAGE_ORDER_FAILURE_IDS, _failed_required_order_ids(report))

    def test_ci_workflow_hygiene_requires_plan_check_after_tiny_smoke(self) -> None:
        with TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "ci.yml"
            workflow.write_text(
                "\n".join(
                    [
                        "name: ci",
                        "jobs:",
                        "  test:",
                        "    steps:",
                        "      - uses: actions/checkout@v6",
                        "      - uses: actions/setup-python@v6",
                        "        with:",
                        '          python-version: "3.11"',
                        "      - name: Source encoding and syntax check",
                        "        run: python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-ci",
                        "      - name: Project docs readability check",
                        "        run: python -B scripts/check_project_docs_readability.py --out-dir runs/project-docs-readability-ci --require-pass --force",
                        "      - name: CI workflow hygiene check",
                        "        run: python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-ci",
                        "      - name: Static analysis gate",
                        "        run: python -B scripts/check_static_analysis.py --out-dir runs/static-analysis-ci",
                        "      - name: Scoped type analysis gate",
                        "        run: python -B scripts/check_type_analysis.py --out-dir runs/type-analysis-ci",
                        "      - name: Model capability honest measurement gate",
                        "        run: python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement-ci",
                        "      - name: Artifact schema guard",
                        "        run: python -B scripts/check_artifact_schema_guard.py --out-dir runs/artifact-schema-guard-ci",
                        "      - name: File size ratchet",
                        "        run: python -B scripts/check_file_size_ratchet.py --out-dir runs/file-size-ratchet-ci",
                        "      - name: aiproj production excellence closeout",
                        "        run: python -B scripts/check_aiproj_track_closeout.py --out-dir runs/aiproj-track-closeout-ci",
                        "      - name: Archived path portability check",
                        "        run: python -B scripts/check_archived_path_portability.py --out-dir runs/archived-path-portability-ci",
                        "      - name: Promoted seed handoff assurance smoke",
                        "        run: python -B scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke-ci",
                        "      - name: Promoted seed receipt contract failure smoke",
                        "        run: python -B scripts/run_ci_promoted_seed_receipt_contract_failure_smoke.py --out-dir runs/promoted-seed-receipt-contract-failure-smoke-ci --force",
                        "      - name: Promoted seed receipt contract failure smoke plan check",
                        "        run: python -B scripts/check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py runs/promoted-seed-receipt-contract-failure-smoke-ci --out-dir runs/ci-promoted-seed-receipt-contract-failure-smoke-plan-check-ci",
                        "      - name: CI tiny scorecard plan digest check",
                        "        run: python -B scripts/check_ci_tiny_scorecard_plan.py runs/tiny-scorecard-comparison-smoke-ci --out-dir runs/ci-tiny-scorecard-plan-check-ci",
                        "      - name: Baseline candidate threshold boundary gate check",
                        "        run: python -B scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py --out-dir runs/baseline-candidate-threshold-boundary-gate-check-ci --force",
                        "      - name: Baseline candidate threshold boundary gate plan check",
                        "        run: python -B scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py runs/baseline-candidate-threshold-boundary-gate-check-ci --out-dir runs/ci-baseline-candidate-threshold-boundary-gate-plan-check-ci",
                        "      - name: Tiny scorecard comparison inline check smoke",
                        "        run: python -B scripts/run_ci_tiny_scorecard_comparison_smoke.py --out-dir runs/tiny-scorecard-comparison-smoke-ci --summary-check-out-dir runs/tiny-scorecard-comparison-smoke-check-ci",
                        "      - name: Release readiness drift contract smoke",
                        "        run: python -B scripts/check_release_readiness_drift_contract_smoke.py --out-dir runs/release-readiness-drift-contract-smoke-ci",
                        "      - name: Normalization guard",
                        "        run: python -B scripts/check_normalization_guard.py",
                        "      - name: Unit tests",
                        "        run: python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(
                workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z"
            )

            failed_order_ids = _failed_required_order_ids(report)
            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["missing_step_count"], 0)
            _assert_summary_gate_state(
                self,
                report["summary"],
                "tiny_scorecard_plan_digest_gate",
                order_ready=False,
                ready=False,
            )
            for gate in (
                "baseline_candidate_threshold_boundary_gate_check",
                "baseline_candidate_threshold_boundary_gate_plan_check",
                "archived_path_portability_check",
                "promoted_seed_receipt_contract_failure_smoke_plan_check",
                "project_docs_readability",
                "normalization_guard",
            ):
                _assert_summary_gate_state(self, report["summary"], gate)
            self.assertIn("order:ci_tiny_scorecard_plan_check_after_smoke", failed_order_ids)

    def test_ci_workflow_hygiene_outputs_json_csv_markdown_and_html(self) -> None:
        report = build_ci_workflow_hygiene_report(
            CI_WORKFLOW, project_root=ROOT, title="CI <workflow>", generated_at="2026-01-01T00:00:00Z"
        )

        with TemporaryDirectory() as tmp:
            outputs = write_ci_workflow_hygiene_outputs(report, Path(tmp) / "out")

            for path in outputs.values():
                self.assertTrue(Path(path).exists())
            self.assertIn("actions/setup-python", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("CI &lt;workflow&gt;", render_ci_workflow_hygiene_html(report))
            self.assertIn("continue_with_node24_native_ci", render_ci_workflow_hygiene_markdown(report))
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            for gate in REQUIRED_SUMMARY_GATES:
                with self.subTest(gate=gate):
                    self.assertIn(f"{gate}_ready", markdown)
            self.assertIn("order_violation_count", markdown)

    def test_ci_workflow_hygiene_cli_accepts_argv_and_returns_status(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "out"
            bad_workflow = root / "ci.yml"
            bad_workflow.write_text(
                "\n".join(
                    [
                        "name: ci",
                        "jobs:",
                        "  test:",
                        "    steps:",
                        "      - uses: actions/checkout@v4",
                        "      - uses: actions/setup-python@v5",
                    ]
                ),
                encoding="utf-8",
            )

            with contextlib.redirect_stdout(io.StringIO()):
                fail_code = cli_main(["--workflow", str(bad_workflow), "--out-dir", str(out_dir)])
                no_fail_code = cli_main(
                    ["--workflow", str(bad_workflow), "--out-dir", str(root / "no-fail"), "--no-fail"]
                )

            self.assertEqual(fail_code, 1)
            self.assertEqual(no_fail_code, 0)
            self.assertTrue((out_dir / "ci_workflow_hygiene.json").is_file())

    def test_ci_workflow_module_reexports_artifact_writers(self) -> None:
        self.assertIs(render_ci_workflow_hygiene_html, artifact_render_ci_workflow_hygiene_html)
        self.assertIs(write_ci_workflow_hygiene_outputs, artifact_write_ci_workflow_hygiene_outputs)
        self.assertIs(ci_workflow_hygiene.REQUIRED_ACTIONS, ci_workflow_hygiene_policy.REQUIRED_ACTIONS)
        self.assertIs(
            ci_workflow_hygiene.REQUIRED_COMMAND_FRAGMENTS, ci_workflow_hygiene_policy.REQUIRED_COMMAND_FRAGMENTS
        )
        self.assertIs(ci_workflow_hygiene.REQUIRED_COMMAND_ORDER, ci_workflow_hygiene_policy.REQUIRED_COMMAND_ORDER)
        self.assertIs(
            ci_workflow_hygiene.REQUIRED_EXECUTION_POLICY_FRAGMENTS,
            ci_workflow_hygiene_policy.REQUIRED_EXECUTION_POLICY_FRAGMENTS,
        )


def _assert_summary_gate_state(
    testcase: unittest.TestCase,
    summary: dict[str, object],
    gate: str,
    *,
    present: bool = True,
    order_ready: bool = True,
    ready: bool = True,
) -> None:
    with testcase.subTest(gate=gate):
        testcase.assertEqual(summary[f"{gate}_present"], present)
        testcase.assertEqual(summary[f"{gate}_order_ready"], order_ready)
        testcase.assertEqual(summary[f"{gate}_ready"], ready)


def _check_ids(report: dict[str, object]) -> set[str]:
    return {str(item["id"]) for item in report["checks"]}


def _failed_required_order_ids(report: dict[str, object]) -> set[str]:
    return {
        str(item["id"])
        for item in report["checks"]
        if item["category"] == "required_order" and item["status"] == "fail"
    }


if __name__ == "__main__":
    unittest.main()
