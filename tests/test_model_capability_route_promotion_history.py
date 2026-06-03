from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review import (
    build_objective_level_contrast_acceptance_review,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_JSON_FILENAME,
    build_objective_level_contrast_promotion_manifest,
)
from minigpt.model_capability_route_promotion_history import (
    build_model_capability_route_promotion_history,
    locate_route_promotion_manifest,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_history_artifacts import (
    render_model_capability_route_promotion_history_html,
    render_model_capability_route_promotion_history_markdown,
    render_model_capability_route_promotion_history_text,
    write_model_capability_route_promotion_history_outputs,
)
from scripts.build_model_capability_route_promotion_history import main as cli_main
from tests.test_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review import (
    ready_rollup_fixture,
)


def ready_promotion_manifest() -> dict:
    review = build_objective_level_contrast_acceptance_review(ready_rollup_fixture())
    return build_objective_level_contrast_promotion_manifest(review)


class ModelCapabilityRoutePromotionHistoryTests(unittest.TestCase):
    def test_builds_ready_history_from_promotion_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = _write_manifest(Path(tmp), ready_promotion_manifest())

            report = build_model_capability_route_promotion_history([manifest_path], names=["objective-level contrast"])

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_history_ready")
        self.assertEqual(report["summary"]["entry_count"], 1)
        self.assertEqual(report["summary"]["ready_count"], 1)
        self.assertEqual(report["summary"]["boundary_mismatch_count"], 0)
        self.assertEqual(report["entries"][0]["promotion_readiness"], "ready")
        self.assertEqual(report["entries"][0]["route_id"], "objective_level_contrast")
        self.assertEqual(resolve_exit_code(report, require_ready_history=True), 0)

    def test_rejects_boundary_mismatch(self) -> None:
        manifest = ready_promotion_manifest()
        manifest["manifest"]["benchmark_history_entry"]["boundary"] = "production_model_quality"
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = _write_manifest(Path(tmp), manifest)

            report = build_model_capability_route_promotion_history([manifest_path])

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["boundary_mismatch_count"], 1)
        self.assertIn("route_promotion_boundary_mismatches", report["readiness_requirement"]["failed_reasons"])
        self.assertEqual(resolve_exit_code(report, require_ready_history=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        manifest = ready_promotion_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = _write_manifest(root, manifest)
            manifest_dir = manifest_path.parent

            self.assertEqual(locate_route_promotion_manifest(manifest_dir), manifest_path)
            report = build_model_capability_route_promotion_history([manifest_dir])
            outputs = write_model_capability_route_promotion_history_outputs(report, root / "history")
            cli_main([str(manifest_dir), "--out-dir", str(root / "cli-history"), "--require-ready-history", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("ready_count=1", render_model_capability_route_promotion_history_text(report))
        self.assertIn("model capability route promotion history", render_model_capability_route_promotion_history_markdown(report))
        self.assertIn("Tracks route promotion manifests", render_model_capability_route_promotion_history_html(report))


def _write_manifest(root: Path, manifest: dict) -> Path:
    out_dir = root / "manifest"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PROMOTION_MANIFEST_JSON_FILENAME
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
