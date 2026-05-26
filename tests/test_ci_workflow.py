from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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

CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


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
        self.assertTrue(report["summary"]["tiny_scorecard_plan_digest_gate_present"])
        self.assertTrue(report["summary"]["tiny_scorecard_plan_digest_gate_order_ready"])
        self.assertTrue(report["summary"]["tiny_scorecard_plan_digest_gate_ready"])
        self.assertTrue(report["summary"]["baseline_candidate_threshold_boundary_gate_check_present"])
        self.assertTrue(report["summary"]["baseline_candidate_threshold_boundary_gate_check_order_ready"])
        self.assertTrue(report["summary"]["baseline_candidate_threshold_boundary_gate_check_ready"])
        self.assertTrue(report["summary"]["release_readiness_drift_contract_smoke_present"])
        self.assertTrue(report["summary"]["release_readiness_drift_contract_smoke_order_ready"])
        self.assertTrue(report["summary"]["release_readiness_drift_contract_smoke_ready"])
        self.assertEqual(report["summary"]["python_version"], "3.11")
        self.assertIn("actions/checkout", {item["repository"] for item in report["actions"]})
        self.assertTrue(all(item["status"] == "pass" for item in report["checks"]))
        self.assertIn(
            "order:promoted_seed_handoff_assurance_smoke_before_coverage",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "order:tiny_scorecard_inline_check_smoke_before_coverage",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "command:tiny_scorecard_summary_check_sidecar",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "command:ci_tiny_scorecard_plan_digest_check",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "command:baseline_candidate_threshold_boundary_gate_check",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "command:release_readiness_drift_contract_smoke",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "order:ci_tiny_scorecard_plan_check_after_smoke",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "order:ci_tiny_scorecard_plan_check_before_coverage",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "order:baseline_candidate_threshold_boundary_gate_check_after_plan_digest",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "order:baseline_candidate_threshold_boundary_gate_check_before_coverage",
            {item["id"] for item in report["checks"]},
        )
        self.assertIn(
            "order:release_readiness_drift_contract_smoke_before_coverage",
            {item["id"] for item in report["checks"]},
        )
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
                        "        run: python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 80",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z")

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["decision"], "fix_ci_workflow_hygiene")
            self.assertGreaterEqual(report["summary"]["failed_check_count"], 4)
            self.assertEqual(report["summary"]["node24_native_action_count"], 0)
            self.assertEqual(report["summary"]["forbidden_env_count"], 1)
            self.assertEqual(report["summary"]["missing_step_count"], 8)
            self.assertEqual(report["summary"]["required_step_count"], 10)
            self.assertFalse(report["summary"]["tiny_scorecard_plan_digest_gate_ready"])
            self.assertFalse(report["summary"]["baseline_candidate_threshold_boundary_gate_check_ready"])
            self.assertFalse(report["summary"]["release_readiness_drift_contract_smoke_ready"])
            self.assertIn("Upgrade required GitHub actions", " ".join(report["recommendations"]))

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
                        "      - name: CI workflow hygiene check",
                        "        run: python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-ci",
                        "      - name: Promoted seed handoff assurance smoke",
                        "        run: python -B scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke-ci",
                        "      - name: Tiny scorecard comparison inline check smoke",
                        "        run: python -B scripts/run_ci_tiny_scorecard_comparison_smoke.py --out-dir runs/tiny-scorecard-comparison-smoke-ci --summary-check-out-dir runs/tiny-scorecard-comparison-smoke-check-ci",
                        "      - name: CI tiny scorecard plan digest check",
                        "        run: python -B scripts/check_ci_tiny_scorecard_plan.py runs/tiny-scorecard-comparison-smoke-ci --out-dir runs/ci-tiny-scorecard-plan-check-ci",
                        "      - name: Baseline candidate threshold boundary gate check",
                        "        run: python -B scripts/check_baseline_candidate_threshold_boundary_gate.py --smoke-summary d/438/解释/baseline-candidate-threshold-boundary-smoke/tiny-scorecard-comparison-smoke/tiny_scorecard_comparison_smoke_summary.json --out-dir runs/baseline-candidate-threshold-boundary-gate-check-ci --thresholds 0:1:0.5 --require-diagnosis-pass --expected-exit-code 2 --expected-diagnosis-decision candidate_not_accepted --require-pass --force",
                        "      - name: Release readiness drift contract smoke",
                        "        run: python -B scripts/check_release_readiness_drift_contract_smoke.py --out-dir runs/release-readiness-drift-contract-smoke-ci",
                        "      - name: Unit tests",
                        "        run: python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 80",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z")

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
                        "      - name: CI workflow hygiene check",
                        "        run: python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-ci",
                        "      - name: Unit tests",
                        "        run: python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 80",
                        "      - name: Promoted seed handoff assurance smoke",
                        "        run: python -B scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke-ci",
                        "      - name: Tiny scorecard comparison inline check smoke",
                        "        run: python -B scripts/run_ci_tiny_scorecard_comparison_smoke.py --out-dir runs/tiny-scorecard-comparison-smoke-ci --summary-check-out-dir runs/tiny-scorecard-comparison-smoke-check-ci",
                        "      - name: CI tiny scorecard plan digest check",
                        "        run: python -B scripts/check_ci_tiny_scorecard_plan.py runs/tiny-scorecard-comparison-smoke-ci --out-dir runs/ci-tiny-scorecard-plan-check-ci",
                        "      - name: Baseline candidate threshold boundary gate check",
                        "        run: python -B scripts/check_baseline_candidate_threshold_boundary_gate.py --smoke-summary d/438/解释/baseline-candidate-threshold-boundary-smoke/tiny-scorecard-comparison-smoke/tiny_scorecard_comparison_smoke_summary.json --out-dir runs/baseline-candidate-threshold-boundary-gate-check-ci --thresholds 0:1:0.5 --require-diagnosis-pass --expected-exit-code 2 --expected-diagnosis-decision candidate_not_accepted --require-pass --force",
                        "      - name: Release readiness drift contract smoke",
                        "        run: python -B scripts/check_release_readiness_drift_contract_smoke.py --out-dir runs/release-readiness-drift-contract-smoke-ci",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z")

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["missing_step_count"], 0)
            self.assertEqual(report["summary"]["order_violation_count"], 5)
            self.assertTrue(report["summary"]["tiny_scorecard_plan_digest_gate_present"])
            self.assertFalse(report["summary"]["tiny_scorecard_plan_digest_gate_order_ready"])
            self.assertFalse(report["summary"]["tiny_scorecard_plan_digest_gate_ready"])
            self.assertTrue(report["summary"]["baseline_candidate_threshold_boundary_gate_check_present"])
            self.assertFalse(report["summary"]["baseline_candidate_threshold_boundary_gate_check_order_ready"])
            self.assertFalse(report["summary"]["baseline_candidate_threshold_boundary_gate_check_ready"])
            self.assertTrue(report["summary"]["release_readiness_drift_contract_smoke_present"])
            self.assertFalse(report["summary"]["release_readiness_drift_contract_smoke_order_ready"])
            self.assertFalse(report["summary"]["release_readiness_drift_contract_smoke_ready"])
            failed_order_ids = {item["id"] for item in report["checks"] if item["category"] == "required_order" and item["status"] == "fail"}
            self.assertIn("order:promoted_seed_handoff_assurance_smoke_before_coverage", failed_order_ids)
            self.assertIn("order:tiny_scorecard_inline_check_smoke_before_coverage", failed_order_ids)
            self.assertIn("order:ci_tiny_scorecard_plan_check_before_coverage", failed_order_ids)
            self.assertIn("order:baseline_candidate_threshold_boundary_gate_check_before_coverage", failed_order_ids)
            self.assertIn("order:release_readiness_drift_contract_smoke_before_coverage", failed_order_ids)
            self.assertNotIn("order:ci_tiny_scorecard_plan_check_after_smoke", failed_order_ids)

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
                        "      - name: CI workflow hygiene check",
                        "        run: python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-ci",
                        "      - name: Promoted seed handoff assurance smoke",
                        "        run: python -B scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke-ci",
                        "      - name: CI tiny scorecard plan digest check",
                        "        run: python -B scripts/check_ci_tiny_scorecard_plan.py runs/tiny-scorecard-comparison-smoke-ci --out-dir runs/ci-tiny-scorecard-plan-check-ci",
                        "      - name: Baseline candidate threshold boundary gate check",
                        "        run: python -B scripts/check_baseline_candidate_threshold_boundary_gate.py --smoke-summary d/438/解释/baseline-candidate-threshold-boundary-smoke/tiny-scorecard-comparison-smoke/tiny_scorecard_comparison_smoke_summary.json --out-dir runs/baseline-candidate-threshold-boundary-gate-check-ci --thresholds 0:1:0.5 --require-diagnosis-pass --expected-exit-code 2 --expected-diagnosis-decision candidate_not_accepted --require-pass --force",
                        "      - name: Tiny scorecard comparison inline check smoke",
                        "        run: python -B scripts/run_ci_tiny_scorecard_comparison_smoke.py --out-dir runs/tiny-scorecard-comparison-smoke-ci --summary-check-out-dir runs/tiny-scorecard-comparison-smoke-check-ci",
                        "      - name: Release readiness drift contract smoke",
                        "        run: python -B scripts/check_release_readiness_drift_contract_smoke.py --out-dir runs/release-readiness-drift-contract-smoke-ci",
                        "      - name: Unit tests",
                        "        run: python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 80",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z")

            failed_order_ids = {item["id"] for item in report["checks"] if item["category"] == "required_order" and item["status"] == "fail"}
            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["missing_step_count"], 0)
            self.assertTrue(report["summary"]["tiny_scorecard_plan_digest_gate_present"])
            self.assertFalse(report["summary"]["tiny_scorecard_plan_digest_gate_order_ready"])
            self.assertFalse(report["summary"]["tiny_scorecard_plan_digest_gate_ready"])
            self.assertTrue(report["summary"]["baseline_candidate_threshold_boundary_gate_check_ready"])
            self.assertIn("order:ci_tiny_scorecard_plan_check_after_smoke", failed_order_ids)

    def test_ci_workflow_hygiene_outputs_json_csv_markdown_and_html(self) -> None:
        report = build_ci_workflow_hygiene_report(CI_WORKFLOW, project_root=ROOT, title="CI <workflow>", generated_at="2026-01-01T00:00:00Z")

        with TemporaryDirectory() as tmp:
            outputs = write_ci_workflow_hygiene_outputs(report, Path(tmp) / "out")

            for path in outputs.values():
                self.assertTrue(Path(path).exists())
            self.assertIn("actions/setup-python", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("CI &lt;workflow&gt;", render_ci_workflow_hygiene_html(report))
            self.assertIn("continue_with_node24_native_ci", render_ci_workflow_hygiene_markdown(report))
            self.assertIn("tiny_scorecard_plan_digest_gate_ready", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("baseline_candidate_threshold_boundary_gate_check_ready", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("release_readiness_drift_contract_smoke_ready", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("order_violation_count", Path(outputs["markdown"]).read_text(encoding="utf-8"))

    def test_ci_workflow_module_reexports_artifact_writers(self) -> None:
        self.assertIs(render_ci_workflow_hygiene_html, artifact_render_ci_workflow_hygiene_html)
        self.assertIs(write_ci_workflow_hygiene_outputs, artifact_write_ci_workflow_hygiene_outputs)


if __name__ == "__main__":
    unittest.main()
