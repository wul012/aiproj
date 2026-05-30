from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_decode_boundary_check import (
    build_model_capability_required_term_pair_decode_boundary_check,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_decode_boundary_check_artifacts import (
    render_model_capability_required_term_pair_decode_boundary_check_html,
    render_model_capability_required_term_pair_decode_boundary_check_markdown,
    render_model_capability_required_term_pair_decode_boundary_check_text,
    write_model_capability_required_term_pair_decode_boundary_check_outputs,
)


class ModelCapabilityRequiredTermPairDecodeBoundaryCheckTests(unittest.TestCase):
    def test_decode_boundary_reports_improvement_over_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_decode_boundary_check(
                stability_report(root, baseline_pair_full=0),
                out_dir=root / "decode",
                decode_specs=({"spec_id": "wide", "top_k": 2, "temperature": 0.2, "max_new_tokens": 12},),
                generated_at="2026-05-31T00:40:00Z",
                generate_func=fake_generate_pair_full,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_decode_boundary_improves_pair_surface")
            self.assertEqual(report["summary"]["best_pair_full_seed_count"], 2)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_decode_boundary_reports_no_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_decode_boundary_check(
                stability_report(root, baseline_pair_full=0),
                out_dir=root / "decode",
                decode_specs=({"spec_id": "greedy", "top_k": 1, "temperature": 0.2, "max_new_tokens": 12},),
                generate_func=fake_generate_fixed_only,
            )

            self.assertEqual(report["decision"], "required_term_pair_decode_boundary_no_pair_surface_gain")
            self.assertEqual(report["summary"]["best_pair_full_seed_count"], 0)

    def test_decode_boundary_fails_without_seed_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = stability_report(root, baseline_pair_full=0)
            payload["seed_reports"] = []
            report = build_model_capability_required_term_pair_decode_boundary_check(
                payload,
                out_dir=root / "decode",
                generate_func=fake_generate_pair_full,
            )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_decode_boundary_check(
                stability_report(root, baseline_pair_full=0),
                out_dir=root / "decode",
                decode_specs=({"spec_id": "wide", "top_k": 2, "temperature": 0.2, "max_new_tokens": 12},),
                generate_func=fake_generate_pair_full,
            )
            outputs = write_model_capability_required_term_pair_decode_boundary_check_outputs(report, root / "decode")
            text = render_model_capability_required_term_pair_decode_boundary_check_text(report)
            markdown = render_model_capability_required_term_pair_decode_boundary_check_markdown(report)
            html = render_model_capability_required_term_pair_decode_boundary_check_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decode_improved_pair_full=True", text)
            self.assertIn("Decode Boundary Check", markdown)
            self.assertIn("MiniGPT pair decode boundary check", html)
            self.assertTrue(
                (
                    root
                    / "decode"
                    / "replay-reports"
                    / "wide"
                    / "seed-535"
                    / "model_capability_required_term_pair_generation_profile_replay.json"
                ).is_file()
            )


def stability_report(root: Path, *, baseline_pair_full: int) -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"seed_count": 2, "pair_full_seed_count": baseline_pair_full},
        "seed_rows": [
            {"seed": 535, "pair_full_observed": False},
            {"seed": 1535, "pair_full_observed": False},
        ],
        "seed_reports": [seed_report(root, 535), seed_report(root, 1535)],
    }


def seed_report(root: Path, seed: int) -> dict[str, object]:
    run_dir = root / f"seed-{seed}" / "run"
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
        "settings": {"seed": seed},
        "training": {
            "checkpoint_path": str(checkpoint),
            "tokenizer_path": str(tokenizer),
        },
    }


def fake_generate_pair_full(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    expected = str(request["expected_term"])
    return {"generated": prompt + expected, "continuation": expected, "blocked_token_count": 0}


def fake_generate_fixed_only(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "fixed", "continuation": "fixed", "blocked_token_count": 0}


if __name__ == "__main__":
    unittest.main()
