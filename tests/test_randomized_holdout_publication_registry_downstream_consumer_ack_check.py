from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack import build_randomized_holdout_publication_registry_downstream_consumer_ack
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_outputs
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CHECK_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_check,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_check_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_check_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_check_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_check_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_check_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_publication_registry_downstream_consumer_ack import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack import ready_ack_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_consumer_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ack, ack_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_check(
                ack,
                consumer_ack_path=ack_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_ack_status"], "downstream_consumer_acknowledged")
        self.assertEqual(report["summary"]["rebuilt_ack_status"], "downstream_consumer_acknowledged")
        self.assertEqual(report["summary"]["original_acked_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_acked_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["original_promotion_ready"], False)
        self.assertEqual(report["summary"]["rebuilt_promotion_ready"], False)
        self.assertEqual(report["summary"]["next_step"], "bundle_randomized_holdout_publication_registry_downstream_consumer_ack")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_ack_use_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ack, ack_path = ready_check_inputs(Path(tmp))
            ack["summary"]["acked_use"] = "production_promotion"
            ack["ack"]["acked_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_check(
                ack,
                consumer_ack_path=ack_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("summary.acked_use", ids)
        self.assertIn("ack.acked_use", ids)

    def test_contract_check_fails_when_source_review_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ack, ack_path = ready_check_inputs(Path(tmp))
            ack["consumer_index_review_path"] = "missing-review.json"
            ack["ack"]["consumer_index_review_path"] = "missing-review.json"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_check(
                ack,
                consumer_ack_path=ack_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_consumer_index_review_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ack, ack_path = ready_check_inputs(root)
            ack["summary"]["acked_use"] = "production_promotion"
            write_json_payload(ack, ack_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(ack_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CHECK_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ack, ack_path = ready_check_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack(ack_path.parent), ack_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_check(
                ack,
                consumer_ack_path=ack_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_check_outputs(report, root / "check")
            cli_main([str(ack_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_CHECK_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_check_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_registry_downstream_consumer_ack_check_markdown(report))
        self.assertIn("consumer ack contract check", render_randomized_holdout_publication_registry_downstream_consumer_ack_check_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_ack_inputs(root)
    ack = build_randomized_holdout_publication_registry_downstream_consumer_ack(review, consumer_index_review_path=review_path)
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_outputs(ack, root / "consumer-ack")
    return ack, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
