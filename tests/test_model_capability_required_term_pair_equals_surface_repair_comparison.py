from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison import (
    build_model_capability_required_term_pair_equals_surface_repair_comparison,
    locate_pair_equals_surface_repair_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison_artifacts import (
    render_model_capability_required_term_pair_equals_surface_repair_comparison_html,
    render_model_capability_required_term_pair_equals_surface_repair_comparison_markdown,
    render_model_capability_required_term_pair_equals_surface_repair_comparison_text,
    write_model_capability_required_term_pair_equals_surface_repair_comparison_outputs,
)


class ModelCapabilityRequiredTermPairEqualsSurfaceRepairComparisonTests(unittest.TestCase):
    def test_comparison_detects_branch_competition_across_repairs(self) -> None:
        report = build_model_capability_required_term_pair_equals_surface_repair_comparison(
            [
                stability_report("equals_surface_fixed_repair", {"default": [], "suppress_newline_tokens": ["fixed"]}),
                stability_report("equals_surface_balanced_repair", {"default": ["loss"], "suppress_newline_tokens": ["loss"]}),
            ],
            source_paths=["fixed.json", "balanced.json"],
            generated_at="2026-05-31T04:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_equals_surface_branch_competition_detected")
        self.assertEqual(report["summary"]["branch_competition_seed_count"], 1)
        self.assertEqual(report["summary"]["pair_full_profile_seed_count"], 0)
        self.assertEqual(report["summary"]["union_hit_terms"], ["fixed", "loss"])
        self.assertEqual(report["branch_rows"][0]["fixed_hit_reports"], ["equals_surface_fixed_repair"])
        self.assertEqual(report["branch_rows"][0]["loss_hit_reports"], ["equals_surface_balanced_repair"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_reports_pair_full_when_one_profile_has_both_terms(self) -> None:
        report = build_model_capability_required_term_pair_equals_surface_repair_comparison(
            [
                stability_report("equals_surface_fixed_repair", {"default": ["fixed"], "suppress_newline_tokens": ["fixed"]}),
                stability_report("equals_surface_joined_repair", {"default": ["fixed", "loss"], "suppress_newline_tokens": ["loss"]}),
            ]
        )

        self.assertEqual(report["decision"], "required_term_pair_equals_surface_pair_full_found")
        self.assertEqual(report["summary"]["pair_full_profile_seed_count"], 1)
        self.assertEqual(report["branch_rows"][0]["pair_full_profile_reports"], ["equals_surface_joined_repair"])

    def test_invalid_comparison_input_fails_require_pass(self) -> None:
        report = build_model_capability_required_term_pair_equals_surface_repair_comparison(
            [stability_report("colon_immediate", {"default": ["fixed"]})]
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("at least two repair reports are required for comparison", report["issues"])
        self.assertIn("colon_immediate report is not an equals-surface corpus mode", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_equals_surface_repair_comparison(
                [
                    stability_report("equals_surface_fixed_repair", {"default": [], "suppress_newline_tokens": ["fixed"]}),
                    stability_report("equals_surface_balanced_repair", {"default": ["loss"], "suppress_newline_tokens": ["loss"]}),
                ]
            )
            outputs = write_model_capability_required_term_pair_equals_surface_repair_comparison_outputs(report, root / "comparison")
            text = render_model_capability_required_term_pair_equals_surface_repair_comparison_text(report)
            markdown = render_model_capability_required_term_pair_equals_surface_repair_comparison_markdown(report)
            html = render_model_capability_required_term_pair_equals_surface_repair_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("branch_competition_seed_count=1", text)
            self.assertIn("equals_surface_fixed_repair", markdown)
            self.assertIn("MiniGPT equals-surface repair comparison", html)

    def test_locate_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_pair_equals_surface_repair_report(root),
                root / "model_capability_required_term_pair_colon_immediate_stability.json",
            )


def stability_report(corpus_mode: str, hits_by_profile: dict[str, list[str]]) -> dict[str, object]:
    pair_full = any({"fixed", "loss"}.issubset(set(terms)) for terms in hits_by_profile.values())
    return {
        "status": "pass",
        "decision": "required_term_pair_colon_immediate_stably_pair_full" if pair_full else "required_term_pair_colon_immediate_not_stable",
        "settings": {"corpus_mode": corpus_mode},
        "summary": {
            "seed_count": 1,
            "pair_full_seed_count": 1 if pair_full else 0,
            "pair_full_seed_rate": 1.0 if pair_full else 0.0,
            "stable_pair_full": pair_full,
        },
        "seed_rows": [
            {
                "seed": 1535,
                "status": "pass",
                "pair_full_observed": pair_full,
            }
        ],
        "seed_reports": [
            {
                "settings": {"seed": 1535},
                "status": "pass",
                "replay_report": {
                    "case_rows": [
                        case_row(profile, term, term in hit_terms)
                        for profile, hit_terms in hits_by_profile.items()
                        for term in ("fixed", "loss")
                    ]
                },
            }
        ],
    }


def case_row(profile: str, term: str, hit: bool) -> dict[str, object]:
    prompt = f"{term}="
    continuation = f"{term}=ok" if hit else "other"
    return {
        "profile_id": profile,
        "term": term,
        "prompt": prompt,
        "continuation_hit": hit,
        "newline_cleanup_hit": hit,
        "blocked_token_count": 1 if profile == "suppress_newline_tokens" else 0,
        "generated_preview": prompt + continuation,
        "continuation_preview": continuation,
    }


if __name__ == "__main__":
    unittest.main()
