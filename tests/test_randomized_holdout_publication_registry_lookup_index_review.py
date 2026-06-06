from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_lookup_index import build_randomized_holdout_publication_registry_lookup_index
from minigpt.randomized_holdout_publication_registry_lookup_index_artifacts import write_randomized_holdout_publication_registry_lookup_index_outputs
from minigpt.randomized_holdout_publication_registry_lookup_index_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_JSON_FILENAME,
    build_randomized_holdout_publication_registry_lookup_index_review,
    locate_randomized_holdout_publication_registry_lookup_index,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_lookup_index_review_artifacts import (
    render_randomized_holdout_publication_registry_lookup_index_review_html,
    render_randomized_holdout_publication_registry_lookup_index_review_markdown,
    render_randomized_holdout_publication_registry_lookup_index_review_text,
    write_randomized_holdout_publication_registry_lookup_index_review_outputs,
)
from scripts.build_randomized_holdout_publication_registry_lookup_index_review import main as cli_main
from tests.test_randomized_holdout_publication_registry_lookup_index import ready_index_inputs


class RandomizedHoldoutPublicationRegistryLookupIndexReviewTests(unittest.TestCase):
    def test_lookup_index_review_accepts_ready_index_for_downstream_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_lookup_index_review(index, lookup_index_path=index_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_lookup_index_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_lookup_index_review_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_downstream_governance_lookup_only")
        self.assertTrue(report["summary"]["downstream_ready"])
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["allowed_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rejected_use"], "production_promotion")
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_publication_registry_downstream_guard")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_downstream_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_lookup_index_review_fails_when_lookup_key_namespace_is_wrong(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["lookup_index"]["lookup_keys"] = ["production:randomized-holdout-publication-v928"]
            report = build_randomized_holdout_publication_registry_lookup_index_review(index, lookup_index_path=index_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("lookup_keys_present", [issue["id"] for issue in report["issues"]])

    def test_lookup_index_review_fails_when_contract_check_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_registry_lookup_index_review(index, lookup_index_path=index_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("contract_check_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_review_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_lookup_index(index_path.parent), index_path)
            report = build_randomized_holdout_publication_registry_lookup_index_review(index, lookup_index_path=index_path)
            outputs = write_randomized_holdout_publication_registry_lookup_index_review_outputs(report, root / "review")
            cli_main(
                [
                    "--lookup-index",
                    str(index_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-downstream-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_REVIEW_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_lookup_index_review_ready=True", render_randomized_holdout_publication_registry_lookup_index_review_text(report))
        self.assertIn("approved_for_downstream_governance_lookup_only", render_randomized_holdout_publication_registry_lookup_index_review_markdown(report))
        self.assertIn("publication registry lookup index review", render_randomized_holdout_publication_registry_lookup_index_review_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    packet, check, packet_path, check_path = ready_index_inputs(root)
    index = build_randomized_holdout_publication_registry_lookup_index(packet, check, lookup_packet_path=packet_path, lookup_packet_check_path=check_path)
    index_outputs = write_randomized_holdout_publication_registry_lookup_index_outputs(index, root / "index")
    return index, Path(index_outputs["json"])


if __name__ == "__main__":
    unittest.main()
