from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from scripts import build_release_bundle, build_release_readiness, check_release_gate, register_runs
from tests.test_registry import make_run as make_registry_run
from tests.test_release_bundle import make_release_inputs


class GovernanceCliBehaviorTests(unittest.TestCase):
    def test_register_runs_main_writes_registry_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_registry_run(
                root,
                "one",
                1.0,
                readiness_trend="panel-changed",
                readiness_suite_design_regression=True,
            )
            out_dir = root / "registry"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = register_runs.main([str(run_dir), "--out-dir", str(out_dir)])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("run_count=1", output)
            self.assertIn("release_readiness_benchmark_suite_design_delta_count=1", output)
            self.assertIn("release_readiness_benchmark_suite_design_regression_count=1", output)
            self.assertIn("outputs=", output)
            registry = json.loads((out_dir / "registry.json").read_text(encoding="utf-8"))
            self.assertEqual(registry["run_count"], 1)
            self.assertEqual(registry["runs"][0]["name"], "one")
            self.assertTrue((out_dir / "registry.csv").is_file())
            self.assertTrue((out_dir / "registry.html").is_file())
            self.assertTrue((out_dir / "registry.svg").is_file())

    def test_release_governance_main_chain_writes_evidence_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (
                registry_path,
                model_path,
                audit_path,
                request_summary_path,
                benchmark_history_path,
                ci_workflow_hygiene_path,
                test_coverage_report_path,
            ) = make_release_inputs(root)
            (registry_path.parent / "registry.svg").write_text("<svg></svg>", encoding="utf-8")

            bundle_dir = root / "release-bundle"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                bundle_exit_code = build_release_bundle.main(
                    [
                        "--registry",
                        str(registry_path),
                        "--model-card",
                        str(model_path),
                        "--audit",
                        str(audit_path),
                        "--request-history-summary",
                        str(request_summary_path),
                        "--benchmark-history",
                        str(benchmark_history_path),
                        "--ci-workflow-hygiene",
                        str(ci_workflow_hygiene_path),
                        "--test-coverage-report",
                        str(test_coverage_report_path),
                        "--out-dir",
                        str(bundle_dir),
                        "--release-name",
                        "v-cli-demo",
                    ]
                )

            bundle_output = stdout.getvalue()
            bundle_path = bundle_dir / "release_bundle.json"
            self.assertEqual(bundle_exit_code, 0)
            self.assertIn("release_status=release-ready", bundle_output)
            self.assertIn("benchmark_history_status=pass", bundle_output)
            self.assertIn("ci_workflow_archived_path_portability_check_ready=True", bundle_output)
            self.assertIn("outputs=", bundle_output)
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(bundle["release_name"], "v-cli-demo")
            self.assertEqual(bundle["summary"]["missing_artifacts"], 0)
            self.assertTrue((bundle_dir / "release_bundle.md").is_file())
            self.assertTrue((bundle_dir / "release_bundle.html").is_file())

            gate_dir = root / "release-gate"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                gate_exit_code = check_release_gate.main(
                    [
                        "--bundle",
                        str(bundle_path),
                        "--out-dir",
                        str(gate_dir),
                        "--allow-missing-generation-quality",
                    ]
                )

            gate_output = stdout.getvalue()
            gate_path = gate_dir / "gate_report.json"
            self.assertEqual(gate_exit_code, 0)
            self.assertIn("gate_status=pass", gate_output)
            self.assertIn("decision=approved", gate_output)
            self.assertIn("require_generation_quality=False", gate_output)
            self.assertIn("outputs=", gate_output)
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            self.assertEqual(gate["summary"]["gate_status"], "pass")
            self.assertTrue((gate_dir / "gate_report.md").is_file())
            self.assertTrue((gate_dir / "gate_report.html").is_file())

            readiness_dir = root / "release-readiness"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                readiness_exit_code = build_release_readiness.main(
                    [
                        "--bundle",
                        str(bundle_path),
                        "--gate",
                        str(gate_path),
                        "--out-dir",
                        str(readiness_dir),
                    ]
                )

            readiness_output = stdout.getvalue()
            readiness_path = readiness_dir / "release_readiness.json"
            self.assertEqual(readiness_exit_code, 0)
            self.assertIn("readiness_status=review", readiness_output)
            self.assertIn("gate_status=pass", readiness_output)
            self.assertIn("benchmark_history_status=pass", readiness_output)
            self.assertIn("outputs=", readiness_output)
            readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
            self.assertEqual(readiness["summary"]["gate_status"], "pass")
            self.assertTrue((readiness_dir / "release_readiness.md").is_file())
            self.assertTrue((readiness_dir / "release_readiness.html").is_file())


if __name__ == "__main__":
    unittest.main()
