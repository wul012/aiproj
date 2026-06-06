from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_guard import build_randomized_holdout_publication_registry_downstream_guard
from minigpt.randomized_holdout_publication_registry_downstream_guard_artifacts import write_randomized_holdout_publication_registry_downstream_guard_outputs
from minigpt.randomized_holdout_publication_registry_downstream_receipt import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_receipt,
    locate_randomized_holdout_publication_registry_downstream_guard,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_receipt_artifacts import (
    render_randomized_holdout_publication_registry_downstream_receipt_html,
    render_randomized_holdout_publication_registry_downstream_receipt_markdown,
    render_randomized_holdout_publication_registry_downstream_receipt_text,
    write_randomized_holdout_publication_registry_downstream_receipt_outputs,
)
from scripts.build_randomized_holdout_publication_registry_downstream_receipt import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_guard import ready_guard_inputs


class RandomizedHoldoutPublicationRegistryDownstreamReceiptTests(unittest.TestCase):
    def test_downstream_receipt_accepts_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard, guard_path = ready_receipt_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_receipt(guard, downstream_guard_path=guard_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_receipt_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_receipt_ready"])
        self.assertEqual(report["summary"]["receipt_status"], "downstream_governance_lookup_receipted")
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["entry_count"], 1)
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertIn("model_quality_expansion", report["summary"]["blocked_uses"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_registry_downstream_receipt")
        self.assertEqual(len(report["downstream_guard_sha256"]), 64)
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True, require_promotion_ready=True), 1)

    def test_downstream_receipt_rejects_missing_blocked_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard, guard_path = ready_receipt_inputs(Path(tmp))
            guard["summary"]["blocked_uses"] = ["production_promotion"]
            report = build_randomized_holdout_publication_registry_downstream_receipt(guard, downstream_guard_path=guard_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("blocked_uses_complete", [issue["id"] for issue in report["issues"]])

    def test_downstream_receipt_rejects_promotion_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard, guard_path = ready_receipt_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_receipt(
                guard,
                downstream_guard_path=guard_path,
                requested_use="production_promotion",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("requested_use_allowed", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            guard, guard_path = ready_receipt_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_guard(guard_path.parent), guard_path)
            report = build_randomized_holdout_publication_registry_downstream_receipt(guard, downstream_guard_path=guard_path)
            outputs = write_randomized_holdout_publication_registry_downstream_receipt_outputs(report, root / "receipt")
            cli_main(
                [
                    "--guard",
                    str(guard_path.parent),
                    "--out-dir",
                    str(root / "cli-receipt"),
                    "--require-receipt-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_receipt_ready=True", render_randomized_holdout_publication_registry_downstream_receipt_text(report))
        self.assertIn("downstream_governance_lookup_receipted", render_randomized_holdout_publication_registry_downstream_receipt_markdown(report))
        self.assertIn("publication registry downstream receipt", render_randomized_holdout_publication_registry_downstream_receipt_html(report))


def ready_receipt_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_guard_inputs(root)
    guard = build_randomized_holdout_publication_registry_downstream_guard(review, lookup_index_review_path=review_path)
    guard_outputs = write_randomized_holdout_publication_registry_downstream_guard_outputs(guard, root / "guard")
    return guard, Path(guard_outputs["json"])


if __name__ == "__main__":
    unittest.main()
