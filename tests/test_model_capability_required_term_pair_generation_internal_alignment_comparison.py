from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison import (
    build_model_capability_required_term_pair_generation_internal_alignment_comparison,
    make_generation_internal_alignment_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison_artifacts import (
    render_generation_internal_alignment_comparison_html,
    render_generation_internal_alignment_comparison_markdown,
    render_generation_internal_alignment_comparison_text,
    write_generation_internal_alignment_comparison_outputs,
)


class GenerationInternalAlignmentComparisonTests(unittest.TestCase):
    def test_generation_pair_full_internal_partial_routes_to_internal_repair(self) -> None:
        report = build_model_capability_required_term_pair_generation_internal_alignment_comparison(
            [
                source(
                    "joint-cycle",
                    generation_terms=["fixed", "loss"],
                    internal_terms=["fixed"],
                )
            ]
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "keep_generation_pair_full_and_repair_internal_preference")
        self.assertEqual(report["summary"]["generation_pair_full_count"], 1)
        self.assertEqual(report["summary"]["internal_pair_full_count"], 0)
        self.assertEqual(report["source_rows"][0]["alignment_class"], "generation_pair_full_internal_partial")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_internal_pair_full_generation_gap_routes_to_generation_bridge(self) -> None:
        report = build_model_capability_required_term_pair_generation_internal_alignment_comparison(
            [
                source(
                    "first-token",
                    generation_terms=["loss"],
                    internal_terms=["fixed", "loss"],
                )
            ]
        )

        self.assertEqual(report["decision"], "use_internal_pair_full_to_repair_generation")
        self.assertEqual(report["summary"]["internal_only_pair_full_count"], 1)
        self.assertEqual(report["source_rows"][0]["alignment_class"], "internal_pair_full_generation_gap")

    def test_internal_pair_full_with_no_generation_hits_is_a_valid_negative_route(self) -> None:
        report = build_model_capability_required_term_pair_generation_internal_alignment_comparison(
            [
                source(
                    "internal-repair",
                    generation_terms=[],
                    internal_terms=["fixed", "loss"],
                )
            ]
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "use_internal_pair_full_to_repair_generation")
        self.assertEqual(report["source_rows"][0]["alignment_class"], "internal_pair_full_generation_none")
        self.assertEqual(report["source_rows"][0]["generation_hit_terms"], [])

    def test_no_internal_expected_best_terms_is_a_valid_failed_route(self) -> None:
        report = build_model_capability_required_term_pair_generation_internal_alignment_comparison(
            [
                source(
                    "not-recovered",
                    generation_terms=["loss"],
                    internal_terms=[],
                )
            ]
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(report["source_rows"][0]["internal_expected_best_terms"], [])
        self.assertEqual(report["source_rows"][0]["alignment_class"], "partial_tradeoff")

    def test_aligned_pair_full_wins_over_generation_only(self) -> None:
        report = build_model_capability_required_term_pair_generation_internal_alignment_comparison(
            [
                source("joint-cycle", generation_terms=["fixed", "loss"], internal_terms=["fixed"]),
                source("aligned", generation_terms=["fixed", "loss"], internal_terms=["fixed", "loss"]),
            ]
        )

        self.assertEqual(report["decision"], "select_aligned_generation_internal_pair_full_candidate")
        self.assertEqual(report["summary"]["aligned_pair_full_count"], 1)
        self.assertEqual(report["summary"]["best_source_labels"], ["aligned"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_generation_internal_alignment_comparison(
                [source("joint-cycle", generation_terms=["fixed", "loss"], internal_terms=["fixed"])]
            )
            outputs = write_generation_internal_alignment_comparison_outputs(report, root / "alignment")
            text = render_generation_internal_alignment_comparison_text(report)
            markdown = render_generation_internal_alignment_comparison_markdown(report)
            html = render_generation_internal_alignment_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=keep_generation_pair_full_and_repair_internal_preference", text)
            self.assertIn("Generation/Internal Alignment Comparison", markdown)
            self.assertIn("MiniGPT generation/internal alignment comparison", html)


def source(label: str, *, generation_terms: list[str], internal_terms: list[str]) -> dict[str, object]:
    return make_generation_internal_alignment_source(
        label=label,
        refresh_report=refresh_report(generation_terms),
        forced_choice_report=forced_choice_report(label, internal_terms),
    )


def refresh_report(hit_terms: list[str]) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_pair_full_observed",
        "settings": {"corpus_mode": "equals_surface_no_pair_id_loss_internal_joint_cycle_repair", "seed": 3535},
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": set(["fixed", "loss"]).issubset(hit_terms),
        },
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
