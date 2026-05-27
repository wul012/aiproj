from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from scripts.check_ci_promoted_seed_receipt_contract_failure_smoke_plan import (  # noqa: E402
    CHECK_HTML_FILENAME,
    CHECK_JSON_FILENAME,
    CHECK_MARKDOWN_FILENAME,
    check_plan,
    load_plan,
    render_check_html,
    render_check_markdown,
    render_check_text,
    write_check_outputs,
)
from scripts.run_ci_promoted_seed_receipt_contract_failure_smoke import PLAN_JSON_FILENAME  # noqa: E402
from test_promoted_training_scale_seed_handoff_receipt_suite_design import (  # noqa: E402
    write_suite_design_handoff_with_sidecars,
)


class CiPromotedSeedReceiptContractFailureSmokePlanCheckTests(unittest.TestCase):
    def test_plan_check_passes_wrapper_output_and_writes_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = self._run_wrapper(root)
            plan_path = out_dir / PLAN_JSON_FILENAME
            plan = load_plan(plan_path)

            report = check_plan(plan, plan_path=plan_path)
            outputs = write_check_outputs(report, root / "plan-check")

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "continue")
            self.assertEqual(report["failed_count"], 0)
            self.assertEqual(report["artifact_failure_count"], 0)
            self.assertEqual(report["failure_smoke_summary"]["scenario_count"], 4)
            self.assertIn("status=pass", render_check_text(report))
            self.assertIn("contract_summary_json", render_check_markdown(report))
            self.assertIn("Source handoff", render_check_html(report))
            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertTrue((root / "plan-check" / CHECK_MARKDOWN_FILENAME).is_file())
            self.assertTrue((root / "plan-check" / CHECK_HTML_FILENAME).is_file())

            cli = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py"),
                    str(out_dir),
                    "--out-dir",
                    str(root / "plan-check-cli"),
                    "--require-pass",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("failed_count=0", cli.stdout)
            self.assertTrue((root / "plan-check-cli" / CHECK_JSON_FILENAME).is_file())

    def test_plan_check_detects_tampered_artifact_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = self._run_wrapper(root)
            plan_path = out_dir / PLAN_JSON_FILENAME
            plan = load_plan(plan_path)
            plan["artifact_digest"]["artifacts"]["failure_smoke_json"]["sha256"] = "0" * 64

            report = check_plan(plan, plan_path=plan_path)

            self.assertEqual(report["status"], "fail")
            self.assertGreater(report["failed_count"], 0)
            failed_ids = {item["id"] for item in report["checks"] if item["status"] == "fail"}
            self.assertIn("artifact:failure_smoke_json:sha256", failed_ids)

    def test_cli_returns_nonzero_for_failed_plan_unless_no_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = self._run_wrapper(root)
            plan_path = out_dir / PLAN_JSON_FILENAME
            plan = load_plan(plan_path)
            plan["commands"][1]["returncode"] = 7
            tampered = root / "tampered-plan.json"
            tampered.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

            failed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py"),
                    str(tampered),
                    "--out-dir",
                    str(root / "failed-check"),
                    "--require-pass",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            no_fail = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_ci_promoted_seed_receipt_contract_failure_smoke_plan.py"),
                    str(tampered),
                    "--out-dir",
                    str(root / "no-fail-check"),
                    "--no-fail",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(failed.returncode, 1)
            self.assertEqual(no_fail.returncode, 0)
            self.assertIn("status=fail", no_fail.stdout)

    def _run_wrapper(self, root: Path) -> Path:
        paths = write_suite_design_handoff_with_sidecars(root)
        out_dir = root / "ci-receipt-failure-smoke"
        subprocess.run(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "run_ci_promoted_seed_receipt_contract_failure_smoke.py"),
                "--source-handoff",
                str(paths["handoff"]),
                "--out-dir",
                str(out_dir),
                "--force",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return out_dir


if __name__ == "__main__":
    unittest.main()
