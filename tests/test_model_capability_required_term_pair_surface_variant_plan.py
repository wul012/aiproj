from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_variant_plan import (
    build_surface_variant_plan,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_variant_plan_outputs,
)


class SurfaceVariantPlanTests(unittest.TestCase):
    def test_variant_plan_includes_separator_variants(self) -> None:
        report = build_surface_variant_plan(profile_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_surface_variant_plan_ready")
        self.assertEqual(report["summary"]["included_variant_count"], 5)
        self.assertIn("newline_context", [row["variant_id"] for row in report["variant_rows"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_profile_without_promotion_boundary_fails(self) -> None:
        profile = profile_fixture()
        profile["profile"]["promotion_allowed"] = True
        report = build_surface_variant_plan(profile)

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_boundary_missing", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_variant_plan(profile_fixture())
            outputs = write_surface_variant_plan_outputs(report, Path(tmp) / "plan")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("variant_count=5", render_text(report))
        self.assertIn("Surface Variant Plan", render_markdown(report))
        self.assertIn("MiniGPT surface variant plan", render_html(report))


def profile_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "profile": {
            "profile_id": "pair_context_prefix_budget_8",
            "policy_id": "pair_context_prefix",
            "max_new_tokens": 8,
            "promotion_allowed": False,
        },
    }


if __name__ == "__main__":
    unittest.main()
