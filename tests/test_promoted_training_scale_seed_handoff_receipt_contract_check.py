from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (  # noqa: E402
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_receipt_contract_summary,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text,
)
from test_promoted_training_scale_seed_handoff_receipt_suite_design import (  # noqa: E402
    write_suite_design_handoff_with_sidecars,
)


class PromotedTrainingScaleSeedHandoffReceiptContractCheckTests(unittest.TestCase):
    def test_contract_summary_check_rebuilds_expected_summary_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)
            text = render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text(check)
            markdown = render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown(check)
            html = render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html(check)

            self.assertEqual(check["status"], "pass")
            self.assertEqual(check["actual_summary_status"], "pass")
            self.assertEqual(check["expected_summary_status"], "pass")
            self.assertEqual(check["sidecar_status"], "pass")
            self.assertGreater(check["summary_field_check_count"], 0)
            self.assertEqual(check["failed_summary_field_check_count"], 0)
            self.assertEqual(check["contract_profile_status"], "pass")
            self.assertEqual(check["contract_profile_check_count"], 4)
            self.assertEqual(check["failed_contract_profile_check_count"], 0)
            self.assertEqual(check["failed_check_target_count"], 0)
            self.assertEqual(check["sidecar_check_count"], 3)
            self.assertEqual(check["failed_sidecar_check_count"], 0)
            family_by_name = {row["family"]: row for row in check["check_family_summary"]}
            self.assertEqual(family_by_name["summary_field"]["status"], "pass")
            self.assertEqual(family_by_name["summary_field"]["failed_count"], 0)
            self.assertEqual(family_by_name["contract_profile"]["status"], "pass")
            self.assertEqual(family_by_name["contract_profile"]["check_count"], 4)
            self.assertEqual(family_by_name["sidecar"]["status"], "pass")
            self.assertEqual(family_by_name["sidecar"]["check_count"], 3)
            contract_checks_row = next(row for row in check["summary_field_checks"] if row["key"] == "contract_checks")
            self.assertEqual(contract_checks_row["id"], "summary_field.contract_checks")
            self.assertEqual(contract_checks_row["check_type"], "summary_field")
            self.assertEqual(contract_checks_row["target"], "summary.contract_checks")
            self.assertEqual(contract_checks_row["status_domain"], ["pass", "fail"])
            self.assertTrue(contract_checks_row["required"])
            self.assertEqual(contract_checks_row["expected_kind"], "list")
            self.assertEqual(contract_checks_row["actual_kind"], "list")
            html_sidecar = next(row for row in check["sidecar_checks"] if row["id"] == "html")
            self.assertEqual(html_sidecar["check_type"], "sidecar_digest")
            self.assertEqual(html_sidecar["status_domain"], ["pass", "fail"])
            self.assertTrue(html_sidecar["required"])
            self.assertEqual(html_sidecar["expected_kind"], "sha256")
            self.assertEqual(html_sidecar["actual_kind"], "sha256")
            self.assertTrue(all(row["status"] == "pass" for row in check["sidecar_checks"]))
            self.assertTrue(
                any(row["key"] == "contract_check_type_summary" for row in check["summary_field_checks"])
            )
            type_profile_row = next(
                row for row in check["contract_profile_checks"] if row["key"] == "contract_check_type_summary"
            )
            self.assertEqual(type_profile_row["id"], "contract_profile.contract_check_type_summary")
            self.assertEqual(type_profile_row["check_type"], "contract_profile_consistency")
            self.assertEqual(type_profile_row["target"], "summary.contract_check_type_summary")
            self.assertEqual(type_profile_row["status"], "pass")
            self.assertEqual(type_profile_row["status_domain"], ["pass", "fail"])
            self.assertTrue(type_profile_row["required"])
            self.assertIn("receipt_contract_summary_check_status=pass", text)
            self.assertIn("receipt_contract_summary_check_failed_summary_field_check_count=0", text)
            self.assertIn("receipt_contract_summary_check_failed_contract_profile_check_count=0", text)
            self.assertIn("receipt_contract_summary_check_failed_check_target_count=0", text)
            self.assertIn("- Sidecar status: `pass`", markdown)
            self.assertIn("- Failed contract profile checks: `0`", markdown)
            self.assertIn("- Failed check targets: `0`", markdown)
            self.assertIn("## Check Family Summary", markdown)
            self.assertIn("| contract_profile | pass | 4 | 0 | 0 | [] |", markdown)
            self.assertIn("## Failed Check Targets", markdown)
            self.assertIn("| contract_checks | summary_field | summary.contract_checks | pass |", markdown)
            self.assertIn(
                "| contract_check_type_summary | contract_profile_consistency | "
                "summary.contract_check_type_summary | pass |",
                markdown,
            )
            self.assertIn("<strong>pass</strong>", html)
            self.assertIn("<td>summary_field</td>", html)
            self.assertIn("<td>contract_checks</td>", html)
            self.assertIn("<h2>Check Family Summary</h2>", html)
            self.assertIn("<h2>Failed Check Targets</h2>", html)
            self.assertIn("<h2>Contract Profile Checks</h2>", html)
            self.assertIn("<td>contract_profile_consistency</td>", html)

    def test_contract_summary_check_rejects_tampered_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            summary_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["receipt_schema_version"] = 2
            summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)

            self.assertEqual(check["status"], "fail")
            self.assertGreaterEqual(check["failed_summary_field_check_count"], 1)
            summary_family = next(row for row in check["check_family_summary"] if row["family"] == "summary_field")
            self.assertEqual(summary_family["status"], "fail")
            self.assertIn("summary.receipt_schema_version", summary_family["failed_targets"])
            self.assertTrue(
                any(
                    row["key"] == "receipt_schema_version"
                    and row["status"] == "fail"
                    and row["detail"] == "field differs from rebuilt summary"
                    for row in check["summary_field_checks"]
                )
            )
            self.assertTrue(
                any("summary.receipt_schema_version expected 4 but got 2" in issue for issue in check["issues"])
            )

    def test_contract_summary_check_rejects_tampered_boundary_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            summary_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["ci_boundary_plan_check_scopes"][1]["handoff_count"] = 9
            summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)

            self.assertEqual(check["status"], "fail")
            self.assertGreaterEqual(check["failed_summary_field_check_count"], 1)
            self.assertTrue(
                any("summary.ci_boundary_plan_check_scopes" in issue for issue in check["issues"])
            )

    def test_contract_summary_check_rejects_tampered_contract_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            summary_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["contract_checks"][0]["status"] = "fail"
            payload["failed_contract_check_count"] = 1
            summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)

            self.assertEqual(check["status"], "fail")
            self.assertGreaterEqual(check["failed_summary_field_check_count"], 1)
            self.assertTrue(any("summary.contract_checks" in issue for issue in check["issues"]))

    def test_contract_summary_check_rejects_tampered_contract_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            summary_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["contract_check_type_summary"][0]["failed_count"] = 7
            summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)

            self.assertEqual(check["status"], "fail")
            self.assertEqual(check["contract_profile_status"], "fail")
            self.assertGreaterEqual(check["failed_contract_profile_check_count"], 1)
            profile_family = next(row for row in check["check_family_summary"] if row["family"] == "contract_profile")
            self.assertEqual(profile_family["status"], "fail")
            self.assertIn("summary.contract_check_type_summary", profile_family["failed_targets"])
            self.assertTrue(
                any(
                    row["target"] == "summary.contract_check_type_summary"
                    and row["status"] == "fail"
                    and row["check_type"] == "contract_profile_consistency"
                    for row in check["contract_profile_checks"]
                )
            )
            self.assertTrue(
                any(
                    row["family"] == "contract_profile"
                    and row["target"] == "summary.contract_check_type_summary"
                    for row in check["failed_check_targets"]
                )
            )
            self.assertTrue(
                any("contract profile summary.contract_check_type_summary" in issue for issue in check["issues"])
            )

    def test_contract_summary_check_rejects_tampered_html_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            html_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.html"
            html_path.write_text(html_path.read_text(encoding="utf-8") + "\n<!-- stale -->\n", encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)

            self.assertEqual(check["status"], "fail")
            self.assertEqual(check["sidecar_status"], "fail")
            self.assertEqual(check["failed_summary_field_check_count"], 0)
            self.assertEqual(check["failed_sidecar_check_count"], 1)
            sidecar_family = next(row for row in check["check_family_summary"] if row["family"] == "sidecar")
            self.assertEqual(sidecar_family["status"], "fail")
            self.assertTrue(any(target.endswith("receipt_contract_summary.html") for target in sidecar_family["failed_targets"]))
            self.assertTrue(
                any(
                    row["id"] == "html"
                    and row["status"] == "fail"
                    and row["check_type"] == "sidecar_digest"
                    for row in check["sidecar_checks"]
                )
            )
            self.assertTrue(any("contract_summary.html content does not match" in issue for issue in check["issues"]))

    def test_cli_writes_contract_summary_check_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            check_dir = root / "contract-summary-check"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_receipt_contract_summary.py"),
                    str(summary_dir),
                    "--out-dir",
                    str(check_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            check = json.loads(
                (check_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary_check.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(check["status"], "pass")
            self.assertIn("receipt_contract_summary_check_status=pass", completed.stdout)
            self.assertIn("receipt_contract_summary_check_html=", completed.stdout)
            self.assertTrue(
                (check_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary_check.txt").is_file()
            )
            self.assertTrue(
                (check_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary_check.md").is_file()
            )
            self.assertTrue(
                (check_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary_check.html").is_file()
            )


def write_summary(handoff_dir: Path, root: Path) -> Path:
    summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(handoff_dir)
    summary_dir = root / "contract-summary"
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs(summary, summary_dir)
    return summary_dir


if __name__ == "__main__":
    unittest.main()
