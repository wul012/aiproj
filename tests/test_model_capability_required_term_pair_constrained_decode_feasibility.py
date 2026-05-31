from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_constrained_decode_feasibility import (
    build_model_capability_required_term_pair_constrained_decode_feasibility,
    locate_pair_constrained_decode_feasibility_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_constrained_decode_feasibility_artifacts import (
    render_model_capability_required_term_pair_constrained_decode_feasibility_html,
    render_model_capability_required_term_pair_constrained_decode_feasibility_markdown,
    render_model_capability_required_term_pair_constrained_decode_feasibility_text,
    write_model_capability_required_term_pair_constrained_decode_feasibility_outputs,
)


class ModelCapabilityRequiredTermPairConstrainedDecodeFeasibilityTests(unittest.TestCase):
    def test_constrained_decode_reports_pair_full_feasible(self) -> None:
        report = build_model_capability_required_term_pair_constrained_decode_feasibility(
            refresh_report_fixture(),
            out_dir="out",
            generated_at="2026-05-31T05:00:00Z",
            generate_func=fake_generate_pair_full_when_blocked,
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_constrained_decode_pair_full_feasible")
        self.assertEqual(report["summary"]["default_hit_count"], 1)
        self.assertEqual(report["summary"]["constrained_hit_count"], 2)
        self.assertTrue(report["summary"]["fixed_constrained_hit"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_constrained_decode_reports_no_gain(self) -> None:
        report = build_model_capability_required_term_pair_constrained_decode_feasibility(
            refresh_report_fixture(),
            out_dir="out",
            generate_func=fake_generate_no_gain,
        )

        self.assertEqual(report["decision"], "required_term_pair_constrained_decode_not_feasible")
        self.assertEqual(report["summary"]["hit_delta"], 0)

    def test_invalid_source_fails_require_pass(self) -> None:
        report = build_model_capability_required_term_pair_constrained_decode_feasibility(
            {"training": {}, "replay_report": {"case_rows": []}},
            out_dir="out",
            generate_func=fake_generate_no_gain,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("refresh report has no training object", report["issues"])
        self.assertIn("refresh report has fewer than two terms to constrain", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_constrained_decode_feasibility(
                refresh_report_fixture(),
                out_dir=root / "decode",
                generate_func=fake_generate_pair_full_when_blocked,
            )
            outputs = write_model_capability_required_term_pair_constrained_decode_feasibility_outputs(report, root / "decode")
            text = render_model_capability_required_term_pair_constrained_decode_feasibility_text(report)
            markdown = render_model_capability_required_term_pair_constrained_decode_feasibility_markdown(report)
            html = render_model_capability_required_term_pair_constrained_decode_feasibility_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("constrained_pair_full=True", text)
            self.assertIn("Constrained Decode Feasibility", markdown)
            self.assertIn("MiniGPT constrained decode feasibility", html)

    def test_locate_accepts_nested_refresh_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "seed-reports" / "seed-1535"
            nested.mkdir(parents=True)
            source = nested / "model_capability_required_term_pair_coexistence_refresh.json"
            source.write_text("{}", encoding="utf-8")

            self.assertEqual(locate_pair_constrained_decode_feasibility_source(root), source)


def refresh_report_fixture() -> dict[str, object]:
    return {
        "training": {
            "checkpoint_path": "checkpoint.pt",
            "tokenizer_path": "tokenizer.json",
        },
        "replay_report": {
            "case_rows": [
                {"term": "fixed", "prompt": "fixed=", "generation_seed": 1535},
                {"term": "loss", "prompt": "loss=", "generation_seed": 1536},
            ]
        },
    }


def fake_generate_pair_full_when_blocked(request: dict[str, object]) -> dict[str, object]:
    term = str(request["expected_term"])
    blocked = tuple(request.get("blocked_token_texts") or ())
    if term == "fixed" and not blocked:
        continuation = "loss-like"
    else:
        continuation = term
    return {
        "generated": str(request["prompt"]) + continuation,
        "continuation": continuation,
        "blocked_token_count": len(blocked),
    }


def fake_generate_no_gain(request: dict[str, object]) -> dict[str, object]:
    blocked = tuple(request.get("blocked_token_texts") or ())
    continuation = "loss-like"
    return {
        "generated": str(request["prompt"]) + continuation,
        "continuation": continuation,
        "blocked_token_count": len(blocked),
    }


if __name__ == "__main__":
    unittest.main()
