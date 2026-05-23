from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import release_gate, release_gate_artifacts
from minigpt.release_gate import (
    build_release_gate,
    exit_code_for_gate,
    release_gate_policy_profiles,
    render_release_gate_html,
    resolve_release_gate_policy,
    write_release_gate_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_bundle(
    root: Path,
    *,
    release_name: str = "v27-demo",
    release_status: str = "release-ready",
    audit_status: str = "pass",
    audit_score: float | None = 100.0,
    ready_runs: int = 1,
    missing_artifacts: int = 0,
    warnings: list[str] | None = None,
    include_generation_checks: bool = True,
    generation_status: str = "pass",
    include_request_history_check: bool = True,
    request_history_status: str = "pass",
    include_benchmark_history_check: bool = True,
    benchmark_history_status: str = "pass",
    benchmark_history_entries: int | None = 1,
    benchmark_history_ready: int | None = 1,
    benchmark_history_review: int | None = 0,
    benchmark_history_blocked: int | None = 0,
    benchmark_history_case_regressions: int | None = 0,
    benchmark_history_generation_flag_regressions: int | None = 0,
    benchmark_history_suite_design_non_comparison_ready_entries: int | None = 0,
    benchmark_history_design_comparison_changed_entries: int | None = 0,
    benchmark_history_readiness_requirement_status: str | None = "pass",
    benchmark_history_readiness_requirement_exit_code: int | None = 0,
    benchmark_history_readiness_requirement_failed_reasons: list[str] | None = None,
    benchmark_history_model_quality_claim: str | None = "candidate_evidence",
    benchmark_history_latest_boundary: str | None = "standard-benchmark-candidate-evidence",
    include_test_coverage_check: bool = True,
    test_coverage_status: str = "pass",
) -> Path:
    audit_checks = [{"id": "ready_run", "title": "At least one ready run", "status": audit_status, "detail": "1 ready run."}]
    if include_generation_checks:
        audit_checks.extend(
            [
                {
                    "id": "generation_quality",
                    "title": "Generation quality coverage",
                    "status": generation_status,
                    "detail": "2/2 run(s).",
                },
                {
                    "id": "non_pass_generation_quality",
                    "title": "No non-pass generation quality runs",
                    "status": generation_status,
                    "detail": "all analyzed runs pass",
                },
            ]
        )
    if include_request_history_check:
        audit_checks.append(
            {
                "id": "request_history_summary",
                "title": "Request history summary is clean",
                "status": request_history_status,
                "detail": f"status={request_history_status}; records=4; invalid=0; timeout_rate=0; error_rate=0.",
            }
        )
    if include_benchmark_history_check:
        audit_checks.append(
            {
                "id": "benchmark_history",
                "title": "Benchmark history is audit-ready",
                "status": benchmark_history_status,
                "detail": (
                    f"entries={benchmark_history_entries}; ready={benchmark_history_ready}; "
                    f"review={benchmark_history_review}; blocked={benchmark_history_blocked}; "
                    f"case_regressions={benchmark_history_case_regressions}; "
                    f"generation_flag_regressions={benchmark_history_generation_flag_regressions}; "
                    f"suite_design_not_ready={benchmark_history_suite_design_non_comparison_ready_entries}; "
                    f"design_comparison_changed={benchmark_history_design_comparison_changed_entries}; "
                    f"readiness_requirement={benchmark_history_readiness_requirement_status}; "
                    f"readiness_exit={benchmark_history_readiness_requirement_exit_code}."
                ),
            }
        )
    if include_test_coverage_check:
        audit_checks.append(
            {
                "id": "test_coverage_report",
                "title": "Test coverage gate is clean",
                "status": test_coverage_status,
                "detail": f"status={test_coverage_status}; decision=continue_with_coverage_gate; line_coverage=90.15; fail_under=80; coverage_gap=0.",
            }
        )
    bundle = {
        "schema_version": 1,
        "title": "MiniGPT release bundle",
        "release_name": release_name,
        "generated_at": "2026-05-12T00:00:00Z",
        "summary": {
            "release_status": release_status,
            "audit_status": audit_status,
            "audit_score_percent": audit_score,
            "run_count": 2,
            "best_run_name": "candidate",
            "best_val_loss": 0.75,
            "ready_runs": ready_runs,
            "available_artifacts": 9,
            "missing_artifacts": missing_artifacts,
            "benchmark_history_status": benchmark_history_status if include_benchmark_history_check else None,
            "benchmark_history_entries": benchmark_history_entries if include_benchmark_history_check else None,
            "benchmark_history_ready": benchmark_history_ready if include_benchmark_history_check else None,
            "benchmark_history_review": benchmark_history_review if include_benchmark_history_check else None,
            "benchmark_history_blocked": benchmark_history_blocked if include_benchmark_history_check else None,
            "benchmark_history_case_regressions": benchmark_history_case_regressions if include_benchmark_history_check else None,
            "benchmark_history_generation_flag_regressions": (
                benchmark_history_generation_flag_regressions if include_benchmark_history_check else None
            ),
            "benchmark_history_suite_design_non_comparison_ready_entries": (
                benchmark_history_suite_design_non_comparison_ready_entries if include_benchmark_history_check else None
            ),
            "benchmark_history_design_comparison_changed_entries": (
                benchmark_history_design_comparison_changed_entries if include_benchmark_history_check else None
            ),
            "benchmark_history_readiness_requirement_status": (
                benchmark_history_readiness_requirement_status if include_benchmark_history_check else None
            ),
            "benchmark_history_readiness_requirement_exit_code": (
                benchmark_history_readiness_requirement_exit_code if include_benchmark_history_check else None
            ),
            "benchmark_history_readiness_requirement_failed_reasons": (
                benchmark_history_readiness_requirement_failed_reasons or [] if include_benchmark_history_check else None
            ),
            "benchmark_history_model_quality_claim": benchmark_history_model_quality_claim if include_benchmark_history_check else None,
            "benchmark_history_latest_boundary": benchmark_history_latest_boundary if include_benchmark_history_check else None,
            "test_coverage_status": test_coverage_status if include_test_coverage_check else None,
            "test_coverage_percent": 90.15 if include_test_coverage_check else None,
            "test_coverage_fail_under": 80.0 if include_test_coverage_check else None,
            "test_coverage_gap": 0.0 if include_test_coverage_check else None,
        },
        "artifacts": [
            {"key": "registry_json", "title": "Registry JSON", "path": str(root / "registry.json"), "exists": True},
            {"key": "project_audit_json", "title": "Project audit JSON", "path": str(root / "audit.json"), "exists": missing_artifacts == 0},
        ],
        "top_runs": [
            {
                "name": "candidate",
                "path": str(root / "run-a"),
                "status": "ready",
                "best_val_loss_rank": 1,
                "best_val_loss": 0.75,
                "best_val_loss_delta": 0.0,
                "dataset_quality": "pass",
                "eval_suite_cases": 3,
            }
        ],
        "audit_checks": audit_checks,
        "test_coverage_context": {
            "available": include_test_coverage_check,
            "status": test_coverage_status if include_test_coverage_check else None,
            "line_coverage_percent": 90.15 if include_test_coverage_check else None,
            "fail_under": 80.0 if include_test_coverage_check else None,
            "coverage_gap": 0.0 if include_test_coverage_check else None,
        },
        "recommendations": ["Release evidence is complete."],
        "warnings": warnings or [],
    }
    path = root / "release-bundle" / "release_bundle.json"
    write_json(path, bundle)
    return path


class ReleaseGateTests(unittest.TestCase):
    def test_release_gate_facade_keeps_artifact_writer_identity(self) -> None:
        self.assertIs(
            release_gate.render_release_gate_html,
            release_gate_artifacts.render_release_gate_html,
        )
        self.assertIs(
            release_gate.write_release_gate_outputs,
            release_gate_artifacts.write_release_gate_outputs,
        )

    def test_release_gate_policy_profiles_are_available(self) -> None:
        profiles = release_gate_policy_profiles()

        self.assertEqual(set(profiles), {"legacy", "review", "standard", "strict"})
        self.assertEqual(profiles["standard"]["minimum_audit_score"], 90.0)
        self.assertEqual(profiles["legacy"]["require_generation_quality"], False)
        self.assertEqual(profiles["standard"]["require_request_history_summary"], True)
        self.assertEqual(profiles["legacy"]["require_request_history_summary"], False)
        self.assertEqual(profiles["standard"]["require_benchmark_history"], True)
        self.assertEqual(profiles["legacy"]["require_benchmark_history"], False)
        self.assertEqual(profiles["standard"]["require_test_coverage"], True)
        self.assertEqual(profiles["legacy"]["require_test_coverage"], False)

        profiles["standard"]["minimum_audit_score"] = 1.0
        self.assertEqual(release_gate_policy_profiles()["standard"]["minimum_audit_score"], 90.0)

    def test_resolve_release_gate_policy_rejects_unknown_profile(self) -> None:
        with self.assertRaises(ValueError):
            resolve_release_gate_policy("unknown")

    def test_build_release_gate_passes_ready_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp))

            gate = build_release_gate(bundle_path, generated_at="2026-05-12T00:00:00Z")

            self.assertEqual(gate["summary"]["gate_status"], "pass")
            self.assertEqual(gate["summary"]["decision"], "approved")
            self.assertEqual(gate["summary"]["fail_count"], 0)
            self.assertEqual(gate["policy"]["policy_profile"], "standard")
            self.assertEqual(gate["policy"]["minimum_audit_score"], 90.0)
            self.assertEqual(gate["policy"]["require_generation_quality_audit_checks"], True)
            self.assertEqual(gate["policy"]["require_request_history_summary_audit_check"], True)
            self.assertEqual(gate["policy"]["require_benchmark_history_gate_check"], True)
            self.assertEqual(gate["policy"]["require_test_coverage_audit_check"], True)
            self.assertIn("generation_quality_audit_checks", {check["id"] for check in gate["checks"]})
            self.assertIn("request_history_summary_audit_check", {check["id"] for check in gate["checks"]})
            self.assertIn("benchmark_history_gate_check", {check["id"] for check in gate["checks"]})
            self.assertIn("test_coverage_audit_check", {check["id"] for check in gate["checks"]})
            self.assertEqual(gate["summary"]["benchmark_history_status"], "pass")
            self.assertEqual(gate["summary"]["benchmark_history_ready"], 1)
            self.assertEqual(gate["summary"]["benchmark_history_suite_design_non_comparison_ready_entries"], 0)
            self.assertEqual(gate["summary"]["benchmark_history_design_comparison_changed_entries"], 0)
            self.assertEqual(gate["summary"]["benchmark_history_readiness_requirement_status"], "pass")
            self.assertEqual(gate["summary"]["benchmark_history_readiness_requirement_exit_code"], 0)
            self.assertEqual(exit_code_for_gate(gate), 0)
            self.assertIn("Release gate passed", " ".join(gate["recommendations"]))

    def test_strict_profile_raises_audit_score_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), audit_score=92.0)

            gate = build_release_gate(bundle_path, policy_profile="strict")

            self.assertEqual(gate["policy"]["policy_profile"], "strict")
            self.assertEqual(gate["policy"]["minimum_audit_score"], 95.0)
            self.assertEqual(gate["summary"]["gate_status"], "fail")
            check = next(item for item in gate["checks"] if item["id"] == "audit_score")
            self.assertEqual(check["status"], "fail")
            self.assertIn("minimum=95%", check["detail"])

    def test_review_profile_lowers_audit_score_threshold_but_keeps_generation_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), audit_score=85.0)

            gate = build_release_gate(bundle_path, policy_profile="review")

            self.assertEqual(gate["policy"]["policy_profile"], "review")
            self.assertEqual(gate["policy"]["minimum_audit_score"], 80.0)
            self.assertEqual(gate["policy"]["require_generation_quality_audit_checks"], True)
            self.assertEqual(gate["summary"]["gate_status"], "pass")

    def test_build_release_gate_warns_for_bundle_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), warnings=["model card was auto-discovered"])

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "warn")
            self.assertEqual(gate["summary"]["decision"], "needs-review")
            self.assertEqual(exit_code_for_gate(gate), 0)
            self.assertEqual(exit_code_for_gate(gate, fail_on_warn=True), 1)
            self.assertIn("Bundle has no warnings", " ".join(gate["recommendations"]))

    def test_build_release_gate_fails_when_generation_quality_checks_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_generation_checks=False)

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "fail")
            self.assertEqual(gate["summary"]["decision"], "blocked")
            check = next(item for item in gate["checks"] if item["id"] == "generation_quality_audit_checks")
            self.assertEqual(check["status"], "fail")
            self.assertIn("missing required audit check", check["detail"])
            self.assertEqual(exit_code_for_gate(gate), 1)

    def test_build_release_gate_can_allow_legacy_bundles_without_generation_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_generation_checks=False)

            gate = build_release_gate(bundle_path, require_generation_quality=False)

            self.assertEqual(gate["summary"]["gate_status"], "pass")
            self.assertEqual(gate["policy"]["require_generation_quality_audit_checks"], False)
            check = next(item for item in gate["checks"] if item["id"] == "generation_quality_audit_checks")
            self.assertEqual(check["status"], "pass")

    def test_legacy_profile_allows_missing_generation_quality_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_generation_checks=False, audit_score=84.0)

            gate = build_release_gate(bundle_path, policy_profile="legacy")

            self.assertEqual(gate["policy"]["policy_profile"], "legacy")
            self.assertEqual(gate["policy"]["minimum_audit_score"], 80.0)
            self.assertEqual(gate["policy"]["require_generation_quality_audit_checks"], False)
            self.assertEqual(gate["policy"]["require_request_history_summary_audit_check"], False)
            self.assertEqual(gate["policy"]["require_benchmark_history_gate_check"], False)
            self.assertEqual(gate["summary"]["gate_status"], "pass")

    def test_explicit_overrides_take_precedence_over_policy_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_generation_checks=False, audit_score=92.0)

            gate = build_release_gate(
                bundle_path,
                policy_profile="strict",
                minimum_audit_score=90.0,
                require_generation_quality=False,
                require_request_history_summary=False,
                require_benchmark_history=False,
                require_test_coverage=False,
            )

            self.assertEqual(gate["policy"]["policy_profile"], "strict")
            self.assertEqual(gate["policy"]["minimum_audit_score"], 90.0)
            self.assertEqual(gate["policy"]["require_generation_quality_audit_checks"], False)
            self.assertEqual(gate["policy"]["require_request_history_summary_audit_check"], False)
            self.assertEqual(gate["policy"]["require_benchmark_history_gate_check"], False)
            self.assertEqual(gate["policy"]["require_test_coverage_audit_check"], False)
            self.assertEqual(
                gate["policy"]["overrides"],
                {
                    "minimum_audit_score": True,
                    "minimum_ready_runs": False,
                    "require_generation_quality": True,
                    "require_request_history_summary": True,
                    "require_benchmark_history": True,
                    "require_test_coverage": True,
                },
            )
            self.assertEqual(gate["summary"]["gate_status"], "pass")

    def test_build_release_gate_warns_for_generation_quality_audit_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), generation_status="warn")

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "warn")
            check = next(item for item in gate["checks"] if item["id"] == "generation_quality_audit_checks")
            self.assertEqual(check["status"], "warn")
            self.assertEqual(exit_code_for_gate(gate), 0)
            self.assertEqual(exit_code_for_gate(gate, fail_on_warn=True), 1)

    def test_build_release_gate_fails_when_request_history_summary_check_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_request_history_check=False)

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "fail")
            check = next(item for item in gate["checks"] if item["id"] == "request_history_summary_audit_check")
            self.assertEqual(check["status"], "fail")
            self.assertIn("missing required audit check", check["detail"])

    def test_legacy_profile_allows_missing_request_history_summary_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_request_history_check=False, audit_score=84.0)

            gate = build_release_gate(bundle_path, policy_profile="legacy")

            self.assertEqual(gate["policy"]["require_request_history_summary_audit_check"], False)
            self.assertEqual(gate["summary"]["gate_status"], "pass")

    def test_build_release_gate_warns_for_request_history_summary_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), request_history_status="warn")

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "warn")
            check = next(item for item in gate["checks"] if item["id"] == "request_history_summary_audit_check")
            self.assertEqual(check["status"], "warn")

    def test_build_release_gate_fails_when_benchmark_history_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_benchmark_history_check=False)

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "fail")
            check = next(item for item in gate["checks"] if item["id"] == "benchmark_history_gate_check")
            self.assertEqual(check["status"], "fail")
            self.assertIn("missing required benchmark_history", check["detail"])

    def test_legacy_profile_allows_missing_benchmark_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_benchmark_history_check=False, audit_score=84.0)

            gate = build_release_gate(bundle_path, policy_profile="legacy")

            self.assertEqual(gate["policy"]["require_benchmark_history_gate_check"], False)
            self.assertEqual(gate["summary"]["gate_status"], "pass")

    def test_build_release_gate_warns_for_benchmark_history_review_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(
                Path(tmp),
                benchmark_history_status="warn",
                benchmark_history_ready=0,
                benchmark_history_review=1,
                benchmark_history_case_regressions=1,
                benchmark_history_model_quality_claim="not_claimed",
                benchmark_history_latest_boundary="tiny-smoke-plumbing-evidence",
            )

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "warn")
            check = next(item for item in gate["checks"] if item["id"] == "benchmark_history_gate_check")
            self.assertEqual(check["status"], "warn")
            self.assertIn("case_regressions=1", check["detail"])
            self.assertEqual(exit_code_for_gate(gate), 0)
            self.assertEqual(exit_code_for_gate(gate, fail_on_warn=True), 1)

    def test_build_release_gate_warns_for_benchmark_history_suite_design_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(
                Path(tmp),
                benchmark_history_status="pass",
                benchmark_history_suite_design_non_comparison_ready_entries=1,
                benchmark_history_design_comparison_changed_entries=1,
            )

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "warn")
            self.assertEqual(gate["summary"]["decision"], "needs-review")
            self.assertEqual(gate["summary"]["benchmark_history_status"], "pass")
            self.assertEqual(gate["summary"]["benchmark_history_suite_design_non_comparison_ready_entries"], 1)
            self.assertEqual(gate["summary"]["benchmark_history_design_comparison_changed_entries"], 1)
            check = next(item for item in gate["checks"] if item["id"] == "benchmark_history_gate_check")
            self.assertEqual(check["status"], "warn")
            self.assertIn("suite_design_not_ready=1", check["detail"])
            self.assertIn("design_comparison_changed=1", check["detail"])
            self.assertEqual(exit_code_for_gate(gate), 0)
            self.assertEqual(exit_code_for_gate(gate, fail_on_warn=True), 1)

    def test_build_release_gate_warns_for_benchmark_history_readiness_requirement_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(
                Path(tmp),
                benchmark_history_status="pass",
                benchmark_history_ready=1,
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=["insufficient_ready_entries"],
            )

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "warn")
            self.assertEqual(gate["summary"]["benchmark_history_readiness_requirement_status"], "fail")
            self.assertEqual(gate["summary"]["benchmark_history_readiness_requirement_exit_code"], 1)
            self.assertEqual(
                gate["summary"]["benchmark_history_readiness_requirement_failed_reasons"],
                ["insufficient_ready_entries"],
            )
            check = next(item for item in gate["checks"] if item["id"] == "benchmark_history_gate_check")
            self.assertEqual(check["status"], "warn")
            self.assertIn("readiness_requirement=fail", check["detail"])
            self.assertIn("readiness_failed_reasons=insufficient_ready_entries", check["detail"])
            self.assertEqual(exit_code_for_gate(gate), 0)
            self.assertEqual(exit_code_for_gate(gate, fail_on_warn=True), 1)

    def test_build_release_gate_fails_for_blocked_benchmark_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(
                Path(tmp),
                benchmark_history_status="pass",
                benchmark_history_blocked=1,
            )

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "fail")
            check = next(item for item in gate["checks"] if item["id"] == "benchmark_history_gate_check")
            self.assertEqual(check["status"], "fail")
            self.assertIn("blocked=1", check["detail"])

    def test_build_release_gate_fails_when_test_coverage_check_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_test_coverage_check=False)

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "fail")
            check = next(item for item in gate["checks"] if item["id"] == "test_coverage_audit_check")
            self.assertEqual(check["status"], "fail")
            self.assertIn("missing required audit check", check["detail"])

    def test_legacy_profile_allows_missing_test_coverage_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_test_coverage_check=False, audit_score=84.0)

            gate = build_release_gate(bundle_path, policy_profile="legacy")

            self.assertEqual(gate["policy"]["require_test_coverage_audit_check"], False)
            self.assertEqual(gate["summary"]["gate_status"], "pass")

    def test_build_release_gate_warns_for_test_coverage_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), test_coverage_status="warn")

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "warn")
            check = next(item for item in gate["checks"] if item["id"] == "test_coverage_audit_check")
            self.assertEqual(check["status"], "warn")

    def test_build_release_gate_fails_for_incomplete_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(
                Path(tmp),
                release_status="blocked",
                audit_status="fail",
                audit_score=40.0,
                ready_runs=0,
                missing_artifacts=2,
            )

            gate = build_release_gate(bundle_path, minimum_audit_score=90.0, minimum_ready_runs=1)

            self.assertEqual(gate["summary"]["gate_status"], "fail")
            self.assertEqual(gate["summary"]["decision"], "blocked")
            self.assertGreater(gate["summary"]["fail_count"], 0)
            self.assertEqual(exit_code_for_gate(gate), 1)
            self.assertIn("Release gate failed", " ".join(gate["recommendations"]))

    def test_write_release_gate_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_bundle(root)
            gate = build_release_gate(bundle_path)

            outputs = write_release_gate_outputs(gate, root / "release-gate")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Checks", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history readiness", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history readiness exit", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history suite-design not-ready", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history design changes", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT release gate", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench design review", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench design changes", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench readiness", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench readiness exit", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_cli_prints_release_gate_benchmark_history_suite_design_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_bundle(root)
            out_dir = root / "release-gate"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "check_release_gate.py"),
                    "--bundle",
                    str(bundle_path),
                    "--out-dir",
                    str(out_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("benchmark_history_suite_design_non_comparison_ready_entries=0", completed.stdout)
            self.assertIn("benchmark_history_design_comparison_changed_entries=0", completed.stdout)

    def test_render_release_gate_html_escapes_release_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), release_name="<script>")
            gate = build_release_gate(bundle_path, title="<Gate>")

            html = render_release_gate_html(gate)

            self.assertIn("&lt;Gate&gt;", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<h1><Gate>", html)


if __name__ == "__main__":
    unittest.main()
