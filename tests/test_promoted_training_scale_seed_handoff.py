from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import promoted_training_scale_seed_handoff as handoff_module  # noqa: E402
from minigpt import promoted_training_scale_seed_handoff_artifacts as artifact_module  # noqa: E402
from minigpt.promoted_training_scale_seed_handoff import (  # noqa: E402
    SEED_HANDOFF_AUTOMATION_GATE_DECISIONS,
    SEED_HANDOFF_AUTOMATION_GATE_STATUSES,
    SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES,
    SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES,
    SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES,
    build_promoted_training_scale_seed_handoff,
    build_seed_handoff_automation_gate,
    build_seed_handoff_clean_batch_review_requirement,
    build_seed_handoff_clean_evidence_requirement,
    render_promoted_training_scale_seed_handoff_html,
    render_promoted_training_scale_seed_handoff_markdown,
    write_promoted_training_scale_seed_handoff_outputs,
)


class PromotedTrainingScaleSeedHandoffTests(unittest.TestCase):
    def test_clean_evidence_status_domain_is_public_contract(self) -> None:
        self.assertEqual(
            SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES,
            ("ready", "pending-plan", "review", "incomplete"),
        )
        self.assertEqual(
            SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES,
            ("not-required", "pass", "fail"),
        )
        self.assertEqual(
            SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES,
            ("not-required", "pass", "fail"),
        )
        self.assertEqual(
            SEED_HANDOFF_AUTOMATION_GATE_STATUSES,
            ("not-required", "pass", "fail"),
        )
        self.assertEqual(
            SEED_HANDOFF_AUTOMATION_GATE_DECISIONS,
            ("not-requested", "continue", "stop"),
        )

    def test_clean_evidence_requirement_helper_maps_public_statuses(self) -> None:
        pending_summary = {
            "seed_handoff_clean_evidence_ready": False,
            "seed_handoff_clean_evidence_status": "pending-plan",
            "seed_handoff_clean_evidence_detail": "execute the seed handoff first",
        }
        ready_summary = {
            "seed_handoff_clean_evidence_ready": True,
            "seed_handoff_clean_evidence_status": "ready",
            "seed_handoff_clean_evidence_detail": "clean evidence is ready",
        }

        optional = build_seed_handoff_clean_evidence_requirement(pending_summary)
        required_pending = build_seed_handoff_clean_evidence_requirement(pending_summary, required=True)
        required_ready = build_seed_handoff_clean_evidence_requirement(ready_summary, required=True)

        self.assertEqual(optional["status"], "not-required")
        self.assertEqual(required_pending["status"], "fail")
        self.assertEqual(required_pending["readiness_status"], "pending-plan")
        self.assertEqual(required_ready["status"], "pass")
        self.assertEqual(required_ready["status_domain"], list(SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES))

    def test_clean_batch_review_requirement_helper_maps_public_statuses(self) -> None:
        clean_summary = {
            "selected_handoff_require_clean_batch_review": True,
            "selected_handoff_clean_batch_review_status": "clean",
        }
        dirty_summary = {
            "selected_handoff_require_clean_batch_review": True,
            "selected_handoff_clean_batch_review_status": "review",
        }
        optional = build_seed_handoff_clean_batch_review_requirement(dirty_summary)
        required_clean = build_seed_handoff_clean_batch_review_requirement(clean_summary, required=True)
        required_dirty = build_seed_handoff_clean_batch_review_requirement(dirty_summary, required=True)

        self.assertEqual(optional["status"], "not-required")
        self.assertFalse(optional["clean"])
        self.assertEqual(required_clean["status"], "pass")
        self.assertTrue(required_clean["clean"])
        self.assertEqual(required_dirty["status"], "fail")
        self.assertFalse(required_dirty["clean"])
        self.assertEqual(required_dirty["selected_status"], "review")
        self.assertEqual(required_dirty["status_domain"], list(SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES))

    def test_automation_gate_aggregates_clean_requirements(self) -> None:
        not_required = build_seed_handoff_automation_gate(
            {
                "required": False,
                "status": "not-required",
                "ready": False,
                "readiness_status": "pending-plan",
                "detail": "not requested",
                "status_domain": list(SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES),
            },
            {
                "required": False,
                "status": "not-required",
                "clean": False,
                "selected_required": True,
                "selected_status": "review",
                "detail": "not requested",
                "status_domain": list(SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES),
            },
        )
        mixed = build_seed_handoff_automation_gate(
            {
                "required": True,
                "status": "fail",
                "ready": False,
                "readiness_status": "pending-plan",
                "detail": "execute first",
                "status_domain": list(SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES),
            },
            {
                "required": True,
                "status": "pass",
                "clean": True,
                "selected_required": True,
                "selected_status": "clean",
                "detail": "clean",
                "status_domain": list(SEED_HANDOFF_CLEAN_BATCH_REVIEW_REQUIREMENT_STATUSES),
            },
        )

        self.assertEqual(not_required["status"], "not-required")
        self.assertEqual(not_required["decision"], "not-requested")
        self.assertEqual(not_required["exit_code"], 0)
        self.assertEqual(not_required["required_requirement_count"], 0)
        self.assertEqual(not_required["failed_requirements"], [])
        self.assertEqual(mixed["status"], "fail")
        self.assertEqual(mixed["decision"], "stop")
        self.assertEqual(mixed["exit_code"], 1)
        self.assertEqual(mixed["required_requirement_count"], 2)
        self.assertEqual(mixed["passed_requirement_count"], 1)
        self.assertEqual(mixed["failed_requirement_count"], 1)
        self.assertEqual(mixed["blocking_requirement_count"], 1)
        self.assertEqual(mixed["failed_requirements"], ["clean_evidence"])
        self.assertEqual(mixed["passed_requirements"], ["clean_batch_review"])
        self.assertEqual(mixed["status_domain"], list(SEED_HANDOFF_AUTOMATION_GATE_STATUSES))
        self.assertEqual(mixed["decision_domain"], list(SEED_HANDOFF_AUTOMATION_GATE_DECISIONS))

    def test_artifact_functions_are_reexported_from_handoff_module(self) -> None:
        self.assertIs(
            handoff_module.render_promoted_training_scale_seed_handoff_html,
            artifact_module.render_promoted_training_scale_seed_handoff_html,
        )
        self.assertIs(
            handoff_module.render_promoted_training_scale_seed_handoff_markdown,
            artifact_module.render_promoted_training_scale_seed_handoff_markdown,
        )
        self.assertIs(
            handoff_module.write_promoted_training_scale_seed_handoff_outputs,
            artifact_module.write_promoted_training_scale_seed_handoff_outputs,
        )

    def test_validates_ready_seed_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root)

            report = build_promoted_training_scale_seed_handoff(seed, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["summary"]["handoff_status"], "planned")
            self.assertTrue(report["handoff_allowed"])
            self.assertFalse(report["execute"])
            self.assertIn("scripts/plan_training_scale.py", report["command"])
            self.assertEqual(report["summary"]["artifact_count"], 5)
            self.assertEqual(report["clean_evidence_requirement"]["status"], "not-required")
            self.assertEqual(report["clean_batch_review_requirement"]["status"], "not-required")
            self.assertEqual(report["automation_gate"]["status"], "not-required")
            self.assertEqual(report["automation_gate"]["decision"], "not-requested")
            self.assertEqual(report["automation_gate"]["exit_code"], 0)

    def test_builder_can_attach_required_clean_evidence_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)

            planned = build_promoted_training_scale_seed_handoff(
                seed,
                require_clean_evidence=True,
                generated_at="2026-05-14T00:00:00Z",
            )
            executed = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                require_clean_evidence=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(planned["clean_evidence_requirement"]["status"], "fail")
            self.assertEqual(planned["clean_evidence_requirement"]["readiness_status"], "pending-plan")
            self.assertEqual(executed["clean_evidence_requirement"]["status"], "pass")
            self.assertEqual(executed["clean_evidence_requirement"]["readiness_status"], "ready")
            self.assertIn("Clean-evidence requirement failed", planned["recommendations"][1])
            self.assertIn("Clean-evidence requirement passed", executed["recommendations"][1])

    def test_blocks_review_when_allow_review_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, seed_status="review")

            report = build_promoted_training_scale_seed_handoff(
                seed,
                allow_review=False,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "blocked")
            self.assertFalse(report["handoff_allowed"])
            self.assertIn("allow_review is false", report["blocked_reason"])

    def test_execute_runs_plan_command_and_detects_plan_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root)

            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "completed")
            self.assertEqual(report["execution"]["returncode"], 0)
            self.assertEqual(report["summary"]["available_artifact_count"], 5)
            self.assertEqual(report["summary"]["plan_status"], "available")
            self.assertTrue(report["summary"]["next_batch_command_available"])
            self.assertIn("run_training_portfolio_batch.py", report["next_batch_command_text"])
            self.assertTrue((root / "next-plan" / "training_scale_plan.json").exists())

    def test_execute_preserves_seed_standard_suite_in_plan_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh")

            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            plan_payload = json.loads((root / "next-plan" / "training_scale_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["handoff_status"], "completed")
            self.assertEqual(report["summary"]["seed_suite_path"], "builtin:standard-zh")
            self.assertEqual(report["summary"]["plan_suite_path"], "builtin:standard-zh")
            self.assertEqual(report["summary"]["seed_handoff_suite_alignment_status"], "missing")
            self.assertEqual(plan_payload["suite"], {"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh"})
            self.assertIn("--suite-name", report["next_batch_command"])
            self.assertIn("standard-zh", report["next_batch_command"])

    def test_carries_seed_handoff_suite_guard_into_handoff_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)

            report = build_promoted_training_scale_seed_handoff(seed, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_seed_handoff_outputs(report, root / "handoff")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary = report["summary"]
            self.assertEqual(summary["handoff_status"], "planned")
            self.assertEqual(summary["selected_handoff_suite_consistency"], "consistent")
            self.assertEqual(summary["selected_handoff_suite_mismatch_count"], 0)
            self.assertEqual(summary["selected_handoff_selected_suite_path"], "builtin:standard-zh")
            self.assertEqual(summary["handoff_suite_mismatch_total"], 0)
            self.assertEqual(summary["seed_handoff_suite_alignment_status"], "pending-plan")
            self.assertEqual(summary["seed_handoff_suite_alignment_mismatch_count"], 0)
            self.assertFalse(summary["seed_handoff_clean_evidence_ready"])
            self.assertEqual(summary["seed_handoff_clean_evidence_status"], "pending-plan")
            self.assertEqual(summary["seed_handoff_clean_evidence_status_domain"], list(SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES))
            self.assertIn("selected_handoff_suite_consistency", csv_text)
            self.assertIn("seed_handoff_suite_alignment_status", csv_text)
            self.assertIn("seed_handoff_clean_evidence_status", csv_text)
            self.assertIn("seed_handoff_clean_evidence_status_domain", csv_text)
            self.assertIn("clean_evidence_requirement_status_domain", csv_text)
            self.assertIn("Selected handoff suite", markdown)
            self.assertIn("Handoff suite mismatches", markdown)
            self.assertIn("Seed handoff suite alignment", markdown)
            self.assertIn("Seed handoff clean evidence", markdown)
            self.assertIn("Seed handoff clean evidence status domain", markdown)
            self.assertIn("Clean evidence requirement status domain", markdown)
            self.assertIn("Selected handoff suite", html)
            self.assertIn("Suite alignment", html)
            self.assertIn("Clean evidence", html)
            self.assertIn("Clean evidence domain", html)
            self.assertIn("Clean evidence gate domain", html)
            self.assertIn("selected_handoff_suite_consistency=consistent", completed.stdout)
            self.assertIn("handoff_suite_mismatch_total=0", completed.stdout)
            self.assertIn("seed_handoff_suite_alignment_status=pending-plan", completed.stdout)
            self.assertIn("seed_handoff_clean_evidence_status=pending-plan", completed.stdout)
            self.assertIn("seed_handoff_clean_evidence_status_domain=", completed.stdout)
            script_payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(script_payload["clean_evidence_requirement"]["status"], "not-required")
            self.assertEqual(
                script_payload["clean_evidence_requirement"]["status_domain"],
                list(SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES),
            )
            self.assertTrue((script_out / "promoted_training_scale_seed_handoff.json").exists())

    def test_carries_seed_handoff_batch_review_into_handoff_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_batch_review=True,
            )

            report = build_promoted_training_scale_seed_handoff(seed, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_seed_handoff_outputs(report, root / "handoff")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary = report["summary"]
            self.assertEqual(summary["handoff_status"], "planned")
            self.assertEqual(summary["selected_handoff_selected_batch_review_status"], "blocker")
            self.assertEqual(summary["selected_handoff_selected_batch_comparison_review_action_count"], 2)
            self.assertEqual(summary["selected_handoff_selected_batch_comparison_blocker_action_count"], 1)
            self.assertEqual(summary["selected_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_blocker_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])
            self.assertIn("selected_handoff_selected_batch_review_status", csv_text)
            self.assertIn("Selected handoff batch review", markdown)
            self.assertIn("Selected handoff batch", html)
            self.assertIn("selected_handoff_selected_batch_review_status=blocker", completed.stdout)
            self.assertIn("comparison_ready_handoff_selected_batch_blocker_count=1", completed.stdout)
            self.assertTrue(any("selected handoff batch blocker" in item for item in report["recommendations"]))

    def test_carries_seed_clean_batch_review_into_handoff_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
            )

            report = build_promoted_training_scale_seed_handoff(seed, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_seed_handoff_outputs(report, root / "handoff")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary = report["summary"]
            clean_batch_requirement = report["clean_batch_review_requirement"]
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["handoff_status"], "planned")
            self.assertTrue(summary["selected_handoff_require_clean_batch_review"])
            self.assertEqual(summary["selected_handoff_clean_batch_review_status"], "clean")
            self.assertEqual(summary["handoff_require_clean_batch_review_count"], 3)
            self.assertEqual(summary["handoff_clean_batch_review_count"], 2)
            self.assertEqual(summary["handoff_unclean_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(summary["comparison_ready_handoff_clean_batch_review_count"], 2)
            self.assertEqual(summary["comparison_ready_handoff_unclean_batch_review_count"], 0)
            self.assertEqual(clean_batch_requirement["status"], "not-required")
            self.assertTrue(clean_batch_requirement["clean"])
            self.assertIn("selected_handoff_require_clean_batch_review", csv_text)
            self.assertIn("selected_handoff_clean_batch_review_status", csv_text)
            self.assertIn("clean_batch_review_requirement_status", csv_text)
            self.assertIn("automation_gate_status", csv_text)
            self.assertIn("automation_gate_decision", csv_text)
            self.assertIn("automation_gate_exit_code", csv_text)
            self.assertIn("Selected handoff require clean batch review", markdown)
            self.assertIn("Comparison-ready clean handoffs", markdown)
            self.assertIn("Clean batch-review requirement", markdown)
            self.assertIn("Automation gate", markdown)
            self.assertIn("Automation gate decision", markdown)
            self.assertIn("Selected clean batch", html)
            self.assertIn("Ready clean batch", html)
            self.assertIn("Clean batch gate", html)
            self.assertIn("Automation gate", html)
            self.assertIn("Automation decision", html)
            self.assertIn("selected_handoff_require_clean_batch_review=True", completed.stdout)
            self.assertIn("selected_handoff_clean_batch_review_status=clean", completed.stdout)
            self.assertIn("handoff_unclean_batch_review_count=1", completed.stdout)
            self.assertIn("comparison_ready_handoff_unclean_batch_review_count=0", completed.stdout)
            self.assertEqual(payload["summary"]["selected_handoff_clean_batch_review_status"], "clean")
            self.assertEqual(payload["clean_batch_review_requirement"]["status"], "not-required")
            self.assertEqual(payload["automation_gate"]["status"], "not-required")
            self.assertEqual(payload["automation_gate"]["decision"], "not-requested")
            self.assertTrue(
                any("Rejected promoted decision inputs include unclean clean-required handoffs" in item for item in report["recommendations"])
            )

    def test_script_can_require_clean_batch_review_when_selected_handoff_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
            )
            script_out = root / "script-out"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--require-clean-batch-review",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            csv_text = (script_out / "promoted_training_scale_seed_handoff.csv").read_text(encoding="utf-8")
            markdown = (script_out / "promoted_training_scale_seed_handoff.md").read_text(encoding="utf-8")
            html = (script_out / "promoted_training_scale_seed_handoff.html").read_text(encoding="utf-8")
            self.assertIn("clean_batch_review_required_selected_status=clean", completed.stdout)
            self.assertIn("clean_batch_review_required_clean=True", completed.stdout)
            self.assertIn("clean_batch_review_required=pass", completed.stdout)
            self.assertIn("automation_gate_status=pass", completed.stdout)
            self.assertIn("automation_gate_decision=continue", completed.stdout)
            self.assertIn("automation_gate_exit_code=0", completed.stdout)
            self.assertIn("automation_gate_required_requirement_count=1", completed.stdout)
            self.assertIn("automation_gate_blocking_requirement_count=0", completed.stdout)
            self.assertIn('automation_gate_passed_requirements=[\"clean_batch_review\"]', completed.stdout)
            self.assertEqual(payload["clean_batch_review_requirement"]["status"], "pass")
            self.assertEqual(payload["automation_gate"]["status"], "pass")
            self.assertEqual(payload["automation_gate"]["decision"], "continue")
            self.assertEqual(payload["automation_gate"]["exit_code"], 0)
            self.assertTrue(payload["clean_batch_review_requirement"]["required"])
            self.assertIn("Clean batch-review requirement passed", payload["recommendations"][1])
            self.assertIn("clean_batch_review_requirement_status", csv_text)
            self.assertIn("Clean batch-review requirement", markdown)
            self.assertIn("Clean batch gate", html)

    def test_script_rejects_dirty_clean_batch_review_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
                clean_batch_review_status="review",
            )
            script_out = root / "script-out"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--require-clean-batch-review",
                ],
                capture_output=True,
                text=True,
            )

            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("selected_handoff_clean_batch_review_status=review", completed.stdout)
            self.assertIn("clean_batch_review_required_selected_status=review", completed.stdout)
            self.assertIn("clean_batch_review_required_clean=False", completed.stdout)
            self.assertIn("clean_batch_review_required=fail", completed.stdout)
            self.assertIn("automation_gate_status=fail", completed.stdout)
            self.assertIn("automation_gate_decision=stop", completed.stdout)
            self.assertIn("automation_gate_exit_code=1", completed.stdout)
            self.assertIn("automation_gate_required_requirement_count=1", completed.stdout)
            self.assertIn("automation_gate_blocking_requirement_count=1", completed.stdout)
            self.assertIn('automation_gate_failed_requirements=[\"clean_batch_review\"]', completed.stdout)
            self.assertEqual(payload["clean_batch_review_requirement"]["status"], "fail")
            self.assertEqual(payload["automation_gate"]["status"], "fail")
            self.assertEqual(payload["automation_gate"]["decision"], "stop")
            self.assertEqual(payload["automation_gate"]["exit_code"], 1)
            self.assertTrue(payload["clean_batch_review_requirement"]["required"])
            self.assertFalse(payload["clean_batch_review_requirement"]["clean"])
            self.assertEqual(payload["clean_batch_review_requirement"]["selected_status"], "review")
            self.assertIn("Clean batch-review requirement failed", payload["recommendations"][1])

    def test_execute_reports_consistent_suite_alignment_after_plan_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)

            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            summary = report["summary"]
            self.assertEqual(summary["handoff_status"], "completed")
            self.assertEqual(summary["seed_handoff_suite_alignment_status"], "consistent")
            self.assertEqual(summary["seed_handoff_suite_alignment_mismatch_count"], 0)
            self.assertEqual(summary["seed_handoff_suite_alignment_missing_count"], 0)
            self.assertTrue(summary["seed_handoff_clean_evidence_ready"])
            self.assertEqual(summary["seed_handoff_clean_evidence_status"], "ready")
            self.assertEqual(summary["seed_handoff_clean_evidence_status_domain"], list(SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES))
            self.assertIn("selected_handoff, seed, and plan suite paths align", summary["seed_handoff_suite_alignment_detail"])
            self.assertIn("Suite alignment is consistent", report["recommendations"][0])

    def test_script_can_require_clean_evidence_after_consistent_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("seed_handoff_clean_evidence_status=ready", completed.stdout)
            self.assertIn("clean_evidence_required_status=ready", completed.stdout)
            self.assertIn("clean_evidence_required_ready=True", completed.stdout)
            self.assertIn("clean_evidence_required_detail=completed handoff has consistent suite alignment", completed.stdout)
            self.assertIn("clean_evidence_required=pass", completed.stdout)
            self.assertIn("automation_gate_status=pass", completed.stdout)
            self.assertIn("automation_gate_decision=continue", completed.stdout)
            self.assertIn("automation_gate_exit_code=0", completed.stdout)
            self.assertIn('automation_gate_passed_requirements=[\"clean_evidence\"]', completed.stdout)
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["clean_evidence_requirement"]["status"], "pass")
            self.assertEqual(payload["automation_gate"]["status"], "pass")
            self.assertEqual(payload["automation_gate"]["decision"], "continue")
            self.assertTrue(payload["clean_evidence_requirement"]["required"])
            self.assertTrue(payload["clean_evidence_requirement"]["ready"])
            self.assertIn("Clean-evidence requirement passed", payload["recommendations"][1])
            self.assertEqual(
                payload["clean_evidence_requirement"]["status_domain"],
                list(SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES),
            )

    def test_script_rejects_pending_clean_evidence_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--require-clean-evidence",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("seed_handoff_clean_evidence_status=pending-plan", completed.stdout)
            self.assertIn("clean_evidence_required_status=pending-plan", completed.stdout)
            self.assertIn("clean_evidence_required_ready=False", completed.stdout)
            self.assertIn("clean_evidence_required_detail=execute the seed handoff before treating clean comparison evidence as ready", completed.stdout)
            self.assertIn("clean_evidence_required=fail", completed.stdout)
            self.assertIn("automation_gate_status=fail", completed.stdout)
            self.assertIn("automation_gate_decision=stop", completed.stdout)
            self.assertIn("automation_gate_exit_code=1", completed.stdout)
            self.assertIn('automation_gate_failed_requirements=[\"clean_evidence\"]', completed.stdout)
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            csv_text = (script_out / "promoted_training_scale_seed_handoff.csv").read_text(encoding="utf-8")
            markdown = (script_out / "promoted_training_scale_seed_handoff.md").read_text(encoding="utf-8")
            html = (script_out / "promoted_training_scale_seed_handoff.html").read_text(encoding="utf-8")
            self.assertEqual(payload["clean_evidence_requirement"]["status"], "fail")
            self.assertTrue(payload["clean_evidence_requirement"]["required"])
            self.assertFalse(payload["clean_evidence_requirement"]["ready"])
            self.assertEqual(payload["clean_evidence_requirement"]["readiness_status"], "pending-plan")
            self.assertEqual(payload["automation_gate"]["status"], "fail")
            self.assertEqual(payload["automation_gate"]["decision"], "stop")
            self.assertIn("Clean-evidence requirement failed", payload["recommendations"][1])
            self.assertIn("execute the seed handoff", payload["recommendations"][1])
            self.assertIn("clean_evidence_requirement_status", csv_text)
            self.assertIn("clean_evidence_requirement_status_domain", csv_text)
            self.assertIn("Clean evidence requirement", markdown)
            self.assertIn("Clean evidence gate", html)
            self.assertIn("Clean evidence gate domain", html)

    def test_script_reports_all_failed_automation_requirements_before_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
                clean_batch_review_status="review",
            )
            script_out = root / "script-out"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--require-clean-evidence",
                    "--require-clean-batch-review",
                ],
                capture_output=True,
                text=True,
            )

            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            csv_text = (script_out / "promoted_training_scale_seed_handoff.csv").read_text(encoding="utf-8")
            markdown = (script_out / "promoted_training_scale_seed_handoff.md").read_text(encoding="utf-8")
            html = (script_out / "promoted_training_scale_seed_handoff.html").read_text(encoding="utf-8")
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("clean_evidence_required=fail", completed.stdout)
            self.assertIn("clean_batch_review_required=fail", completed.stdout)
            self.assertIn("automation_gate_status=fail", completed.stdout)
            self.assertIn("automation_gate_decision=stop", completed.stdout)
            self.assertIn("automation_gate_failed_requirement_count=2", completed.stdout)
            self.assertIn("automation_gate_blocking_requirement_count=2", completed.stdout)
            self.assertIn(
                'automation_gate_failed_requirements=[\"clean_evidence\", \"clean_batch_review\"]',
                completed.stdout,
            )
            self.assertEqual(payload["automation_gate"]["status"], "fail")
            self.assertEqual(payload["automation_gate"]["decision"], "stop")
            self.assertEqual(payload["automation_gate"]["exit_code"], 1)
            self.assertEqual(payload["automation_gate"]["required_requirement_count"], 2)
            self.assertEqual(payload["automation_gate"]["failed_requirement_count"], 2)
            self.assertEqual(payload["automation_gate"]["blocking_requirement_count"], 2)
            self.assertEqual(payload["automation_gate"]["failed_requirements"], ["clean_evidence", "clean_batch_review"])
            self.assertIn("automation_gate_status", csv_text)
            self.assertIn("automation_gate_decision", csv_text)
            self.assertIn("automation_gate_blocking_requirement_count", csv_text)
            self.assertIn("Automation gate", markdown)
            self.assertIn("Automation gate decision", markdown)
            self.assertIn("Automation gate", html)
            self.assertIn("Automation decision", html)

    def test_reports_mismatched_selected_suite_alignment_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="default", include_handoff_suite_guard=True)

            report = build_promoted_training_scale_seed_handoff(seed, generated_at="2026-05-14T00:00:00Z")

            summary = report["summary"]
            self.assertEqual(summary["handoff_status"], "planned")
            self.assertEqual(summary["seed_handoff_suite_alignment_status"], "mismatch")
            self.assertEqual(summary["seed_handoff_suite_alignment_mismatch_count"], 1)
            self.assertFalse(summary["seed_handoff_clean_evidence_ready"])
            self.assertEqual(summary["seed_handoff_clean_evidence_status"], "review")
            self.assertIn("selected_handoff=builtin:standard-zh differs from seed=builtin:default", summary["seed_handoff_suite_alignment_detail"])
            self.assertIn("Review suite alignment mismatch", report["recommendations"][0])
            self.assertIn("Review the generated seed command", report["recommendations"][1])

    def test_missing_suite_alignment_adds_review_recommendation_without_blocking_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh")

            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "completed")
            self.assertEqual(report["summary"]["seed_handoff_suite_alignment_status"], "missing")
            self.assertFalse(report["summary"]["seed_handoff_clean_evidence_ready"])
            self.assertEqual(report["summary"]["seed_handoff_clean_evidence_status"], "incomplete")
            self.assertIn("Record missing suite alignment evidence", report["recommendations"][0])
            self.assertIn("Use the generated plan report", report["recommendations"][1])

    def test_execute_reports_failed_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, command=[sys.executable, "-c", "import sys; sys.exit(7)"])

            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "failed")
            self.assertEqual(report["execution"]["returncode"], 7)

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root)

            report = build_promoted_training_scale_seed_handoff(
                seed.parent,
                title="<Handoff>",
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_promoted_training_scale_seed_handoff_outputs(report, root / "handoff")
            markdown = render_promoted_training_scale_seed_handoff_markdown(report)
            html = render_promoted_training_scale_seed_handoff_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertIn("## Command", markdown)
            self.assertIn("&lt;Handoff&gt;", html)
            self.assertNotIn("<Handoff>", html)


def write_seed_tree(
    root: Path,
    *,
    seed_status: str = "ready",
    command: list[str] | None = None,
    suite_name: str | None = None,
    include_handoff_suite_guard: bool = False,
    include_handoff_clean_batch_review: bool = False,
    include_handoff_batch_review: bool = False,
    clean_batch_review_status: str = "clean",
) -> Path:
    source = root / "corpus.txt"
    source.write_text("MiniGPT v82 next cycle corpus.\n" * 180, encoding="utf-8")
    plan_out = root / "next-plan"
    batch_out = root / "batch"
    command = command or [
        sys.executable,
        "scripts/plan_training_scale.py",
        str(source),
        "--project-root",
        str(ROOT),
        "--out-dir",
        str(plan_out),
        "--batch-out-root",
        str(batch_out),
        "--dataset-name",
        "next-zh",
        "--dataset-version-prefix",
        "v82-test",
        *(
            ["--suite-name", suite_name]
            if suite_name
            else []
        ),
        "--max-variants",
        "1",
    ]
    suite = (
        {"mode": "builtin", "name": suite_name, "path": f"builtin:{suite_name}", "source": "inherited"}
        if suite_name
        else {"mode": "file", "name": None, "path": str(ROOT / "data" / "eval_prompts.json"), "source": "default"}
    )
    baseline_seed = {
        "selected_name": "beta",
        "decision_status": "accepted" if seed_status != "blocked" else "blocked",
        "gate_status": "pass",
        "batch_status": "completed",
        "readiness_score": 107,
        "training_scale_run_path": str(root / "beta" / "training_scale_run.json"),
        "training_scale_run_exists": True,
        "suite": suite,
        "suite_path": suite["path"],
    }
    if include_handoff_suite_guard:
        baseline_seed["handoff_suite_guard"] = {
            "selected_handoff_require_suite_consistency": True,
            "selected_handoff_suite_consistency": "consistent",
            "selected_handoff_suite_mismatch_count": 0,
            "selected_handoff_selected_suite_path": "builtin:standard-zh",
            "handoff_require_suite_consistency_count": 2,
            "handoff_suite_consistent_count": 2,
            "handoff_suite_mismatch_total": 0,
            "comparison_ready_handoff_suite_mismatch_total": 0,
        }
    if include_handoff_clean_batch_review:
        baseline_seed["handoff_clean_batch_review"] = {
            "selected_handoff_require_clean_batch_review": True,
            "selected_handoff_clean_batch_review_status": clean_batch_review_status,
            "handoff_require_clean_batch_review_count": 3,
            "handoff_clean_batch_review_count": 2 if clean_batch_review_status == "clean" else 1,
            "handoff_unclean_batch_review_count": 1 if clean_batch_review_status == "clean" else 2,
            "comparison_ready_handoff_require_clean_batch_review_count": 2,
            "comparison_ready_handoff_clean_batch_review_count": 2 if clean_batch_review_status == "clean" else 1,
            "comparison_ready_handoff_unclean_batch_review_count": 0 if clean_batch_review_status == "clean" else 1,
        }
    if include_handoff_batch_review:
        baseline_seed["handoff_batch_review"] = {
            "selected_handoff_selected_batch_review_status": "blocker",
            "selected_handoff_selected_batch_comparison_review_action_count": 2,
            "selected_handoff_selected_batch_comparison_blocker_action_count": 1,
            "selected_handoff_selected_batch_maturity_coverage_regression_count": 1,
            "selected_handoff_batch_comparison_review_action_count": 2,
            "selected_handoff_batch_comparison_blocker_action_count": 1,
            "selected_handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
            "comparison_ready_handoff_selected_batch_review_count": 1,
            "comparison_ready_handoff_selected_batch_blocker_count": 1,
            "comparison_ready_handoff_selected_batch_comparison_review_action_total": 4,
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": 1,
            "comparison_ready_handoff_batch_comparison_review_action_total": 4,
            "comparison_ready_handoff_batch_comparison_blocker_action_total": 1,
            "comparison_ready_handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
        }
    seed = {
        "schema_version": 1,
        "title": "seed",
        "generated_at": "2026-05-14T00:00:00Z",
        "seed_status": seed_status,
        "baseline_seed": baseline_seed,
        "next_plan": {
            "project_root": str(ROOT),
            "dataset_name": "next-zh",
            "dataset_version_prefix": "v82-test",
            "suite": suite,
            "suite_path": suite["path"],
            "suite_source": suite["source"],
            "plan_out_dir": str(plan_out),
            "batch_out_root": str(batch_out),
            "sources": [
                {
                    "path": str(source),
                    "resolved_path": str(source.resolve()),
                    "exists": True,
                    "kind": "file",
                }
            ],
            "command": command,
            "command_text": " ".join(command),
            "command_available": bool(command),
            "execution_ready": seed_status == "ready",
        },
        "summary": {
            "seed_status": seed_status,
            "selected_name": "beta",
            "command_available": bool(command),
        },
    }
    seed_path = root / "promoted-seed" / "promoted_training_scale_seed.json"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    return seed_path


if __name__ == "__main__":
    unittest.main()
