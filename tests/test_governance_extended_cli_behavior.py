from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from scripts import (
    build_maturity_narrative,
    build_maturity_summary,
    check_release_readiness_drift_contract,
    compare_release_gate_profiles,
    compare_release_readiness,
)
from tests.test_maturity import make_project as make_maturity_project
from tests.test_maturity import make_request_history_summary
from tests.test_maturity_narrative import make_project as make_maturity_narrative_project
from tests.test_release_gate_comparison import make_bundle as make_gate_comparison_bundle
from tests.test_release_readiness_comparison import make_readiness


class GovernanceExtendedCliBehaviorTests(unittest.TestCase):
    def test_maturity_summary_and_narrative_mains_write_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_project = root / "summary-project"
            summary_project.mkdir()
            make_maturity_project(summary_project, version_count=65)
            request_history = make_request_history_summary(summary_project)
            summary_out = root / "maturity-summary"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                summary_exit_code = build_maturity_summary.main(
                    [
                        "--project-root",
                        str(summary_project),
                        "--request-history-summary",
                        str(request_history),
                        "--out-dir",
                        str(summary_out),
                    ]
                )

            summary_output = stdout.getvalue()
            self.assertEqual(summary_exit_code, 0)
            self.assertIn("current_version=65", summary_output)
            self.assertIn("overall_status=pass", summary_output)
            self.assertIn("release_readiness_trend_status=improved", summary_output)
            self.assertIn("outputs=", summary_output)
            summary = json.loads((summary_out / "maturity_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["summary"]["current_version"], 65)
            self.assertTrue((summary_out / "maturity_summary.md").is_file())
            self.assertTrue((summary_out / "maturity_summary.html").is_file())
            self.assertTrue((summary_out / "maturity_summary.csv").is_file())

            narrative_paths = make_maturity_narrative_project(root / "narrative-fixture")
            narrative_out = root / "maturity-narrative"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                narrative_exit_code = build_maturity_narrative.main(
                    [
                        "--project-root",
                        str(narrative_paths["project"]),
                        "--out-dir",
                        str(narrative_out),
                    ]
                )

            narrative_output = stdout.getvalue()
            self.assertEqual(narrative_exit_code, 0)
            self.assertIn("portfolio_status=ready", narrative_output)
            self.assertIn("benchmark_history_suite_design_non_comparison_ready_entries=0", narrative_output)
            self.assertIn("release_readiness_benchmark_suite_design_regression_count=0", narrative_output)
            self.assertIn("outputs=", narrative_output)
            narrative = json.loads((narrative_out / "maturity_narrative.json").read_text(encoding="utf-8"))
            self.assertEqual(narrative["summary"]["portfolio_status"], "ready")
            self.assertTrue((narrative_out / "maturity_narrative.md").is_file())
            self.assertTrue((narrative_out / "maturity_narrative.html").is_file())

    def test_release_readiness_comparison_and_drift_contract_mains_write_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="ready", decision="ship", gate_status="pass")
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_suite_design_non_comparison_ready_entries=4,
                benchmark_history_design_comparison_changed_entries=5,
                warn_panels=1,
            )
            comparison_out = root / "release-readiness-comparison"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                comparison_exit_code = compare_release_readiness.main(
                    [
                        "--readiness",
                        str(baseline),
                        "--readiness",
                        str(current),
                        "--out-dir",
                        str(comparison_out),
                    ]
                )

            comparison_output = stdout.getvalue()
            comparison_path = comparison_out / "release_readiness_comparison.json"
            self.assertEqual(comparison_exit_code, 0)
            self.assertIn("readiness=2", comparison_output)
            self.assertIn("regressed=1", comparison_output)
            self.assertIn("benchmark_history_suite_design_non_comparison_ready_regression_count=1", comparison_output)
            self.assertIn("benchmark_history_suite_design=current:4:5", comparison_output)
            self.assertIn("outputs=", comparison_output)
            comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
            self.assertEqual(comparison["summary"]["regressed_count"], 1)
            self.assertTrue((comparison_out / "release_readiness_comparison.md").is_file())
            self.assertTrue((comparison_out / "release_readiness_comparison.html").is_file())
            self.assertTrue((comparison_out / "release_readiness_deltas.csv").is_file())

            drift_out = root / "release-readiness-drift-contract"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                drift_exit_code = check_release_readiness_drift_contract.main(
                    [str(comparison_out), "--out-dir", str(drift_out)]
                )

            drift_output = stdout.getvalue()
            self.assertEqual(drift_exit_code, 0)
            self.assertIn("status=pass", drift_output)
            self.assertIn("decision=continue", drift_output)
            self.assertIn("delta_pass_count=1", drift_output)
            self.assertIn("outputs=", drift_output)
            drift = json.loads((drift_out / "release_readiness_drift_contract_check.json").read_text(encoding="utf-8"))
            self.assertEqual(drift["status"], "pass")
            self.assertTrue((drift_out / "release_readiness_drift_contract_check.txt").is_file())

    def test_release_gate_profile_comparison_main_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_gate_comparison_bundle(root, audit_score=92.0)
            out_dir = root / "release-gate-profiles"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = compare_release_gate_profiles.main(
                    [
                        "--bundle",
                        str(bundle_path),
                        "--out-dir",
                        str(out_dir),
                        "--profiles",
                        "standard",
                        "strict",
                    ]
                )

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("bundles=1", output)
            self.assertIn("profiles=standard,strict", output)
            self.assertIn("blocked=1", output)
            self.assertIn("decision_deltas=1", output)
            self.assertIn("outputs=", output)
            report = json.loads((out_dir / "release_gate_profile_comparison.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["row_count"], 2)
            self.assertEqual(report["summary"]["blocked_count"], 1)
            self.assertTrue((out_dir / "release_gate_profile_comparison.md").is_file())
            self.assertTrue((out_dir / "release_gate_profile_comparison.html").is_file())
            self.assertTrue((out_dir / "release_gate_profile_deltas.csv").is_file())


if __name__ == "__main__":
    unittest.main()
