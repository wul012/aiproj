from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_policy_leakage_risk import (
    build_surface_policy_leakage_risk,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_policy_leakage_risk_outputs,
)


class SurfacePolicyLeakageRiskTests(unittest.TestCase):
    def test_contextual_anchor_risk_is_documented(self) -> None:
        report = build_surface_policy_leakage_risk(selector_fixture(), minimality_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_surface_policy_contextual_risk_documented")
        self.assertEqual(report["summary"]["risk_level"], "medium")
        self.assertFalse(report["summary"]["promotion_allowed"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_bad_selector_fails(self) -> None:
        selector = selector_fixture()
        selector["status"] = "fail"
        report = build_surface_policy_leakage_risk(selector, minimality_fixture())

        self.assertEqual(report["status"], "fail")
        self.assertIn("source selector report is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_policy_leakage_risk(selector_fixture(), minimality_fixture())
            outputs = write_surface_policy_leakage_risk_outputs(report, Path(tmp) / "risk")

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue(Path(outputs["csv"]).is_file())
            self.assertIn("risk_level=medium", render_text(report))
            self.assertIn("Leakage Risk", render_markdown(report))
            self.assertIn("MiniGPT surface policy leakage risk", render_html(report))


def selector_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "selected_policy": {
            "policy_id": "pair_context_prefix",
            "leakage_level": "contextual_anchor",
            "uses_boundary_sentence": False,
        },
    }


def minimality_fixture() -> dict[str, object]:
    return {"status": "pass", "summary": {"contextual_anchor_required": True}}


if __name__ == "__main__":
    unittest.main()
