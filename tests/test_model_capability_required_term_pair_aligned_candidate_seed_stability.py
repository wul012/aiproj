from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_aligned_candidate_seed_stability import (
    build_model_capability_required_term_pair_aligned_candidate_seed_stability,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_aligned_candidate_seed_stability_artifacts import (
    render_aligned_candidate_seed_stability_html,
    render_aligned_candidate_seed_stability_markdown,
    render_aligned_candidate_seed_stability_text,
    write_aligned_candidate_seed_stability_outputs,
)


class ModelCapabilityRequiredTermPairAlignedCandidateSeedStabilityTests(unittest.TestCase):
    def test_stability_reports_all_seed_pair_full_from_route_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_aligned_candidate_seed_stability(
                out_dir=root / "stability",
                route_decision=route_decision_fixture(),
                seeds=(1535, 2535),
                repeat=2,
                bridge_repeat=1,
                max_iters=4,
                generated_at="2026-06-01T14:20:00Z",
                train_func=fake_train,
                generate_func=fake_generate_pair_full,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_aligned_candidate_stably_pair_full")
            self.assertEqual(report["settings"]["corpus_mode"], "equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair")
            self.assertEqual(report["summary"]["pair_full_seed_count"], 2)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_stability_reports_partial_seed_pair_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_aligned_candidate_seed_stability(
                out_dir=root / "stability",
                route_decision=route_decision_fixture(),
                seeds=(1535, 2535),
                repeat=2,
                bridge_repeat=1,
                max_iters=4,
                train_func=fake_train,
                generate_func=fake_generate_only_seed_1535_pair_full,
            )

            self.assertEqual(report["decision"], "required_term_pair_aligned_candidate_partial_stability")
            self.assertEqual(report["summary"]["pair_full_seed_count"], 1)

    def test_invalid_route_decision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_aligned_candidate_seed_stability(
                out_dir=root / "stability",
                route_decision={"status": "fail"},
                seeds=(1535,),
                corpus_mode="equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair",
                repeat=2,
                bridge_repeat=1,
                max_iters=4,
                train_func=fake_train,
                generate_func=fake_generate_pair_full,
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("source route decision is not pass", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats_and_seed_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_aligned_candidate_seed_stability(
                out_dir=root / "stability",
                route_decision=route_decision_fixture(),
                seeds=(1535,),
                repeat=2,
                bridge_repeat=1,
                max_iters=4,
                train_func=fake_train,
                generate_func=fake_generate_pair_full,
            )
            outputs = write_aligned_candidate_seed_stability_outputs(report, root / "stability")
            text = render_aligned_candidate_seed_stability_text(report)
            markdown = render_aligned_candidate_seed_stability_markdown(report)
            html = render_aligned_candidate_seed_stability_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("stable_pair_full=True", text)
            self.assertIn("Aligned-Candidate Seed Stability", markdown)
            self.assertIn("MiniGPT aligned-candidate seed stability", html)
            self.assertTrue(
                (
                    root
                    / "stability"
                    / "seed-reports"
                    / "seed-1535"
                    / "model_capability_required_term_pair_coexistence_refresh.json"
                ).is_file()
            )


def route_decision_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "repeat_aligned_pair_full_candidate_before_promotion",
        "summary": {
            "aligned_route_label": "dual-boundary-seed-3535",
            "direct_promotion_ready": True,
        },
        "aligned_route": {
            "source_label": "dual-boundary-seed-3535",
            "corpus_mode": "equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair",
            "alignment_class": "generation_internal_pair_full",
        },
    }


def fake_train(context: dict[str, object]) -> dict[str, object]:
    run_dir = Path(str(context["train_dir"]))
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "returncode": 0,
        "run_dir": str(run_dir),
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "checkpoint_exists": True,
        "tokenizer_exists": True,
    }


def fake_generate_pair_full(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    expected = str(request["expected_term"])
    return {"generated": prompt + expected, "continuation": expected, "blocked_token_count": 0}


def fake_generate_only_seed_1535_pair_full(request: dict[str, object]) -> dict[str, object]:
    if "seed-1535" in str(request["checkpoint_path"]).replace("\\", "/"):
        return fake_generate_pair_full(request)
    prompt = str(request["prompt"])
    return {"generated": prompt + "other", "continuation": "other", "blocked_token_count": 0}


if __name__ == "__main__":
    unittest.main()
