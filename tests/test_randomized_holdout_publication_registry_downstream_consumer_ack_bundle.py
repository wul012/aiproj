from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_check,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_outputs,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_check import build_randomized_holdout_publication_registry_downstream_consumer_ack_check
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_check_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_check_outputs
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack_check import ready_check_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundleTests(unittest.TestCase):
    def test_ack_bundle_accepts_ready_ack_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ack, ack_path, ack_check, ack_check_path = ready_bundle_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(
                ack,
                ack_check,
                consumer_ack_path=ack_path,
                consumer_ack_check_path=ack_check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready"])
        self.assertEqual(report["summary"]["bundle_status"], "ready_for_downstream_consumer_ack_review")
        self.assertEqual(report["summary"]["acked_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["evidence_count"], 2)
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle")
        self.assertEqual(resolve_exit_code(report, require_bundle_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_bundle_ready=True, require_promotion_ready=True), 1)

    def test_ack_bundle_fails_when_ack_check_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ack, ack_path, ack_check, ack_check_path = ready_bundle_inputs(Path(tmp))
            ack_check["status"] = "fail"
            ack_check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(
                ack,
                ack_check,
                consumer_ack_path=ack_path,
                consumer_ack_check_path=ack_check_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("consumer_ack_check_passed", ids)
        self.assertIn("contract_check_ready", ids)

    def test_ack_bundle_fails_when_ack_use_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ack, ack_path, ack_check, ack_check_path = ready_bundle_inputs(Path(tmp))
            ack["summary"]["acked_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(
                ack,
                ack_check,
                consumer_ack_path=ack_path,
                consumer_ack_check_path=ack_check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("acked_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ack, ack_path, ack_check, ack_check_path = ready_bundle_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack(ack_path.parent), ack_path)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_check(ack_check_path.parent), ack_check_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(
                ack,
                ack_check,
                consumer_ack_path=ack_path,
                consumer_ack_check_path=ack_check_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_outputs(report, root / "bundle")
            cli_main(
                [
                    "--consumer-ack",
                    str(ack_path.parent),
                    "--consumer-ack-check",
                    str(ack_check_path.parent),
                    "--out-dir",
                    str(root / "cli-bundle"),
                    "--require-bundle-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_text(report))
        self.assertIn("Evidence", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_markdown(report))
        self.assertIn("consumer ack bundle", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_html(report))


def ready_bundle_inputs(root: Path) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    ack, ack_path = ready_check_inputs(root)
    ack_check = build_randomized_holdout_publication_registry_downstream_consumer_ack_check(ack, consumer_ack_path=ack_path)
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_check_outputs(ack_check, root / "consumer-ack-check")
    return ack, ack_path, ack_check, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
