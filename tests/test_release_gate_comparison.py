from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_gate_comparison import (
    build_release_gate_profile_comparison,
    render_release_gate_profile_comparison_html,
    render_release_gate_profile_comparison_markdown,
    write_release_gate_profile_comparison_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_bundle(
    root: Path,
    *,
    release_name: str = "v32-demo",
    audit_score: float | None = 100.0,
    include_generation_checks: bool = True,
    warnings: list[str] | None = None,
) -> Path:
    audit_checks = [{"id": "ready_run", "title": "At least one ready run", "status": "pass", "detail": "1 ready run."}]
    if include_generation_checks:
        audit_checks.extend(
            [
                {
                    "id": "generation_quality",
                    "title": "Generation quality coverage",
                    "status": "pass",
                    "detail": "2/2 run(s).",
                },
                {
                    "id": "non_pass_generation_quality",
                    "title": "No non-pass generation quality runs",
                    "status": "pass",
                    "detail": "all analyzed runs pass",
                },
            ]
        )
    bundle = {
        "schema_version": 1,
        "title": "MiniGPT release bundle",
        "release_name": release_name,
        "generated_at": "2026-05-13T00:00:00Z",
        "summary": {
            "release_status": "release-ready",
            "audit_status": "pass",
            "audit_score_percent": audit_score,
            "run_count": 2,
            "best_run_name": "candidate",
            "best_val_loss": 0.75,
            "ready_runs": 1,
            "available_artifacts": 9,
            "missing_artifacts": 0,
        },
        "artifacts": [
            {"key": "registry_json", "title": "Registry JSON", "path": str(root / "registry.json"), "exists": True},
            {"key": "project_audit_json", "title": "Project audit JSON", "path": str(root / "audit.json"), "exists": True},
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


class ReleaseGateProfileComparisonTests(unittest.TestCase):
    def test_build_profile_comparison_matrix_for_one_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), audit_score=92.0)

            report = build_release_gate_profile_comparison([bundle_path], generated_at="2026-05-13T00:00:00Z")

            self.assertEqual(report["summary"]["bundle_count"], 1)
            self.assertEqual(report["summary"]["profile_count"], 4)
            self.assertEqual(report["summary"]["row_count"], 4)
            self.assertEqual(report["summary"]["approved_count"], 3)
            self.assertEqual(report["summary"]["blocked_count"], 1)
            strict = next(row for row in report["rows"] if row["policy_profile"] == "strict")
            self.assertEqual(strict["decision"], "blocked")
            self.assertIn("audit_score", strict["failed_checks"])
            standard = next(row for row in report["rows"] if row["policy_profile"] == "standard")
            self.assertEqual(standard["decision"], "approved")

    def test_legacy_profile_can_be_compared_against_missing_generation_quality_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), audit_score=84.0, include_generation_checks=False)

            report = build_release_gate_profile_comparison([bundle_path], policy_profiles=["standard", "review", "legacy"])

            by_profile = {row["policy_profile"]: row for row in report["rows"]}
            self.assertEqual(by_profile["standard"]["decision"], "blocked")
            self.assertIn("audit_score", by_profile["standard"]["failed_checks"])
            self.assertIn("generation_quality_audit_checks", by_profile["standard"]["failed_checks"])
            self.assertEqual(by_profile["review"]["decision"], "blocked")
            self.assertIn("generation_quality_audit_checks", by_profile["review"]["failed_checks"])
            self.assertEqual(by_profile["legacy"]["decision"], "approved")
            self.assertEqual(by_profile["legacy"]["require_generation_quality_audit_checks"], False)

    def test_profile_comparison_supports_multiple_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_a = make_bundle(root / "a", release_name="bundle-a", audit_score=100.0)
            bundle_b = make_bundle(root / "b", release_name="bundle-b", audit_score=70.0)

            report = build_release_gate_profile_comparison([bundle_a, bundle_b], policy_profiles=["standard", "legacy"])

            self.assertEqual(report["summary"]["bundle_count"], 2)
            self.assertEqual(report["summary"]["profile_count"], 2)
            self.assertEqual(report["summary"]["row_count"], 4)
            self.assertEqual(len({row["release_name"] for row in report["rows"]}), 2)
            self.assertEqual(report["summary"]["blocked_count"], 2)

    def test_profile_comparison_rejects_empty_or_unknown_inputs(self) -> None:
        with self.assertRaises(ValueError):
            build_release_gate_profile_comparison([])
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp))
            with self.assertRaises(ValueError):
                build_release_gate_profile_comparison([bundle_path], policy_profiles=["unknown"])

    def test_write_profile_comparison_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_bundle(root, audit_score=92.0)
            report = build_release_gate_profile_comparison([bundle_path])

            outputs = write_release_gate_profile_comparison_outputs(report, root / "comparison")

            json_payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            md_text = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html_text = Path(outputs["html"]).read_text(encoding="utf-8")
            self.assertEqual(json_payload["summary"]["row_count"], 4)
            self.assertIn("policy_profile,gate_status", csv_text)
            self.assertIn("## Profile Matrix", md_text)
            self.assertIn("Profile Matrix", html_text)

    def test_profile_comparison_renderers_escape_release_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), release_name="<script>", audit_score=100.0)
            report = build_release_gate_profile_comparison([bundle_path], policy_profiles=["standard"])

            html = render_release_gate_profile_comparison_html(report)
            markdown = render_release_gate_profile_comparison_markdown(report)

            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<td><script>", html)
            self.assertIn("<script>", markdown)


if __name__ == "__main__":
    unittest.main()
