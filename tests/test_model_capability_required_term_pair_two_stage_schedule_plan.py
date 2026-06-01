from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_two_stage_schedule_plan import (
    build_model_capability_required_term_pair_two_stage_schedule_plan,
    make_two_stage_schedule_plan_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_two_stage_schedule_plan_artifacts import (
    render_two_stage_schedule_plan_html,
    render_two_stage_schedule_plan_markdown,
    render_two_stage_schedule_plan_text,
    write_two_stage_schedule_plan_outputs,
)
from minigpt.report_utils import write_json_payload


ROOT = Path(__file__).resolve().parents[1]


class TwoStageSchedulePlanTests(unittest.TestCase):
    def test_plan_passes_with_split_generation_and_internal_full_sources(self) -> None:
        report = build_model_capability_required_term_pair_two_stage_schedule_plan(
            surface_source=source("surface", generation_terms=["fixed", "loss"], internal_terms=["fixed"]),
            internal_source=source("internal", generation_terms=[], internal_terms=["fixed", "loss"]),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "two_stage_surface_internal_schedule_ready")
        self.assertEqual(report["schedule_boundary"]["training_semantics"], "not_checkpoint_resume")
        self.assertEqual(report["summary"]["stage_gate_pass_count"], 2)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_surface_source_lacks_generation_pair_full(self) -> None:
        report = build_model_capability_required_term_pair_two_stage_schedule_plan(
            surface_source=source("surface", generation_terms=["fixed"], internal_terms=["fixed"]),
            internal_source=source("internal", generation_terms=[], internal_terms=["fixed", "loss"]),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("surface_generation_pair_full_required", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_two_stage_schedule_plan(
                surface_source=source("surface", generation_terms=["fixed", "loss"], internal_terms=["fixed"]),
                internal_source=source("internal", generation_terms=[], internal_terms=["fixed", "loss"]),
            )
            outputs = write_two_stage_schedule_plan_outputs(report, Path(tmp) / "plan")
            text = render_two_stage_schedule_plan_text(report)
            markdown = render_two_stage_schedule_plan_markdown(report)
            html = render_two_stage_schedule_plan_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=two_stage_surface_internal_schedule_ready", text)
            self.assertIn("Two-Stage Schedule Plan", markdown)
            self.assertIn("MiniGPT two-stage schedule plan", html)

    def test_cli_require_pass_returns_nonzero_on_bad_surface_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            surface_refresh = root / "surface_refresh" / "model_capability_required_term_pair_coexistence_refresh.json"
            surface_forced = (
                root
                / "surface_forced"
                / "model_capability_required_term_pair_refresh_forced_choice_diagnostic.json"
            )
            internal_refresh = root / "internal_refresh" / "model_capability_required_term_pair_coexistence_refresh.json"
            internal_forced = (
                root
                / "internal_forced"
                / "model_capability_required_term_pair_refresh_forced_choice_diagnostic.json"
            )
            write_json_payload(refresh_report(["fixed"]), surface_refresh)
            write_json_payload(forced_choice_report("surface", ["fixed"]), surface_forced)
            write_json_payload(refresh_report([]), internal_refresh)
            write_json_payload(forced_choice_report("internal", ["fixed", "loss"]), internal_forced)

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_model_capability_required_term_pair_two_stage_schedule_plan.py"),
                    "--surface-source",
                    "surface",
                    str(surface_refresh.parent),
                    str(surface_forced.parent),
                    "--internal-source",
                    "internal",
                    str(internal_refresh.parent),
                    str(internal_forced.parent),
                    "--out-dir",
                    str(root / "out"),
                    "--require-pass",
                    "--force",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("status=fail", result.stdout)


def source(label: str, *, generation_terms: list[str], internal_terms: list[str]) -> dict[str, object]:
    return make_two_stage_schedule_plan_source(
        label=label,
        refresh_report=refresh_report(generation_terms),
        forced_choice_report=forced_choice_report(label, internal_terms),
    )


def refresh_report(hit_terms: list[str]) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_pair_full_observed",
        "settings": {"corpus_mode": "equals_surface_no_pair_id_loss_internal_joint_cycle_repair", "seed": 3535},
        "summary": {"training_status": "pass", "checkpoint_exists": True},
        "replay_report": {
            "case_rows": [
                {"profile_id": "default", "term": "fixed", "continuation_hit": "fixed" in hit_terms},
                {"profile_id": "default", "term": "loss", "continuation_hit": "loss" in hit_terms},
            ]
        },
    }


def forced_choice_report(label: str, expected_best_terms: list[str]) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "refresh_forced_choice_partial_internal_match",
        "prompt_summaries": [
            {"source_label": label, "prompt_term": "fixed", "expected_best": "fixed" in expected_best_terms},
            {"source_label": label, "prompt_term": "loss", "expected_best": "loss" in expected_best_terms},
        ],
        "source_summaries": [
            {
                "source_label": label,
                "expected_best_terms": expected_best_terms,
                "forced_choice_full_match": set(["fixed", "loss"]).issubset(expected_best_terms),
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
