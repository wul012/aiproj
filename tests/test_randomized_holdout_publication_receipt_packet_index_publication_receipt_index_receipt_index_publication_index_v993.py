from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992_outputs
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_V993_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993,
    locate_publication_check_v993,
    locate_publication_v993,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_artifacts import (
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_html,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_markdown,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993 import main as cli_main
from tests.test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992 import ready_check_inputs


class RandomizedHoldoutPublicationReceiptPacketIndexPublicationReceiptIndexReceiptIndexPublicationIndexV993Tests(unittest.TestCase):
    def test_publication_index_accepts_publication_and_contract_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path, check, check_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993(
                publication,
                check,
                publication_path=publication_path,
                publication_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_ready"])
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertEqual(report["summary"]["published_use"], "downstream_governance_lookup_only")
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_publication_index_fails_when_published_use_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path, check, check_path = ready_index_inputs(Path(tmp))
            publication["summary"]["published_use"] = "production_promotion"
            publication["publication"]["published_use"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993(
                publication,
                check,
                publication_path=publication_path,
                publication_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("published_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_publication_index_fails_when_contract_check_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path, check, check_path = ready_index_inputs(Path(tmp))
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993(
                publication,
                check,
                publication_path=publication_path,
                publication_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("contract_check_ready", [issue["id"] for issue in report["issues"]])

    def test_cli_require_index_ready_returns_one_on_tampered_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publication, publication_path, _check, check_path = ready_index_inputs(root)
            publication["summary"]["published_use"] = "production_promotion"
            write_json_payload(publication, publication_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main(["--publication", str(publication_path.parent), "--publication-check", str(check_path.parent), "--out-dir", str(root / "cli-index"), "--require-index-ready", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-index" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_V993_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publication, publication_path, check, check_path = ready_index_inputs(root)
            self.assertEqual(locate_publication_v993(publication_path.parent), publication_path)
            self.assertEqual(locate_publication_check_v993(check_path.parent), check_path)
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993(
                publication,
                check,
                publication_path=publication_path,
                publication_check_path=check_path,
            )
            outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_outputs(report, root / "index")
            cli_main(["--publication", str(publication_path.parent), "--publication-check", str(check_path.parent), "--out-dir", str(root / "cli-index"), "--require-index-ready", "--require-lookup-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_V993_JSON_FILENAME))
        self.assertIn("index_ready=True", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_text(report))
        self.assertIn("Source Evidence", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_markdown(report))
        self.assertIn("publication index", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    publication, publication_path = ready_check_inputs(root)
    check = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992(
        publication,
        publication_path=publication_path,
    )
    check_outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992_outputs(check, root / "publication-check")
    return publication, publication_path, check, Path(check_outputs["json"])


if __name__ == "__main__":
    unittest.main()
