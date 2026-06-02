from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_baseline_contrast import (
    build_surface_baseline_contrast,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_baseline_contrast_outputs,
)


class SurfaceBaselineContrastTests(unittest.TestCase):
    def test_contextual_anchor_required_when_baselines_are_not_stable(self) -> None:
        report = build_surface_baseline_contrast(policy_replay_fixture(), variant_selector_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_contextual_variant_needed_over_non_leaking_baselines")
        self.assertTrue(report["summary"]["contextual_anchor_required"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_missing_baselines_fails(self) -> None:
        replay = policy_replay_fixture()
        replay["policy_summaries"] = []
        report = build_surface_baseline_contrast(replay, variant_selector_fixture())

        self.assertEqual(report["status"], "fail")
        self.assertIn("missing_non_leaking_baselines", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_baseline_contrast(policy_replay_fixture(), variant_selector_fixture())
            outputs = write_surface_baseline_contrast_outputs(report, Path(tmp) / "contrast")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("contextual_anchor_required=True", render_text(report))
        self.assertIn("Surface Baseline Contrast", render_markdown(report))
        self.assertIn("MiniGPT surface baseline contrast", render_html(report))


def policy_replay_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "policy_summaries": [
            {"policy_id": "single_label_default", "stable_pair_full": False, "pair_full_seed_count": 0, "hit_case_count": 1},
            {"policy_id": "single_label_suppress_newline", "stable_pair_full": False, "pair_full_seed_count": 0, "hit_case_count": 1},
        ],
    }


def variant_selector_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "selected_variant": {
            "variant_id": "space_context_control",
            "stable_pair_full": True,
            "pair_full_seed_count": 3,
            "hit_case_count": 6,
        },
    }


if __name__ == "__main__":
    unittest.main()
