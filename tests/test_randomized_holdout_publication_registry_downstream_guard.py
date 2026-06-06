from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_guard import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_guard,
    locate_randomized_holdout_publication_registry_lookup_index_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_guard_artifacts import (
    render_randomized_holdout_publication_registry_downstream_guard_html,
    render_randomized_holdout_publication_registry_downstream_guard_markdown,
    render_randomized_holdout_publication_registry_downstream_guard_text,
    write_randomized_holdout_publication_registry_downstream_guard_outputs,
)
from minigpt.randomized_holdout_publication_registry_lookup_index_review import build_randomized_holdout_publication_registry_lookup_index_review
from minigpt.randomized_holdout_publication_registry_lookup_index_review_artifacts import write_randomized_holdout_publication_registry_lookup_index_review_outputs
from scripts.build_randomized_holdout_publication_registry_downstream_guard import main as cli_main
from tests.test_randomized_holdout_publication_registry_lookup_index_review import ready_review_inputs


class RandomizedHoldoutPublicationRegistryDownstreamGuardTests(unittest.TestCase):
    def test_downstream_guard_accepts_lookup_index_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_guard_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_guard(review, lookup_index_review_path=review_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_guard_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_guard_ready"])
        self.assertEqual(report["summary"]["guard_status"], "downstream_governance_lookup_allowed")
        self.assertTrue(report["summary"]["downstream_ready"])
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["allowed_use"], "downstream_governance_lookup_only")
        self.assertIn("production_promotion", report["summary"]["blocked_uses"])
        self.assertEqual(report["summary"]["next_step"], "record_randomized_holdout_publication_registry_downstream_receipt")
        self.assertEqual(resolve_exit_code(report, require_guard_ready=True, require_downstream_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_guard_ready=True, require_promotion_ready=True), 1)

    def test_downstream_guard_fails_when_production_promotion_is_not_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_guard_inputs(Path(tmp))
            review["summary"]["rejected_use"] = "none"
            report = build_randomized_holdout_publication_registry_downstream_guard(review, lookup_index_review_path=review_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("rejected_use_production_promotion", [issue["id"] for issue in report["issues"]])

    def test_downstream_guard_fails_when_promotion_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_guard_inputs(Path(tmp))
            review["summary"]["promotion_ready"] = True
            report = build_randomized_holdout_publication_registry_downstream_guard(review, lookup_index_review_path=review_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_guard_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_lookup_index_review(review_path.parent), review_path)
            report = build_randomized_holdout_publication_registry_downstream_guard(review, lookup_index_review_path=review_path)
            outputs = write_randomized_holdout_publication_registry_downstream_guard_outputs(report, root / "guard")
            cli_main(
                [
                    "--lookup-index-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "cli-guard"),
                    "--require-guard-ready",
                    "--require-downstream-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_guard_ready=True", render_randomized_holdout_publication_registry_downstream_guard_text(report))
        self.assertIn("downstream_governance_lookup_allowed", render_randomized_holdout_publication_registry_downstream_guard_markdown(report))
        self.assertIn("publication registry downstream guard", render_randomized_holdout_publication_registry_downstream_guard_html(report))


def ready_guard_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index, index_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_registry_lookup_index_review(index, lookup_index_path=index_path)
    review_outputs = write_randomized_holdout_publication_registry_lookup_index_review_outputs(review, root / "review")
    return review, Path(review_outputs["json"])


if __name__ == "__main__":
    unittest.main()
