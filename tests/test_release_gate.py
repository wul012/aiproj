from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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
        "recommendations": ["Release evidence is complete."],
        "warnings": warnings or [],
    }
    path = root / "release-bundle" / "release_bundle.json"
    write_json(path, bundle)
    return path


class ReleaseGateTests(unittest.TestCase):
    def test_release_gate_policy_profiles_are_available(self) -> None:
        profiles = release_gate_policy_profiles()

        self.assertEqual(set(profiles), {"legacy", "review", "standard", "strict"})
        self.assertEqual(profiles["standard"]["minimum_audit_score"], 90.0)
        self.assertEqual(profiles["legacy"]["require_generation_quality"], False)

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
            self.assertIn("generation_quality_audit_checks", {check["id"] for check in gate["checks"]})
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
            self.assertEqual(gate["summary"]["gate_status"], "pass")

    def test_explicit_overrides_take_precedence_over_policy_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), include_generation_checks=False, audit_score=92.0)

            gate = build_release_gate(
                bundle_path,
                policy_profile="strict",
                minimum_audit_score=90.0,
                require_generation_quality=False,
            )

            self.assertEqual(gate["policy"]["policy_profile"], "strict")
            self.assertEqual(gate["policy"]["minimum_audit_score"], 90.0)
            self.assertEqual(gate["policy"]["require_generation_quality_audit_checks"], False)
            self.assertEqual(
                gate["policy"]["overrides"],
                {
                    "minimum_audit_score": True,
                    "minimum_ready_runs": False,
                    "require_generation_quality": True,
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
            self.assertIn("MiniGPT release gate", Path(outputs["html"]).read_text(encoding="utf-8"))

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
