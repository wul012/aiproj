from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_acceptance_publication_packet import (
    RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_JSON_FILENAME,
    build_randomized_holdout_acceptance_publication_packet,
    locate_randomized_holdout_acceptance_summary,
    locate_randomized_holdout_acceptance_summary_check,
    resolve_exit_code,
)
from minigpt.randomized_holdout_acceptance_publication_packet_artifacts import (
    render_randomized_holdout_acceptance_publication_packet_html,
    render_randomized_holdout_acceptance_publication_packet_markdown,
    render_randomized_holdout_acceptance_publication_packet_text,
    write_randomized_holdout_acceptance_publication_packet_outputs,
)
from minigpt.randomized_holdout_acceptance_summary_check import build_randomized_holdout_acceptance_summary_check
from minigpt.randomized_holdout_acceptance_summary_check_artifacts import write_randomized_holdout_acceptance_summary_check_outputs
from scripts.build_randomized_holdout_acceptance_publication_packet import main as cli_main
from tests.test_randomized_holdout_acceptance_summary_check import ready_check_inputs


class RandomizedHoldoutAcceptancePublicationPacketTests(unittest.TestCase):
    def test_publication_packet_passes_with_verified_summary_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, check, summary_path, check_path = ready_publication_inputs(Path(tmp))
            report = build_randomized_holdout_acceptance_publication_packet(
                summary,
                check,
                acceptance_summary_path=summary_path,
                contract_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_acceptance_publication_packet_ready")
        self.assertTrue(report["summary"]["randomized_holdout_acceptance_publication_packet_ready"])
        self.assertEqual(report["summary"]["handoff_status"], "ready_for_bounded_acceptance_publication_review")
        self.assertEqual(report["summary"]["accepted_claim_count"], 1)
        self.assertEqual(report["summary"]["blocked_claim_count"], 3)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["allowed_use"], "bounded_model_capability_governance_only")
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_promotion_ready=True), 1)

    def test_publication_packet_fails_when_contract_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, check, summary_path, check_path = ready_publication_inputs(Path(tmp))
            check["status"] = "fail"
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_acceptance_publication_packet(
                summary,
                check,
                acceptance_summary_path=summary_path,
                contract_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("contract_check_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True), 1)

    def test_publication_packet_fails_when_allowed_use_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, check, summary_path, check_path = ready_publication_inputs(Path(tmp))
            summary["summary"]["allowed_use"] = "production_promotion"
            report = build_randomized_holdout_acceptance_publication_packet(
                summary,
                check,
                acceptance_summary_path=summary_path,
                contract_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("allowed_use_bounded", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary, check, summary_path, check_path = ready_publication_inputs(root)
            self.assertEqual(locate_randomized_holdout_acceptance_summary(summary_path.parent), summary_path)
            self.assertEqual(locate_randomized_holdout_acceptance_summary_check(check_path.parent), check_path)
            report = build_randomized_holdout_acceptance_publication_packet(
                summary,
                check,
                acceptance_summary_path=summary_path,
                contract_check_path=check_path,
            )
            outputs = write_randomized_holdout_acceptance_publication_packet_outputs(report, root / "packet")
            cli_main(
                [
                    "--acceptance-summary",
                    str(summary_path.parent),
                    "--contract-check",
                    str(check_path.parent),
                    "--out-dir",
                    str(root / "cli-packet"),
                    "--require-packet-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_ACCEPTANCE_PUBLICATION_PACKET_JSON_FILENAME))
        self.assertIn("randomized_holdout_acceptance_publication_packet_ready=True", render_randomized_holdout_acceptance_publication_packet_text(report))
        self.assertIn("Evidence", render_randomized_holdout_acceptance_publication_packet_markdown(report))
        self.assertIn("acceptance publication packet", render_randomized_holdout_acceptance_publication_packet_html(report))


def ready_publication_inputs(root: Path) -> tuple[dict[str, object], dict[str, object], Path, Path]:
    summary, summary_path = ready_check_inputs(root / "check-source")
    check = build_randomized_holdout_acceptance_summary_check(summary, acceptance_summary_path=summary_path)
    check_outputs = write_randomized_holdout_acceptance_summary_check_outputs(check, root / "check")
    return summary, check, summary_path, Path(check_outputs["json"])


if __name__ == "__main__":
    unittest.main()
