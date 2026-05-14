from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_gate import (  # noqa: E402
    build_training_scale_gate,
    load_training_scale_plan,
    render_training_scale_gate_html,
    render_training_scale_gate_markdown,
    write_training_scale_gate_outputs,
)
from minigpt.training_scale_plan import build_training_scale_plan, write_training_scale_plan_outputs  # noqa: E402


class TrainingScaleGateTests(unittest.TestCase):
    def test_review_profile_warns_for_tiny_plan_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT scale gate data.\n" * 30), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )

            gate = build_training_scale_gate(plan, profile="review", generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(gate["overall_status"], "warn")
            self.assertEqual(gate["fail_count"], 0)
            self.assertTrue(any(check["code"] == "tiny_corpus" and check["status"] == "warn" for check in gate["checks"]))
            self.assertEqual(gate["plan_summary"]["variant_count"], len(plan["variants"]))

    def test_standard_profile_fails_tiny_or_warning_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tiny.txt"
            source.write_text("tiny", encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )

            gate = build_training_scale_gate(plan, profile="standard", generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(gate["overall_status"], "fail")
            self.assertGreaterEqual(gate["fail_count"], 2)
            self.assertTrue(any(check["code"] == "min_char_count" and check["status"] == "fail" for check in gate["checks"]))
            self.assertTrue(any(check["code"] == "quality_warnings" and check["status"] == "fail" for check in gate["checks"]))

    def test_write_outputs_and_load_plan_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT scale gate output data.\n" * 60), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan_outputs = write_training_scale_plan_outputs(plan, root / "scale")
            loaded = load_training_scale_plan(plan_outputs["json"])

            gate = build_training_scale_gate(
                loaded,
                plan_path=plan_outputs["json"],
                profile="review",
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_training_scale_gate_outputs(gate, root / "gate")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["plan_path"], plan_outputs["json"])
            self.assertIn(payload["overall_status"], {"pass", "warn", "fail"})

    def test_missing_baseline_variant_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT baseline gate data.\n" * 50), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan["batch"]["baseline"] = "missing"

            gate = build_training_scale_gate(plan, profile="review", generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(gate["overall_status"], "fail")
            self.assertTrue(any(check["code"] == "baseline_variant" and check["status"] == "fail" for check in gate["checks"]))

    def test_token_budget_limit_can_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT budget gate data.\n" * 80), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan["variant_matrix"][0]["token_budget"] = 9_000_000

            gate = build_training_scale_gate(plan, profile="standard", generated_at="2026-05-14T00:00:00Z")

            self.assertTrue(any(check["code"] == "token_budget" and check["status"] == "fail" for check in gate["checks"]))

    def test_renderers_escape_html_and_include_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT render gate data.\n" * 50), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                dataset_name="<demo>",
                generated_at="2026-05-14T00:00:00Z",
            )
            gate = build_training_scale_gate(plan, profile="review", generated_at="2026-05-14T00:00:00Z")

            markdown = render_training_scale_gate_markdown(gate)
            html = render_training_scale_gate_html(gate)

            self.assertIn("## Checks", markdown)
            self.assertIn("&lt;demo&gt;", html)
            self.assertNotIn("<demo>", html)

    def test_unknown_profile_fails_fast(self) -> None:
        with self.assertRaises(ValueError):
            build_training_scale_gate({}, profile="missing")


if __name__ == "__main__":
    unittest.main()
