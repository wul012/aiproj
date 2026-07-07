from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.artifact_schema_guard import (
    build_artifact_schema_guard_report,
    render_artifact_schema_guard_html,
    render_artifact_schema_guard_markdown,
    resolve_exit_code,
    write_artifact_schema_guard_outputs,
)
from scripts.check_artifact_schema_guard import main as cli_main
from tests._bootstrap import ROOT


REGISTRY = ROOT / "docs" / "artifact-schema-guard-registry.json"


class ArtifactSchemaGuardTests(unittest.TestCase):
    def test_current_registry_passes(self) -> None:
        report = build_artifact_schema_guard_report(REGISTRY, project_root=ROOT, generated_at="2026-07-07T00:00:00Z")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "continue_with_artifact_schema_guard")
        self.assertEqual(report["summary"]["schema_count"], 4)
        self.assertEqual(report["summary"]["artifact_count"], 4)
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_missing_required_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = _copy_registry(Path(tmp))
            payload = json.loads(registry.read_text(encoding="utf-8"))
            payload["schemas"][0]["required_fields"].append("missing_required_field")
            registry.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            report = build_artifact_schema_guard_report(registry, project_root=ROOT)

        self.assertEqual(report["status"], "fail")
        self.assertIn("field:missing_required_field", _failed_check_ids(report))

    def test_publication_receipt_promotion_widening_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = _copy_registry(Path(tmp))
            payload = json.loads(registry.read_text(encoding="utf-8"))
            payload["schemas"][3]["expected_values"]["summary.promotion_ready"] = True
            registry.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            report = build_artifact_schema_guard_report(registry, project_root=ROOT)

        self.assertEqual(report["status"], "fail")
        self.assertIn("value:summary.promotion_ready", _failed_check_ids(report))

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_artifact_schema_guard_report(REGISTRY, project_root=ROOT)
            outputs = write_artifact_schema_guard_outputs(report, root / "report")
            exit_code = cli_main(["--registry", str(REGISTRY), "--out-dir", str(root / "cli"), "--require-pass"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
        self.assertIn("failed_check_count", render_artifact_schema_guard_markdown(report))
        self.assertIn("artifact schema guard", render_artifact_schema_guard_html(report))


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
