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
        self.assertEqual(report["proposal_routing"]["decision"], "not_applicable")
        self.assertEqual(report["proposal_routing"]["item_count"], 0)

    def test_governance_stabilization_routes_proposals_into_existing_chains(self) -> None:
        report = build_governance_stabilization_review(
            proposed_items=[
                {"title": "Dataset drift note", "description": "dataset source dedupe and corpus change"},
                {"title": "Promotion receipt field cleanup", "description": "promoted seed handoff receipt helpers", "target_chain": "training-promotion"},
            ]
        )

        routing = report["proposal_routing"]
        self.assertEqual(routing["decision"], "merge_existing")
        self.assertEqual(routing["merge_existing_count"], 2)
        self.assertEqual(routing["review_count"], 0)
        self.assertEqual(routing["new_chain_candidate_count"], 0)
        self.assertEqual(routing["exact_match_count"], 1)
        self.assertEqual(routing["keyword_match_count"], 1)
        self.assertEqual(routing["items"][0]["suggested_chain"], "dataset-provenance")
        self.assertEqual(routing["items"][1]["suggested_chain"], "training-promotion")
        self.assertEqual(routing["items"][0]["match_basis"], "keyword")
        self.assertEqual(routing["items"][0]["matched_keyword"], "dataset")
        self.assertEqual(routing["items"][1]["match_basis"], "exact")
        self.assertEqual(routing["items"][1]["matched_keyword"], "")
        self.assertIn("Route current proposals", " ".join(report["recommendations"]))

    def test_governance_stabilization_reviews_high_risk_proposals(self) -> None:
        report = build_governance_stabilization_review(
            proposed_items=[
                {"title": "Release gate schema change", "description": "release gate output schema", "target_chain": "release-readiness", "risk_flags": ["schema_change"]},
            ]
        )

        routing = report["proposal_routing"]
        self.assertEqual(routing["decision"], "review_before_merge")
        self.assertEqual(routing["review_count"], 1)
        self.assertEqual(routing["items"][0]["route_decision"], "review")
        self.assertEqual(routing["items"][0]["match_basis"], "exact")
        self.assertIn("high-risk governance proposals", " ".join(report["recommendations"]))

    def test_governance_stabilization_reviews_ambiguous_keyword_matches(self) -> None:
        report = build_governance_stabilization_review(
            proposed_items=[
                {"title": "Dataset benchmark bridge", "description": "dataset snapshot should be reviewed beside benchmark history"},
            ]
        )
        html = render_governance_stabilization_html(report)
        markdown = render_governance_stabilization_markdown(report)

        routing = report["proposal_routing"]
        item = routing["items"][0]
        self.assertEqual(routing["decision"], "review_before_merge")
        self.assertEqual(routing["review_count"], 1)
        self.assertEqual(routing["merge_existing_count"], 0)
        self.assertEqual(routing["keyword_match_count"], 0)
        self.assertEqual(routing["ambiguous_keyword_match_count"], 1)
        self.assertEqual(routing["ambiguous_keyword_hits"], ["dataset", "data", "benchmark"])
        self.assertEqual(item["route_decision"], "review")
        self.assertEqual(item["match_basis"], "ambiguous_keyword")
        self.assertEqual(item["matched_keyword"], "dataset")
        self.assertEqual(item["matched_chains"], ["dataset-provenance", "benchmark-history"])
        self.assertIn("dataset", item["matched_keywords"])
        self.assertIn("benchmark", item["matched_keywords"])
        self.assertIn("multiple governance chains", item["reason"])
        self.assertIn("Ambiguous keyword matches", markdown)
        self.assertIn("Matched chains", markdown)
        self.assertIn("ambiguous-hits=dataset, data, benchmark", html)
        self.assertIn("ambiguous_keyword", html)

    def test_governance_stabilization_rejects_unmatched_proposals_during_pause(self) -> None:
        report = build_governance_stabilization_review(
            proposed_items=[
                {"title": "Unknown expansion surface", "description": "new chain candidate with no match"},
            ]
        )

        routing = report["proposal_routing"]
        self.assertEqual(routing["decision"], "reject_new_chain_during_pause")
        self.assertEqual(routing["new_chain_candidate_count"], 1)
        self.assertEqual(routing["items"][0]["route_decision"], "new_chain_candidate")
        self.assertIn("Reject unmatched governance-chain proposals", " ".join(report["recommendations"]))

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
            proposals_path = root / "proposals.json"
            proposals_path.write_text(
                json.dumps(
                    [
                        {"title": "Dataset drift note", "description": "dataset source dedupe and corpus change"},
                        {"title": "Promotion receipt field cleanup", "description": "promoted seed handoff receipt helpers", "target_chain": "training-promotion"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = build_governance_stabilization_review(
                title="<Governance>",
                proposed_items=json.loads(proposals_path.read_text(encoding="utf-8")),
            )

            outputs = write_governance_stabilization_outputs(report, root / "review")
            html = render_governance_stabilization_html(report)
            markdown = render_governance_stabilization_markdown(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("&lt;Governance&gt;", html)
            self.assertIn("Dataset provenance", markdown)
            self.assertIn("Proposal Routing", markdown)
            self.assertIn("Expansion rule", markdown)
            self.assertIn("Target chain", markdown)
            self.assertIn("Match basis", markdown)
            self.assertIn("training-promotion", markdown)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_maintenance_batching.py"),
                    "--skip-module-pressure",
                    "--governance-proposals",
                    str(proposals_path),
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
            self.assertIn("governance_routing_decision=merge_existing", completed.stdout)
            self.assertIn("governance_routing_item_count=2", completed.stdout)
            self.assertIn("governance_routing_merge_existing_count=2", completed.stdout)
            self.assertIn("governance_routing_review_count=0", completed.stdout)
            self.assertIn("governance_routing_new_chain_candidate_count=0", completed.stdout)
            self.assertIn("governance_routing_exact_match_count=1", completed.stdout)
            self.assertIn("governance_routing_keyword_match_count=1", completed.stdout)
            self.assertIn("governance_routing_ambiguous_keyword_match_count=0", completed.stdout)
            self.assertIn("governance_routing_keyword_hits=dataset", completed.stdout)
            self.assertIn("governance_routing_ambiguous_keyword_hits=", completed.stdout)
            self.assertIn("governance_routing_requirement_status=not-required", completed.stdout)
            self.assertIn("governance_routing_requirement_exit_code=0", completed.stdout)

    def test_script_can_require_clean_governance_routing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proposals_path = root / "proposals.json"
            proposals_path.write_text(
                json.dumps(
                    [
                        {"title": "Dataset drift note", "description": "dataset source dedupe and corpus change"},
                        {"title": "Registry model card polish", "description": "registry model card summary"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_maintenance_batching.py"),
                    "--skip-module-pressure",
                    "--governance-proposals",
                    str(proposals_path),
                    "--require-clean-governance-routing",
                    "--out-dir",
                    str(root / "script-clean"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("governance_routing_decision=merge_existing", completed.stdout)
            self.assertIn("governance_routing_requirement_status=pass", completed.stdout)
            self.assertIn("governance_routing_requirement_decision=continue", completed.stdout)
            self.assertIn("governance_routing_requirement_exit_code=0", completed.stdout)
            self.assertIn("governance_routing_requirement_blocking_count=0", completed.stdout)
            payload = json.loads((root / "script-clean" / "governance_stabilization.json").read_text(encoding="utf-8"))
            markdown = (root / "script-clean" / "governance_stabilization.md").read_text(encoding="utf-8")
            html = (root / "script-clean" / "governance_stabilization.html").read_text(encoding="utf-8")
            self.assertEqual(payload["routing_requirement"]["status"], "pass")
            self.assertIn("Requirement status: `pass`", markdown)
            self.assertIn("Routing Requirement", html)

    def test_script_required_clean_governance_routing_blocks_ambiguous_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proposals_path = root / "proposals.json"
            proposals_path.write_text(
                json.dumps(
                    [
                        {"title": "Dataset benchmark bridge", "description": "dataset snapshot beside benchmark history"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_maintenance_batching.py"),
                    "--skip-module-pressure",
                    "--governance-proposals",
                    str(proposals_path),
                    "--require-clean-governance-routing",
                    "--out-dir",
                    str(root / "script-fail"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("governance_routing_decision=review_before_merge", completed.stdout)
            self.assertIn("governance_routing_ambiguous_keyword_match_count=1", completed.stdout)
            self.assertIn("governance_routing_requirement_status=fail", completed.stdout)
            self.assertIn("governance_routing_requirement_decision=stop", completed.stdout)
            self.assertIn("governance_routing_requirement_exit_code=1", completed.stdout)
            self.assertIn("governance_routing_requirement_blocking_count=1", completed.stdout)
            self.assertIn("governance_routing_requirement_failed_reasons=review_required,ambiguous_keyword", completed.stdout)
            payload = json.loads((root / "script-fail" / "governance_stabilization.json").read_text(encoding="utf-8"))
            markdown = (root / "script-fail" / "governance_stabilization.md").read_text(encoding="utf-8")
            html = (root / "script-fail" / "governance_stabilization.html").read_text(encoding="utf-8")
            self.assertEqual(payload["routing_requirement"]["status"], "fail")
            self.assertEqual(payload["routing_requirement"]["exit_code"], 1)
            self.assertIn("Requirement status: `fail`", markdown)
            self.assertIn("Failed reasons", html)

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
