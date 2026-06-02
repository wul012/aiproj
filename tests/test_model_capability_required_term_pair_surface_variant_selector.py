from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_variant_selector import (
    build_surface_variant_selector,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_variant_selector_outputs,
)


class SurfaceVariantSelectorTests(unittest.TestCase):
    def test_selector_prefers_space_control_when_all_stable(self) -> None:
        report = build_surface_variant_selector(plan_fixture(), replay_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["selected_variant"]["variant_id"], "space_context_control")
        self.assertEqual(report["decision"], "required_term_pair_surface_variant_selected_for_contextual_demo")
        self.assertFalse(report["summary"]["promotion_allowed"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_no_stable_variant_fails(self) -> None:
        replay = replay_fixture()
        for row in replay["variant_summaries"]:
            row["stable_pair_full"] = False
        report = build_surface_variant_selector(plan_fixture(), replay)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_stable_variant", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_variant_selector(plan_fixture(), replay_fixture())
            outputs = write_surface_variant_selector_outputs(report, Path(tmp) / "selector")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("selected_variant_id=space_context_control", render_text(report))
        self.assertIn("Surface Variant Selector", render_markdown(report))
        self.assertIn("MiniGPT surface variant selector", render_html(report))


def plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "variant_rows": [
            {"variant_id": "compact_context", "prompt_template": "{other_term}={other_term}{term}=", "separator_style": "compact"},
            {"variant_id": "space_context_control", "prompt_template": "{other_term}={other_term} {term}=", "separator_style": "space"},
        ],
    }


def replay_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"max_new_tokens": 8},
        "variant_summaries": [
            {"variant_id": "compact_context", "stable_pair_full": True, "pair_full_seed_count": 3, "hit_case_count": 6},
            {"variant_id": "space_context_control", "stable_pair_full": True, "pair_full_seed_count": 3, "hit_case_count": 6},
        ],
    }


if __name__ == "__main__":
    unittest.main()
