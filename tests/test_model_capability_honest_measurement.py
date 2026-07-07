from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.model_capability_honest_measurement import (
    build_model_capability_honest_measurement_report,
    render_model_capability_honest_measurement_html,
    render_model_capability_honest_measurement_markdown,
    resolve_exit_code,
    write_model_capability_honest_measurement_outputs,
)
from scripts.check_model_capability_honest_measurement import main as cli_main
from tests._bootstrap import ROOT


REGISTRY = ROOT / "docs" / "model-capability-honest-measurement-registry.json"


class ModelCapabilityHonestMeasurementTests(unittest.TestCase):
    def test_current_registry_passes(self) -> None:
        report = build_model_capability_honest_measurement_report(
            REGISTRY, project_root=ROOT, generated_at="2026-07-07T00:00:00Z"
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "continue_with_honest_measurement_gate")
        self.assertEqual(report["summary"]["family_count"], 2)
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_single_seed_stochastic_claim_must_be_exploratory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = _copy_registry(Path(tmp))
            payload = json.loads(registry.read_text(encoding="utf-8"))
            payload["families"][0]["single_seed_label"] = "seed_stable_claim"
            registry.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            report = build_model_capability_honest_measurement_report(registry, project_root=ROOT)

        self.assertEqual(report["status"], "fail")
        self.assertIn("single_seed_label", _failed_check_ids(report))
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_missing_negative_marker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = _copy_registry(Path(tmp))
            payload = json.loads(registry.read_text(encoding="utf-8"))
            payload["families"][0]["negative_test_markers"].append("test_marker_that_does_not_exist")
            registry.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            report = build_model_capability_honest_measurement_report(registry, project_root=ROOT)

        self.assertEqual(report["status"], "fail")
        self.assertIn("marker:test_marker_that_does_not_exist", _failed_check_ids(report))

    def test_missing_source_artifact_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = _copy_registry(Path(tmp))
            payload = json.loads(registry.read_text(encoding="utf-8"))
            payload["families"][0]["source_artifacts"][0] = "missing/handoff.json"
            registry.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            report = build_model_capability_honest_measurement_report(registry, project_root=ROOT)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_artifacts[0]", _failed_check_ids(report))

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_honest_measurement_report(REGISTRY, project_root=ROOT)
            outputs = write_model_capability_honest_measurement_outputs(report, root / "report")
            exit_code = cli_main(["--registry", str(REGISTRY), "--out-dir", str(root / "cli"), "--require-pass"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
        self.assertIn("failed_check_count", render_model_capability_honest_measurement_markdown(report))
        self.assertIn("honest measurement gate", render_model_capability_honest_measurement_html(report))


def _copy_registry(root: Path) -> Path:
    path = root / "registry.json"
    path.write_text(REGISTRY.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _failed_check_ids(report: dict[str, object]) -> set[str]:
    checks = report.get("checks")
    if not isinstance(checks, list):
        return set()
    return {str(item.get("check_id")) for item in checks if isinstance(item, dict) and item.get("status") == "fail"}


if __name__ == "__main__":
    unittest.main()
