from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review import (
    build_objective_level_contrast_acceptance_review,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest import (
    build_objective_level_contrast_promotion_manifest,
    locate_objective_level_contrast_promotion_manifest_acceptance_review,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest_artifacts import (
    render_objective_level_contrast_promotion_manifest_html,
    render_objective_level_contrast_promotion_manifest_markdown,
    render_objective_level_contrast_promotion_manifest_text,
    write_objective_level_contrast_promotion_manifest_outputs,
)
from scripts.run_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest import (
    main as cli_main,
)
from tests.test_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review import (
    ready_rollup_fixture,
)


class ObjectiveLevelContrastPromotionManifestTests(unittest.TestCase):
    def test_builds_manifest_from_accepted_review(self) -> None:
        review = build_objective_level_contrast_acceptance_review(ready_rollup_fixture())
        report = build_objective_level_contrast_promotion_manifest(review)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_level_contrast_promotion_manifest_ready")
        self.assertTrue(report["summary"]["promotion_manifest_ready"])
        self.assertTrue(report["summary"]["can_feed_benchmark_history"])
        self.assertEqual(report["manifest"]["route_status"], "promoted")
        self.assertEqual(report["manifest"]["benchmark_history_entry"]["entry_type"], "model_capability_route_promotion")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_rejects_wrong_route_id(self) -> None:
        review = build_objective_level_contrast_acceptance_review(ready_rollup_fixture())
        report = build_objective_level_contrast_promotion_manifest(review, route_id="other_route")

        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["summary"]["promotion_manifest_ready"])
        self.assertIn("route_id_matches", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_rejects_when_boundary_is_not_pair_probe_scoped(self) -> None:
        review = build_objective_level_contrast_acceptance_review(ready_rollup_fixture())
        review["summary"]["model_quality_boundary"] = "production_model_quality"

        report = build_objective_level_contrast_promotion_manifest(review)

        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["summary"]["promotion_manifest_ready"])
        self.assertIn("boundary_scoped", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        review = build_objective_level_contrast_acceptance_review(ready_rollup_fixture())
        report = build_objective_level_contrast_promotion_manifest(review)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "review"
            review_dir.mkdir()
            review_path = review_dir / "model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.json"
            review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")

            self.assertEqual(locate_objective_level_contrast_promotion_manifest_acceptance_review(review_dir), review_path)
            outputs = write_objective_level_contrast_promotion_manifest_outputs(report, root / "manifest")
            cli_main(["--acceptance-review", str(review_dir), "--out-dir", str(root / "cli-manifest"), "--force", "--require-pass"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("promotion_manifest_ready=True", render_objective_level_contrast_promotion_manifest_text(report))
        self.assertIn("Objective-Level Contrast Promotion Manifest", render_objective_level_contrast_promotion_manifest_markdown(report))
        self.assertIn("MiniGPT objective-level contrast promotion manifest", render_objective_level_contrast_promotion_manifest_html(report))


if __name__ == "__main__":
    unittest.main()
