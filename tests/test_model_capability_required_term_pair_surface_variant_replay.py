from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_variant_replay import (
    build_surface_variant_replay,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_variant_replay_outputs,
)


class SurfaceVariantReplayTests(unittest.TestCase):
    def test_variant_replay_summarizes_stability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_variant_replay(
                stability_fixture(Path(tmp)),
                variant_plan_fixture(),
                out_dir=Path(tmp) / "replay",
                generate_func=variant_generate,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["stable_variant_ids"], ["space_context_control"])
        self.assertEqual(report["decision"], "required_term_pair_surface_variant_replay_partial_stability")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_bad_plan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = variant_plan_fixture()
            plan["status"] = "fail"
            report = build_surface_variant_replay(stability_fixture(Path(tmp)), plan, out_dir=Path(tmp) / "replay", generate_func=variant_generate)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_variant_replay(
                stability_fixture(Path(tmp)),
                variant_plan_fixture(),
                out_dir=Path(tmp) / "replay",
                generate_func=variant_generate,
            )
            outputs = write_surface_variant_replay_outputs(report, Path(tmp) / "out")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("stable_variant_count=1", render_text(report))
        self.assertIn("Surface Variant Replay", render_markdown(report))
        self.assertIn("MiniGPT surface variant replay", render_html(report))


def stability_fixture(root: Path) -> dict[str, object]:
    seed_reports = []
    for seed in (11, 22):
        run_dir = root / f"seed-{seed}"
        run_dir.mkdir(parents=True, exist_ok=True)
        checkpoint = run_dir / "checkpoint.pt"
        tokenizer = run_dir / "tokenizer.json"
        checkpoint.write_text("fake", encoding="utf-8")
        tokenizer.write_text("fake", encoding="utf-8")
        seed_reports.append({"settings": {"seed": seed}, "training": {"checkpoint_path": str(checkpoint), "tokenizer_path": str(tokenizer)}})
    return {"status": "pass", "seed_reports": seed_reports}


def variant_plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"max_new_tokens": 8},
        "execution_profile": {"temperature": 0.2, "top_k": 1},
        "variant_rows": [
            {"variant_id": "space_context_control", "prompt_template": "{other_term}={other_term} {term}=", "leakage_level": "contextual_anchor", "included_in_replay": True},
            {"variant_id": "compact_context", "prompt_template": "{other_term}={other_term}{term}=", "leakage_level": "contextual_anchor", "included_in_replay": True},
        ],
    }


def variant_generate(request: dict[str, object]) -> dict[str, object]:
    term = str(request["expected_term"])
    policy_id = str(request["policy_id"])
    continuation = term if policy_id == "space_context_control" else "x"
    return {"generated": str(request["prompt"]) + continuation, "continuation": continuation, "blocked_token_count": 0}


if __name__ == "__main__":
    unittest.main()
