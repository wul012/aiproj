from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maintenance_policy import (  # noqa: E402
    DEFAULT_MODULE_CRITICAL_LINES,
    DEFAULT_MODULE_TOP_N,
    DEFAULT_MODULE_WARNING_LINES,
    build_governance_stabilization_review,
    build_maintenance_batching_report,
    build_module_pressure_report,
    build_maintenance_proposal_decision,
    render_governance_stabilization_html,
    render_governance_stabilization_markdown,
    render_module_pressure_html,
    render_module_pressure_markdown,
    render_maintenance_batching_html,
    render_maintenance_batching_markdown,
    write_governance_stabilization_outputs,
    write_maintenance_batching_outputs,
    write_module_pressure_outputs,
)
from minigpt import maintenance_policy, maintenance_pressure  # noqa: E402


class MaintenancePolicyTests(unittest.TestCase):
    def test_report_warns_on_long_single_module_utils_run(self) -> None:
        history = [
            {"version": "v84", "title": "report-utils migration", "category": "report-utils", "modules": ["a.py"]},
            {"version": "v85", "title": "report-utils migration", "category": "report-utils", "modules": ["b.py"]},
            {"version": "v86", "title": "report-utils migration", "category": "report-utils", "modules": ["c.py"]},
            {"version": "v87", "title": "report-utils migration", "category": "report-utils", "modules": ["d.py"]},
        ]

        report = build_maintenance_batching_report(history, single_module_limit=3, generated_at="2026-05-15T00:00:00Z")

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertEqual(report["summary"]["longest_single_module_utils_run"], 4)
        self.assertEqual(report["single_module_utils_runs"][0]["start_version"], "v84")
        self.assertIn("Batch the next related", " ".join(report["recommendations"]))

    def test_batched_utils_release_breaks_the_warning_run(self) -> None:
        history = [
            {"version": "v105", "title": "report-utils migration", "category": "report-utils", "modules": ["a.py"]},
            {
                "version": "v108",
                "title": "batched release governance report utility migration",
                "category": "report-utils",
                "modules": ["release_gate.py", "release_gate_comparison.py", "request_history_summary.py"],
            },
            {"version": "v109", "title": "maintenance batching policy", "category": "feature", "modules": ["maintenance_policy.py"]},
        ]

        report = build_maintenance_batching_report(history, single_module_limit=3)

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["batched_utils_count"], 1)
        self.assertEqual(report["summary"]["longest_single_module_utils_run"], 1)

    def test_proposal_batches_related_low_risk_items(self) -> None:
        decision = build_maintenance_proposal_decision(
            [
                {"name": "registry helpers", "category": "report-utils"},
                {"name": "benchmark helpers", "category": "report-utils"},
                {"name": "audit helpers", "category": "report-utils"},
            ]
        )

        self.assertEqual(decision["decision"], "batch")
        self.assertEqual(decision["target_version_kind"], "batched")
        self.assertEqual(decision["groups"][0]["count"], 3)

    def test_proposal_splits_high_risk_items(self) -> None:
        decision = build_maintenance_proposal_decision(
            [
                {"name": "server endpoint", "category": "report-utils", "risk_flags": ["service_change"]},
                {"name": "registry helper", "category": "report-utils"},
            ]
        )

        self.assertEqual(decision["decision"], "split")
        self.assertEqual(decision["split_count"], 1)
        self.assertIn("service/API", decision["items"][0]["split_reasons"][0])

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_maintenance_batching_report(
                [{"version": "<v1>", "title": "<report-utils>", "category": "report-utils", "modules": ["a.py"]}],
                proposal_items=[{"name": "<helper>", "category": "report-utils"}],
                title="<Maintenance>",
            )

            outputs = write_maintenance_batching_outputs(report, root)
            html = render_maintenance_batching_html(report)
            markdown = render_maintenance_batching_markdown(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("&lt;Maintenance&gt;", html)
            self.assertNotIn("<h1><Maintenance>", html)
            self.assertIn("<Maintenance>", markdown)
            payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["proposal"]["decision"], "single_ok")

    def test_governance_stabilization_review_pauses_new_chains(self) -> None:
        report = build_governance_stabilization_review(generated_at="2026-05-21T00:00:00Z")

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["decision"], "pause_new_governance_chains")
        self.assertEqual(report["summary"]["chain_count"], 7)
        self.assertEqual(report["summary"]["keep_count"], 5)
        self.assertEqual(report["summary"]["watch_count"], 2)
        self.assertEqual(report["summary"]["missing_review_reason_count"], 0)
        self.assertEqual(report["summary"]["missing_expansion_rule_count"], 0)
        self.assertEqual(report["policy"]["new_chain_pause"], "active")
        self.assertIn("review_reason", report["chains"][0])
        self.assertIn("expansion_rule", report["chains"][0])
        self.assertIn("Treat seven active chains", " ".join(report["recommendations"]))

    def test_governance_stabilization_flags_consolidation_candidates(self) -> None:
        report = build_governance_stabilization_review(
            [
                {
                    "id": "release",
                    "name": "Release readiness",
                    "action": "keep",
                    "consumer": "review",
                    "evidence": "bundle",
                    "review_reason": "release decision",
                    "expansion_rule": "merge release checks here",
                },
                {
                    "id": "links",
                    "name": "Extra link dashboard",
                    "action": "merge",
                    "consumer": "registry",
                    "evidence": "links",
                    "review_reason": "duplicate index",
                    "expansion_rule": "fold into registry",
                },
                {
                    "id": "stale",
                    "name": "Stale trend projection",
                    "action": "cut",
                    "consumer": "none",
                    "evidence": "duplicate trend",
                    "review_reason": "no longer distinct",
                    "expansion_rule": "do not expand",
                },
            ],
            pause_days=2,
        )

        self.assertEqual(report["summary"]["status"], "review")
        self.assertEqual(report["summary"]["decision"], "pause_and_consolidate_governance_chains")
        self.assertEqual(report["summary"]["merge_count"], 1)
        self.assertEqual(report["summary"]["cut_count"], 1)
        self.assertEqual(report["summary"]["consolidation_candidate_count"], 2)
        self.assertIn("Consolidate chains marked merge/cut", " ".join(report["recommendations"]))

    def test_governance_stabilization_requires_reasons_and_expansion_rules(self) -> None:
        report = build_governance_stabilization_review(
            [{"id": "thin", "name": "Thin chain", "action": "keep", "consumer": "reader", "evidence": "artifact"}]
        )

        self.assertEqual(report["summary"]["status"], "review")
        self.assertEqual(report["summary"]["decision"], "pause_and_review_governance_chains")
        self.assertEqual(report["summary"]["missing_review_reason_count"], 1)
        self.assertEqual(report["summary"]["missing_expansion_rule_count"], 1)
        self.assertIn("Add review reasons and expansion rules", " ".join(report["recommendations"]))

    def test_governance_stabilization_outputs_and_script_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_governance_stabilization_review(title="<Governance>")

            outputs = write_governance_stabilization_outputs(report, root / "review")
            html = render_governance_stabilization_html(report)
            markdown = render_governance_stabilization_markdown(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("&lt;Governance&gt;", html)
            self.assertIn("Dataset provenance", markdown)
            self.assertIn("Expansion rule", markdown)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_maintenance_batching.py"),
                    "--skip-module-pressure",
                    "--out-dir",
                    str(root / "script"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("governance_status=pass", completed.stdout)
            self.assertIn("governance_decision=pause_new_governance_chains", completed.stdout)
            self.assertIn("governance_chain_count=7", completed.stdout)
            self.assertIn("governance_missing_review_reason_count=0", completed.stdout)
            self.assertIn("governance_missing_expansion_rule_count=0", completed.stdout)

    def test_module_pressure_report_flags_large_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            large = root / "large_module.py"
            small = root / "small_module.py"
            large.write_text(
                "\n".join(
                    [
                        "class Service:",
                        "    def handle(self):",
                        *["        value = 1" for _ in range(15)],
                        "        return value",
                    ]
                ),
                encoding="utf-8",
            )
            small.write_text("def ok():\n    return 1\n", encoding="utf-8")

            report = build_module_pressure_report(
                [large, small],
                project_root=root,
                warning_lines=8,
                critical_lines=18,
                generated_at="2026-05-15T00:00:00Z",
            )

            self.assertEqual(report["summary"]["status"], "warn")
            self.assertEqual(report["summary"]["critical_count"], 1)
            self.assertEqual(report["summary"]["largest_module"], "large_module.py")
            self.assertEqual(report["top_modules"][0]["largest_function"], "handle")
            self.assertEqual(report["summary"]["decision"], "plan_targeted_split")
            self.assertIn("split", " ".join(report["recommendations"]))

    def test_module_pressure_builder_is_split_but_legacy_export_stays(self) -> None:
        self.assertIs(build_module_pressure_report, maintenance_pressure.build_module_pressure_report)
        self.assertIs(maintenance_policy.build_module_pressure_report, maintenance_pressure.build_module_pressure_report)
        self.assertEqual(DEFAULT_MODULE_WARNING_LINES, maintenance_pressure.DEFAULT_MODULE_WARNING_LINES)
        self.assertEqual(DEFAULT_MODULE_CRITICAL_LINES, maintenance_pressure.DEFAULT_MODULE_CRITICAL_LINES)
        self.assertEqual(DEFAULT_MODULE_TOP_N, maintenance_pressure.DEFAULT_MODULE_TOP_N)

    def test_module_pressure_report_handles_syntax_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken = root / "broken.py"
            broken.write_text("def broken(:\n    pass\n", encoding="utf-8")

            report = build_module_pressure_report([broken], project_root=root, warning_lines=10, critical_lines=20)

            self.assertEqual(report["modules"][0]["path"], "broken.py")
            self.assertEqual(report["modules"][0]["parse_error"], "syntax-error:1")
            self.assertEqual(report["modules"][0]["status"], "pass")

    def test_module_pressure_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module = root / "module.py"
            module.write_text("def risky_name():\n    return '<x>'\n", encoding="utf-8")
            report = build_module_pressure_report([module], project_root=root, title="<Pressure>")

            outputs = write_module_pressure_outputs(report, root / "out")
            html = render_module_pressure_html(report)
            markdown = render_module_pressure_markdown(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("&lt;Pressure&gt;", html)
            self.assertIn("<Pressure>", markdown)
            self.assertIn("module.py", Path(outputs["csv"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
