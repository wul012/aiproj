from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_outputs
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_INDEX_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check import ready_check_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationIndexTests(unittest.TestCase):
    def test_publication_index_accepts_publication_and_contract_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path, check, check_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index(
                publication,
                check,
                publication_path=publication_path,
                publication_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_ready"])
        self.assertEqual(report["summary"]["publication_row_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["published_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_publication_index_fails_when_contract_check_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path, check, check_path = ready_index_inputs(Path(tmp))
            check["status"] = "fail"
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index(
                publication,
                check,
                publication_path=publication_path,
                publication_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("publication_check_passed", ids)
        self.assertIn("contract_check_ready", ids)

    def test_publication_index_fails_when_published_use_drifts_from_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path, check, check_path = ready_index_inputs(Path(tmp))
            publication["summary"]["published_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index(
                publication,
                check,
                publication_path=publication_path,
                publication_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("published_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_cli_require_index_ready_returns_one_on_tampered_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publication, publication_path, _check, check_path = ready_index_inputs(root)
            publication["summary"]["published_use"] = "production_promotion"
            write_json_payload(publication, publication_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main(
                    [
                        "--publication",
                        str(publication_path.parent),
                        "--publication-check",
                        str(check_path.parent),
                        "--out-dir",
                        str(root / "cli-index"),
                        "--require-index-ready",
                        "--force",
                    ]
                )

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-index" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_INDEX_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publication, publication_path, check, check_path = ready_index_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication(publication_path.parent), publication_path)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check(check_path.parent), check_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index(
                publication,
                check,
                publication_path=publication_path,
                publication_check_path=check_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_outputs(report, root / "index")
            cli_main(
                [
                    "--publication",
                    str(publication_path.parent),
                    "--publication-check",
                    str(check_path.parent),
                    "--out-dir",
                    str(root / "cli-index"),
                    "--require-index-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_INDEX_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_text(report))
        self.assertIn("Source Evidence", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_markdown(report))
        self.assertIn("publication index", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    publication, publication_path = ready_check_inputs(root)
    check = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check(
        publication,
        publication_path=publication_path,
    )
    check_outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_outputs(check, root / "publication-check")
    return publication, publication_path, check, Path(check_outputs["json"])


if __name__ == "__main__":
    unittest.main()
